import { useCallback, useEffect, useState } from "react";
import Doctors from "./components/Doctors.jsx";
import Appointments from "./components/Appointments.jsx";
import Phone from "./components/Phone.jsx";
import { useCall } from "./hooks/useCall.js";
import { useEvents } from "./hooks/useEvents.js";

export default function App() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [flashId, setFlashId] = useState(null);
  const [ghost, setGhost] = useState(null);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [dr, ar] = await Promise.all([fetch("/api/doctors"), fetch("/api/appointments")]);
      if (!dr.ok || !ar.ok) throw new Error("Backend API is unavailable");
      setDoctors(await dr.json());
      setAppointments(await ar.json());
      setLoadError("");
    } catch (err) {
      setLoadError("Cannot load clinic data. Make sure the backend is running on port 7860.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const retry = setInterval(refresh, 3000);
    return () => clearInterval(retry);
  }, [refresh]);

  // Backend tells us when the agent books or cancels: refresh and highlight the row.
  const { items, clear } = useEvents((booked, appt) => {
    refresh();
    if (booked) {
      setFlashId(appt.id);
      setTimeout(() => setFlashId(null), 2500);
    } else {
      setGhost(appt);
      setTimeout(() => setGhost(null), 1600);
    }
  });

  const call = useCall({ onStart: clear, onEnd: refresh });

  return (
    <div className="simple-app"><main className="booking-page"><div className="simple-brand"><span>✚</span> ClinicFlow</div><section className="booking-hero"><div><p className="eyebrow">YOUR HEALTH, MADE SIMPLE</p><h1>Book your next<br /><span>appointment</span> easily.</h1><p>Talk to our friendly assistant and find the right doctor and time in seconds.</p><button className="book-button" onClick={call.start} disabled={call.phase !== "idle"}>Book an appointment <b>→</b></button></div><div className="robo-illustration"><div className="robo-face big">◉‿◉</div><div className="robo-spark">✦</div><strong>Doctor Robo</strong><small>Your booking assistant</small></div></section>{loadError && <div className="empty">{loadError}</div>}<section className="upcoming"><div className="section-heading"><div><p className="eyebrow">YOUR SCHEDULE</p><h2>Upcoming appointments</h2></div><span className="count">{appointments.length}</span></div><Appointments appointments={appointments} flashId={flashId} ghost={ghost} /></section></main>
      {call.phase !== "idle" && <Phone call={call} items={items} />}
      <audio ref={call.remoteAudio} autoPlay playsInline />
    </div>
  );
}
