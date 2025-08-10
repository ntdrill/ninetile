// タイマーとビープ音（短音/長音）を生成

type TickHandler = (elapsed: number) => void;

let running = false;
let startAt = 0;
let rafId = 0 as number | 0;
let lastSec = -1;

let audioCtx: AudioContext | null = null;

export function unlockAudio(): void {
  if (!audioCtx) {
    try {
      audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      // 無音を短く鳴らして解放
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.frequency.value = 20;
      g.gain.value = 0;
      o.connect(g).connect(audioCtx.destination);
      o.start();
      o.stop(audioCtx.currentTime + 0.01);
    } catch {
      audioCtx = null;
    }
  }
}

function beep(durationMs: number, freqHz: number): void {
  if (!audioCtx) return;
  const o = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  o.type = 'sine';
  o.frequency.value = freqHz;
  g.gain.setValueAtTime(0.0001, audioCtx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.1, audioCtx.currentTime + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + durationMs / 1000);
  o.connect(g).connect(audioCtx.destination);
  o.start();
  o.stop(audioCtx.currentTime + durationMs / 1000 + 0.02);
}

export function startTimer(onTick: TickHandler): void {
  running = true;
  startAt = performance.now();
  lastSec = -1;

  const loop = () => {
    if (!running) return;
    const now = performance.now();
    const elapsed = (now - startAt) / 1000;
    onTick(elapsed);
    const curSec = Math.floor(elapsed);
    if (curSec !== lastSec) {
      const isLong = curSec % 3 === 0;
      // 3秒毎に長音、それ以外は短音
      beep(isLong ? 180 : 90, isLong ? 880 : 660);
      lastSec = curSec;
    }
    rafId = requestAnimationFrame(loop);
  };
  rafId = requestAnimationFrame(loop);
}

export function stopTimer(): void {
  running = false;
  if (rafId) cancelAnimationFrame(rafId);
}

export function formatElapsed(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const cs = Math.floor((sec - Math.floor(sec)) * 100);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s
    .toString()
    .padStart(2, '0')}.${cs.toString().padStart(2, '0')}`;
}

