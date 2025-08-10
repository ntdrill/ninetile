import { CROSS_PAIRS, WARM_MARKS } from './constants';
import type { Mark } from './constants';

export type JudgeResult = {
  correct: boolean;
  conflict: boolean;
  reqWarm: number;
  reqCold: number;
};

export function judgeSelection(selected: Mark[], warmTotal: number): JudgeResult {
  // 必要枚数テーブル（Python版準拠）
  const reqMap: Record<number, [number, number]> = {
    6: [3, 0],
    5: [2, 1],
    4: [1, 2],
    3: [0, 3],
  };
  const req = reqMap[warmTotal] ?? [-1, -1];
  const [reqWarm, reqCold] = req;

  // 3枚のマークが全て異なる必要がある
  const unique = new Set(selected);
  const allDifferent = unique.size === 3;

  // 暖色/寒色の数
  const warmSel = selected.reduce((a, m) => a + (WARM_MARKS.has(m) ? 1 : 0), 0);
  const coldSel = 3 - warmSel;

  // クロス関係を含むか
  let conflict = false;
  const selSet = new Set<Mark>(selected);
  for (const pair of CROSS_PAIRS) {
    let ok = true;
    for (const m of pair) if (!selSet.has(m)) ok = false;
    if (ok) { conflict = true; break; }
  }

  const correct = !conflict && allDifferent && warmSel === reqWarm && coldSel === reqCold;
  return { correct, conflict, reqWarm, reqCold };
}

