import { useEffect, useMemo, useState } from 'react';
import './index.css';
import Tile from './components/Tile';
import type { Mark } from './logic/constants';
import { loadPatterns } from './logic/patterns';
import type { Pattern } from './logic/patterns';
import { judgeSelection } from './logic/judge';
import { formatElapsed, startTimer, stopTimer, unlockAudio } from './logic/timer';

type GameState = 'IDLE' | 'RUNNING' | 'PAUSED';

function App() {
  const [state, setState] = useState<GameState>('IDLE');
  const [patterns, setPatterns] = useState<Pattern[] | null>(null);
  const [current, setCurrent] = useState<Pattern | null>(null);
  const [shuffledMarks, setShuffledMarks] = useState<Mark[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number[]>([]);
  const [trial, setTrial] = useState(0);
  const [times, setTimes] = useState<number[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [feedback, setFeedback] = useState('Tap START →');

  useEffect(() => {
    loadPatterns().then(setPatterns).catch((e) => console.error(e));
  }, []);

  const gridSize = 3;
  const tilePx = 110;

  function nextPattern() {
    if (!patterns || patterns.length === 0) return;
    const p = patterns[Math.floor(Math.random() * patterns.length)];
    setCurrent(p);
    const order = [...p.marks];
    for (let i = order.length - 1; i >= 1; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    setShuffledMarks(order);
    setSelectedIdx([]);
    setFeedback('Tap START →');
    setState('IDLE');
  }

  useEffect(() => {
    if (patterns && patterns.length > 0) {
      nextPattern();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patterns]);

  function onToggleTile(idx: number) {
    if (state !== 'RUNNING') return;
    setSelectedIdx((prev) => {
      const exists = prev.includes(idx);
      const next = exists ? prev.filter((i) => i !== idx) : [...prev, idx];
      return next.slice(0, 3);
    });
  }

  useEffect(() => {
    if (state !== 'RUNNING') return;
    if (selectedIdx.length === 3 && current) {
      // 判定
      const marks = selectedIdx.map((i) => shuffledMarks[i]);
      const res = judgeSelection(marks, current.warmTotal);
      stopTimer();
      setTimes((t) => [...t, elapsed]);
      setTrial((n) => n + 1);
      const msg = res.correct ? '✅ Correct!' : `❌ Incorrect${res.conflict ? ' (Conflict)' : ''}`;
      setFeedback(`${msg} | ${elapsed.toFixed(2)}s`);
      setState('PAUSED');
    }
  }, [selectedIdx]);

  function onMainButton() {
    if (state === 'IDLE') {
      unlockAudio();
      setElapsed(0);
      startTimer((sec) => setElapsed(sec));
      setFeedback('');
      setState('RUNNING');
    } else if (state === 'RUNNING') {
      stopTimer();
      setTimes((t) => [...t, elapsed]);
      setTrial((n) => n + 1);
      setFeedback(`⏸ ${elapsed.toFixed(2)}s recorded – tap to NEXT →`);
      setState('PAUSED');
    } else {
      if (trial >= 30) return; // 後でfinish処理
      nextPattern();
      unlockAudio();
      setElapsed(0);
      startTimer((sec) => setElapsed(sec));
      setState('RUNNING');
    }
  }

  const avg = useMemo(() => {
    if (times.length === 0) return 0;
    return times.reduce((a, b) => a + b, 0) / times.length;
  }, [times]);

  const finished = trial >= 30;

  return (
    <div className="container">
      <div className="timer">{formatElapsed(elapsed)}</div>
      <div className="grid" style={{ gridTemplateColumns: `repeat(${gridSize}, ${tilePx}px)` }}>
        {shuffledMarks.map((m, i) => (
          <Tile key={i} mark={m} selected={selectedIdx.includes(i)} onToggle={() => onToggleTile(i)} sizePx={tilePx} />
        ))}
      </div>
      <div className="feedback">{finished ? `🎉 Finished! Average: ${avg.toFixed(2)}s` : feedback}</div>
      {!finished && (
        <button className="mainbtn" onClick={onMainButton}>{state === 'IDLE' ? 'START' : state === 'RUNNING' ? 'STOP' : 'NEXT'}</button>
      )}
    </div>
  );
}

export default App;
