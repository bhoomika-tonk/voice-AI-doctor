import { useEffect, useRef } from "react";

// Draws bars that react to both your voice and the agent's voice.
export default function Waveform({ analysers }) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    const g = canvas.getContext("2d");
    const N = 32;
    let raf;
    const draw = () => {
      const { width: W, height: H } = canvas;
      g.clearRect(0, 0, W, H);
      const bars = new Array(N).fill(0);
      analysers.current.forEach((an) => {
        const d = new Uint8Array(an.frequencyBinCount);
        an.getByteFrequencyData(d);
        for (let i = 0; i < N; i++) bars[i] = Math.max(bars[i], d[Math.floor((i * d.length) / N / 2)] / 255);
      });
      g.fillStyle = "#12d1a9";
      const w = W / N;
      bars.forEach((v, i) => {
        const h = Math.max(4, v * H);
        g.fillRect(i * w + 3, (H - h) / 2, w - 6, h);
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [analysers]);

  return <canvas ref={ref} width="600" height="112" aria-hidden="true" />;
}