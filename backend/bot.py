"""The Pipecat voice pipeline: mic -> STT -> LLM (tools) -> TTS -> speaker."""

from pipecat.frames.frames import (
    LLMFullResponseEndFrame, LLMFullResponseStartFrame, LLMRunFrame, LLMTextFrame, TranscriptionFrame,
)
import os
from datetime import date

import store
from events import publish

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    LLMFullResponseEndFrame, LLMFullResponseStartFrame, LLMTextFrame, TranscriptionFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

SYSTEM = f"""You are Asha, the phone receptionist for a clinic. Today is {date.today().isoformat()}.
You help callers check doctor availability, book, and cancel appointments.
Speak like a calm person on the phone: short sentences, no lists, no markdown, no emojis.
Rules:
- The caller is identified ONLY by the phone number they say aloud. Ask for it.
- Before booking or cancelling, read the 10-digit number back digit by digit and wait for a clear yes.
  If they say no, ask again.
- To check slots, call check_doctor_availability, then offer at most 3 options out loud.
- Call book_appointment only after: doctor, date, time and confirmed phone number are known.
- Call cancel_appointment only after the phone number is confirmed.
- Pass dates as YYYY-MM-DD and times as 24-hour HH:MM. Say times naturally, like "half past two".
- Never invent doctors or slots. Use only what the tools return.
Start by greeting the caller briefly and asking how you can help."""


class TranscriptTap(FrameProcessor):
    """Copies what the user said / what the bot says to the dashboard."""

    def __init__(self, role):
        super().__init__()
        self.role, self._buf = role, []

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if self.role == "user" and isinstance(frame, TranscriptionFrame) and frame.text.strip():
            publish({"type": "transcript", "role": "user", "text": frame.text.strip()})
        elif self.role == "bot":
            if isinstance(frame, LLMFullResponseStartFrame):
                self._buf = []
            elif isinstance(frame, LLMTextFrame):
                self._buf.append(frame.text)
            elif isinstance(frame, LLMFullResponseEndFrame):
                text = "".join(self._buf).strip()
                if text:
                    publish({"type": "transcript", "role": "bot", "text": text})
                self._buf = []
        await self.push_frame(frame, direction)


def make_stt():
    key = os.environ["ELEVENLABS_API_KEY"]
    try:  # newer Pipecat versions have a streaming ElevenLabs STT
        from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
        return ElevenLabsRealtimeSTTService(api_key=key)
    except ImportError:
        import aiohttp
        from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
        return ElevenLabsSTTService(api_key=key, aiohttp_session=aiohttp.ClientSession())


TOOLS = ToolsSchema(standard_tools=[
    FunctionSchema(
        name="check_doctor_availability",
        description="List free appointment slots. Filter by doctor name/speciality and/or date.",
        properties={
            "doctor": {"type": "string", "description": "Doctor name or speciality. Optional."},
            "date": {"type": "string", "description": "YYYY-MM-DD. Optional."},
        },
        required=[],
    ),
    FunctionSchema(
        name="book_appointment",
        description="Book a slot for the caller using the phone number they confirmed.",
        properties={
            "doctor": {"type": "string", "description": "Doctor name."},
            "date": {"type": "string", "description": "YYYY-MM-DD"},
            "time": {"type": "string", "description": "24-hour HH:MM"},
            "phone": {"type": "string", "description": "Caller's confirmed 10-digit phone number."},
            "patient_name": {"type": "string", "description": "Caller's name. Optional."},
        },
        required=["doctor", "date", "time", "phone"],
    ),
    FunctionSchema(
        name="cancel_appointment",
        description="Cancel the caller's appointment, found by their confirmed phone number.",
        properties={
            "phone": {"type": "string", "description": "Caller's confirmed 10-digit phone number."},
            "date": {"type": "string", "description": "YYYY-MM-DD. Only if they have several."},
            "time": {"type": "string", "description": "HH:MM. Only if they have several."},
        },
        required=["phone"],
    ),
])


async def on_check(params: FunctionCallParams):
    a = params.arguments
    await params.result_callback(store.availability(a.get("doctor"), a.get("date")))


async def on_book(params: FunctionCallParams):
    a = params.arguments
    res = store.book(a.get("doctor"), a.get("date"), a.get("time"), a.get("phone"), a.get("patient_name", ""))
    if res["ok"]:
        publish({"type": "appointment", "action": "booked", "appointment": res["appointment"]})
    await params.result_callback(res)


async def on_cancel(params: FunctionCallParams):
    a = params.arguments
    res = store.cancel(a.get("phone"), a.get("date"), a.get("time"))
    if res["ok"]:
        publish({"type": "appointment", "action": "cancelled", "appointment": res["appointment"]})
    await params.result_callback(res)


async def run_bot(connection):
    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )
    stt = make_stt()
    llm = GoogleLLMService(
        api_key=os.environ["GOOGLE_API_KEY"],
        model=os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
    )
    tts = ElevenLabsTTSService(
        api_key=os.environ["ELEVENLABS_API_KEY"],
        voice_id=os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
    )
    llm.register_function("check_doctor_availability", on_check)
    llm.register_function("book_appointment", on_book)
    llm.register_function("cancel_appointment", on_cancel)

    # The system prompt now lives inside the conversation itself.
    context = OpenAILLMContext(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "The caller just connected. Greet them."},
        ],
        TOOLS,
    )
    agg = llm.create_context_aggregator(context)

    pipeline = Pipeline([
        transport.input(), stt, TranscriptTap("user"), agg.user(),
        llm, TranscriptTap("bot"), tts, transport.output(), agg.assistant(),
    ])
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

    @transport.event_handler("on_client_connected")
    async def _connected(_t, _c):
        publish({"type": "call", "state": "connected"})
        await task.queue_frames([LLMRunFrame()])  # bot speaks first

    @transport.event_handler("on_client_disconnected")
    async def _disconnected(_t, _c):
        publish({"type": "call", "state": "ended"})
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)