import { useCallback, useRef, useState } from "react";

const STUN = [{ urls: "stun:stun.l.google.com:19302" }];

// Owns the whole browser side of the call: mic, WebRTC, timer, sounds, mute.
// phase: idle | connecting | connected | ended | error
export function useCall({ onStart, onEnd }) {
  const [phase, setPhase] = useState("idle");
  const [seconds, setSeconds] = useState(0);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState("");
  const analysers = useRef([]); // read by the waveform
  const remoteAudio = useRef(null);
  const s = useRef({}); // pc, mic, ctx, ring, clock

  const tone = (freqs, ms) => {
    const ctx = s.current.ctx;
    if (!ctx) return;
    const g = ctx.createGain();
    g.gain.value = 0.06;
    g.connect(ctx.destination);
    freqs.forEach((f) => {
      const o = ctx.createOscillator();
      o.frequency.value = f;
      o.connect(g);
      o.start();
      o.stop(ctx.currentTime + ms / 1000);
    });
  };

  const listen = (stream) => {
    const an = s.current.ctx.createAnalyser();
    an.fftSize = 128;
    s.current.ctx.createMediaStreamSource(stream).connect(an);
    analysers.current.push(an);
  };

  const stop = useCallback(() => {
    const c = s.current;
    if (!c.active) return;
    c.active = false;
    clearInterval(c.ring);
    clearInterval(c.clock);
    tone([480, 620], 400);
    c.pc?.close();
    c.mic?.getTracks().forEach((t) => t.stop());
    analysers.current = [];
    setPhase("ended");
    onEnd?.();
    setTimeout(() => {
      c.ctx?.close();
      c.ctx = null;
      setPhase("idle");
    }, 1200);
  }, [onEnd]);

  const start = useCallback(async () => {
    const c = s.current;
    c.active = true;
    setError("");
    setSeconds(0);
    setMuted(false);
    setPhase("connecting");
    onStart?.();

    c.ctx = new (window.AudioContext || window.webkitAudioContext)();
    tone([440, 480], 900);
    c.ring = setInterval(() => tone([440, 480], 900), 2500);

    try {
      c.mic = await navigator.mediaDevices.getUserMedia({ audio: true });
      listen(c.mic);

      c.pc = new RTCPeerConnection({ iceServers: STUN });
      c.pc.ontrack = (e) => {
        // `event.streams` is allowed to be empty for a valid WebRTC track.
        // Build a stream from the track so playback does not depend on the
        // remote implementation attaching an MSID.
        const stream = e.streams[0] || new MediaStream([e.track]);
        const audio = remoteAudio.current;
        if (!audio) return;
        audio.srcObject = stream;
        e.track.onunmute = () => audio.play().catch(() => {});
        listen(stream);
        // The track arrives after the click that started the call. Explicitly
        // start playback because browsers may ignore autoplay in this case.
        audio.play().catch((err) => {
          console.warn("Remote audio playback was blocked", err);
          setError("Click the call screen to enable bot audio");
        });
      };
      c.pc.onconnectionstatechange = () => {
        const st = c.pc.connectionState;
        if (st === "connected") {
          clearInterval(c.ring);
          tone([660], 200);
          const t0 = Date.now();
          c.clock = setInterval(() => setSeconds(Math.floor((Date.now() - t0) / 1000)), 1000);
          setPhase("connected");
        }
        if (["failed", "closed", "disconnected"].includes(st)) stop();
      };
      c.mic.getTracks().forEach((t) => c.pc.addTrack(t, c.mic));
      c.pc.createDataChannel("chat");

      await c.pc.setLocalDescription(await c.pc.createOffer());
      await new Promise((resolve) => {
        if (c.pc.iceGatheringState === "complete") return resolve();
        c.pc.addEventListener("icegatheringstatechange", () => {
          if (c.pc.iceGatheringState === "complete") resolve();
        });
      });

      const res = await fetch("/api/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sdp: c.pc.localDescription.sdp, type: c.pc.localDescription.type }),
      });
      if (!res.ok) throw new Error("Server refused the call");
      await c.pc.setRemoteDescription(await res.json());
    } catch (err) {
      console.error(err);
      clearInterval(c.ring);
      c.active = false;
      c.pc?.close();
      c.mic?.getTracks().forEach((t) => t.stop());
      setError(err.name === "NotAllowedError" ? "Allow microphone access" : "Could not connect");
      setPhase("error");
    }
  }, [onStart, stop]);

  const toggleMute = () => {
    const next = !muted;
    s.current.mic?.getAudioTracks().forEach((t) => (t.enabled = !next));
    setMuted(next);
  };

  const dismiss = () => setPhase("idle");

  const enableAudio = useCallback(async () => {
    try {
      await s.current.ctx?.resume();
      if (remoteAudio.current?.srcObject) await remoteAudio.current.play();
      setError("");
    } catch (err) {
      console.warn("Could not start remote audio", err);
      setError("Browser blocked audio. Check the tab's sound permission.");
    }
  }, []);

  return { phase, seconds, muted, error, analysers, remoteAudio, start, stop, toggleMute, dismiss, enableAudio };
}
