// 定数・型定義（Pythonista版 ナインタイル_3.py をTypeScriptへ移植）

export type Mark = 'Maru' | 'Cookie' | 'Sakura' | 'Lime' | 'Hanabana' | 'Brocco';

export const WARM_MARKS: Set<Mark> = new Set(['Maru', 'Cookie', 'Sakura']);

// 画像ファイル名のマッピング（public/assets への相対パス）
export const MARK_TO_IMAGE: Record<Mark, string> = {
  Maru: '/assets/maru.png',
  Cookie: '/assets/cookie.png',
  Sakura: '/assets/sakura.png',
  Lime: '/assets/lime.png',
  Hanabana: '/assets/hanabi.png',
  Brocco: '/assets/block.png',
};

// CSVの各ビット位置 1..9 で、0/1 がどのマークに対応するか
// Python版の BIT_ROMAJI をそのまま踏襲
export const BIT_ROMAJI: Record<number, [Mark, Mark]> = {
  1: ['Maru', 'Cookie'],
  2: ['Maru', 'Sakura'],
  3: ['Maru', 'Brocco'],
  4: ['Lime', 'Hanabana'],
  5: ['Lime', 'Sakura'],
  6: ['Lime', 'Brocco'],
  7: ['Cookie', 'Hanabana'],
  8: ['Cookie', 'Sakura'],
  9: ['Hanabana', 'Brocco'],
};

// クロス関係（同時に選択するとNG）
export const CROSS_PAIRS: Array<Set<Mark>> = [
  new Set(['Maru', 'Brocco']),
  new Set(['Lime', 'Sakura']),
  new Set(['Cookie', 'Hanabana']),
];

export type TileInfo = {
  mark: Mark;
  isWarm: boolean;
};

