import { useEffect, useRef, useState } from "react";

// Listens to the backend's live event stream (transcript lines + booking/cancel events).
export function useEvents(onAppointment) {
  const [items, setItems] = useState([]);
  const cb = useRef(onAppointment);
  cb.current = onAppointment;

  useEffect(() => {
    const es = new EventSource("/api/events");
    es.onmessage = (e) => {
      const ev = JSON.parse(e.data);
      if (ev.type === "transcript") {
        setItems((p) => [...p, { kind: "msg", role: ev.role, text: ev.text }]);
      } else if (ev.type === "appointment") {
        const booked = ev.action === "booked";
        setItems((p) => [...p, { kind: "card", booked, appt: ev.appointment }]);
        cb.current(booked, ev.appointment);
      }
    };
    return () => es.close();
  }, []);

  return { items, clear: () => setItems([]) };
}
