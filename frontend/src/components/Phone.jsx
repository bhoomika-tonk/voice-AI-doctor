import { useEffect, useRef } from "react";
import Waveform from "./Waveform.jsx";
import { fmtClock, fmtDay, fmtTime } from "../lib/format.js";

export default function Phone({ call, items }) {
  const { phase, seconds, muted, error, analysers, stop, toggleMute, dismiss, enableAudio } = call;
  const log = useRef(null);

  useEffect(() => {
    log.current?.scrollTo({ top: log.current.scrollHeight });
  }, [items]);

  const status =
    phase === "connecting" ? "Calling…" :
    phase === "connected" ? fmtClock(seconds) :
    phase === "ended" ? "Call ended" : error;

  return (
    <div className="scrim" role="dialog" aria-label="Call with Asha">
      <div className="phone">
        <div className="who">
          <div className="avatar">A</div>
          <h3>Asha</h3>
          <div className="status">{status}</div>
        {phase === "connected" && error && <button onClick={enableAudio}>Enable bot audio</button>}
        </div>

        <Waveform analysers={analysers} />

        <div className="log" ref={log} aria-live="polite">
          {items.map((it, i) =>
            it.kind === "msg" ? (
              <div key={i} className={`m ${it.role}`}>{it.text}</div>
            ) : (
              <div key={i} className={`card ${it.booked ? "" : "cancel"}`}>
                <b>{it.booked ? "Booked" : "Cancelled"}</b>
                {it.appt.doctor}<br />
                {fmtDay(it.appt.date)}, {fmtTime(it.appt.time)}
              </div>
            )
          )}
        </div>

        <div className="ctl">
          <button className={muted ? "on" : ""} aria-pressed={muted} onClick={toggleMute}>Mute</button>
          <button className="end" onClick={phase === "error" ? dismiss : stop}>
            {phase === "error" ? "Close" : "End"}
          </button>
        </div>
      </div>
    </div>
  );
}
