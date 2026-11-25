import { fmtDay, fmtTime } from "../lib/format.js";

// flashId: row to highlight after a booking. ghost: a just-cancelled row shown struck through.
export default function Appointments({ appointments, flashId, ghost }) {
  const rows = ghost ? [...appointments, ghost] : appointments;
  return (
    <section>
      <div className="section-heading"><h2>Appointments</h2><button className="text-action">View all →</button></div>
      {rows.length === 0 ? (
        <div className="empty">No appointments yet.</div>
      ) : (
        <table>
          <thead>
            <tr><th>Phone</th><th>Doctor</th><th>When</th></tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id} className={ghost && a.id === ghost.id ? "gone" : a.id === flashId ? "flash" : ""}>
                <td>{a.phone}</td>
                <td>{a.doctor}</td>
                <td>{fmtDay(a.date)}, {fmtTime(a.time)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
