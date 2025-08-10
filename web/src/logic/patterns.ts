import { BIT_ROMAJI, WARM_MARKS } from './constants';
import type { Mark } from './constants';

// CSV 1行を [0|1]×9 にパース
function parseCsvLine(line: string): number[] | null {
  const cols = line.split(',').map((s) => s.trim());
  if (cols.length < 9) return null;
  const bits: number[] = [];
  for (let i = 0; i < 9; i += 1) {
    const v = cols[i] === '' ? 0 : Number(cols[i]);
    if (Number.isNaN(v)) return null;
    bits.push(v ? 1 : 0);
  }
  return bits;
}

function bitsToMarks(bits: number[]): Mark[] {
  const marks: Mark[] = [];
  for (let i = 0; i < 9; i += 1) {
    const pair = BIT_ROMAJI[i + 1];
    const mark = pair[bits[i] as 0 | 1];
    marks.push(mark);
  }
  return marks;
}

function isValidPattern(marks: Mark[]): boolean {
  // Python版同様、同一マークが3枚以上含まれる行は除外
  const count: Record<Mark, number> = {
    Maru: 0,
    Cookie: 0,
    Sakura: 0,
    Lime: 0,
    Hanabana: 0,
    Brocco: 0,
  };
  for (const m of marks) count[m] += 1;
  return Object.values(count).every((c) => c < 3);
}

export type Pattern = {
  bits: number[]; // 0/1×9
  marks: Mark[];  // 展開済
  warmTotal: number;
};

export async function loadPatterns(): Promise<Pattern[]> {
  const res = await fetch('/data/512_Patterns_of_Nine_Tile.csv', { cache: 'no-store' });
  const text = await res.text();
  const patterns: Pattern[] = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const bits = parseCsvLine(line);
    if (!bits) continue;
    const marks = bitsToMarks(bits);
    if (!isValidPattern(marks)) continue;
    const warmTotal = marks.reduce((acc, m) => acc + (WARM_MARKS.has(m) ? 1 : 0), 0);
    patterns.push({ bits, marks, warmTotal });
  }
  if (patterns.length === 0) throw new Error('No valid patterns found in CSV');
  return patterns;
}

