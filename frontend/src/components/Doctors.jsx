import { fmtDay, fmtTime } from "../lib/format.js";

export default function Doctors({ doctors }) {
  return (
    <section>
      <h2>Doctors</h2>
      {doctors.map((d) => {
        const byDay = {};
        d.slots.forEach((s) => (byDay[s.date] ??= []).push(s.time));
        const days = Object.keys(byDay);
        return (
          <div className="doc" key={d.id}>
            <button className="small-action">View schedule</button>
            <b>{d.name}</b>
            <span className="sp">{d.speciality}</span>
            {days.length === 0 && <div className="day"><small>Fully booked</small></div>}
            {days.map((day) => (
              <div className="day" key={day}>
                <small>{fmtDay(day)}</small>
                {byDay[day].map((t) => (
                  <span className="pill" key={t}>{fmtTime(t)}</span>
                ))}
              </div>
            ))}
          </div>
        );
      })}
    </section>
  );
}
