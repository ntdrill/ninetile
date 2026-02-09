const ICON_BASE = "../ナインタイル解説doc/imgs/icons";
const CSV_PATH = "../ナインタイルpythonista/512_Patterns_of_Nine_Tile.csv";

const MARKS = {
  maru: { label: "Maru", icon: "donut.svg" },
  cookie: { label: "Cookie", icon: "cookie.svg" },
  sakura: { label: "Sakura", icon: "sakura.svg" },
  lime: { label: "Lime", icon: "lime.svg" },
  hanabi: { label: "Hanabi", icon: "hanabi.svg" },
  block: { label: "Block", icon: "block.svg" },
};

const CARDS = [
  ["maru", "cookie"], // e1
  ["maru", "sakura"], // e2
  ["maru", "block"], // e3 (cross)
  ["lime", "hanabi"], // e4
  ["lime", "sakura"], // e5 (cross)
  ["lime", "block"], // e6
  ["cookie", "hanabi"], // e7 (cross)
  ["cookie", "sakura"], // e8
  ["hanabi", "block"], // e9
];

const MARK_TO_CARDS = {
  maru: [0, 1, 2],
  cookie: [0, 6, 7],
  sakura: [1, 4, 7],
  lime: [3, 4, 5],
  hanabi: [3, 6, 8],
  block: [2, 5, 8],
};

const state = {
  patterns: [],
  initialPos: [],
  targetMarks: [],
  targetPos: [],
  cardMark: {},
  swapOps: [],
  states: [],
  stepIndex: 0,
};

const gridLeft = document.getElementById("grid-left");
const gridMid = document.getElementById("grid-mid");
const gridRight = document.getElementById("grid-right");
const infoEl = document.getElementById("info");
const statusEl = document.getElementById("status");
const resetBtn = document.getElementById("resetBtn");
const stepBtn = document.getElementById("stepBtn");
const loadBtn = document.getElementById("loadBtn");
const csvInput = document.getElementById("csvInput");

const leftCells = createGrid(gridLeft);
const midCells = createGrid(gridMid);
const rightCells = createGrid(gridRight);

resetBtn.addEventListener("click", () => resetState());
stepBtn.addEventListener("click", () => stepForward());
loadBtn.addEventListener("click", () => csvInput.click());
csvInput.addEventListener("change", (event) => {
  const file = event.target.files && event.target.files[0];
  if (file) loadPatternsFromFile(file);
  csvInput.value = "";
});

init();

async function init() {
  setSwapControlsEnabled(false);
  try {
    state.patterns = await loadPatterns();
    statusEl.textContent = `Loaded patterns: ${state.patterns.length}`;
    resetState();
    setSwapControlsEnabled(true);
  } catch (err) {
    statusEl.textContent = `Failed to load patterns. Use "Load CSV". ${err}`;
  }
}

function setSwapControlsEnabled(enabled) {
  resetBtn.disabled = !enabled;
  stepBtn.disabled = !enabled;
}

function createGrid(container) {
  const cells = [];
  for (let i = 0; i < 9; i += 1) {
    const tile = document.createElement("div");
    tile.className = "tile";
    const img = document.createElement("img");
    const label = document.createElement("span");
    tile.appendChild(img);
    tile.appendChild(label);
    container.appendChild(tile);
    cells.push({ tile, img, label });
  }
  return cells;
}

function setTile(cell, mark, cardId) {
  const info = MARKS[mark];
  cell.label.textContent = cardId;
  cell.tile.classList.remove("has-image");
  cell.img.onload = () => cell.tile.classList.add("has-image");
  cell.img.onerror = () => cell.tile.classList.remove("has-image");
  cell.img.alt = info.label;
  cell.img.src = encodeURI(`${ICON_BASE}/${info.icon}`);
}

async function loadPatterns() {
  const res = await fetch(encodeURI(CSV_PATH));
  if (!res.ok) {
    throw new Error(`CSV not found: ${CSV_PATH}`);
  }
  const text = await res.text();
  return parsePatterns(text);
}

function loadPatternsFromFile(file) {
  setSwapControlsEnabled(false);
  statusEl.textContent = `Loading ${file.name}...`;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      state.patterns = parsePatterns(reader.result);
      statusEl.textContent = `Loaded patterns from ${file.name}: ${state.patterns.length}`;
      resetState();
      setSwapControlsEnabled(true);
    } catch (err) {
      statusEl.textContent = `Failed to parse CSV. ${err}`;
    }
  };
  reader.onerror = () => {
    statusEl.textContent = "Failed to read CSV file.";
  };
  reader.readAsText(file);
}

function parsePatterns(text) {
  const lines = String(text).split(/\r?\n/);
  const patterns = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    const raw = line.split(",");
    const bits = raw.map((x) => (x.trim() === "" ? 0 : Number(x)));
    while (bits.length < 9) bits.push(0);
    const trimmed = bits.slice(0, 9);
    const marks = trimmed.map((bit, i) => CARDS[i][bit]);
    const counts = {};
    for (const m of marks) counts[m] = (counts[m] || 0) + 1;
    const maxCount = Math.max(...Object.values(counts));
    if (maxCount < 3) patterns.push(trimmed);
  }
  if (patterns.length === 0) {
    throw new Error("No valid patterns found in CSV");
  }
  return patterns;
}

function randomTopicMarks() {
  const bits = state.patterns[Math.floor(Math.random() * state.patterns.length)];
  const marks = bits.map((bit, i) => CARDS[i][bit]);
  shuffleInPlace(marks);
  return marks;
}

function minSwapsCount(start, target) {
  const targetIndex = new Map();
  target.forEach((card, idx) => targetIndex.set(card, idx));
  const visited = Array(start.length).fill(false);
  let cycles = 0;
  for (let i = 0; i < start.length; i += 1) {
    if (visited[i]) continue;
    let j = i;
    while (!visited[j]) {
      visited[j] = true;
      j = targetIndex.get(start[j]);
    }
    cycles += 1;
  }
  return start.length - cycles;
}

function computeSwaps(start, target) {
  const cur = start.slice();
  const posOfCard = new Map();
  cur.forEach((card, idx) => posOfCard.set(card, idx));
  const swaps = [];
  for (let i = 0; i < cur.length; i += 1) {
    const desired = target[i];
    if (cur[i] === desired) continue;
    const j = posOfCard.get(desired);
    swaps.push([i, j]);
    [cur[i], cur[j]] = [cur[j], cur[i]];
    posOfCard.set(cur[i], i);
    posOfCard.set(cur[j], j);
  }
  return swaps;
}

function findTargetArrangement(startPos, targetMarks) {
  const candidates = targetMarks.map((mark) => MARK_TO_CARDS[mark].slice());
  const order = Array.from({ length: 9 }, (_, i) => i).sort(
    (a, b) => candidates[a].length - candidates[b].length,
  );

  const used = Array(9).fill(false);
  const assignment = Array(9).fill(-1);
  let best = null;
  let bestSwaps = Infinity;

  function backtrack(k) {
    if (k === 9) {
      const swaps = minSwapsCount(startPos, assignment);
      if (swaps < bestSwaps) {
        bestSwaps = swaps;
        best = assignment.slice();
      }
      return;
    }
    const pos = order[k];
    for (const card of candidates[pos]) {
      if (used[card]) continue;
      assignment[pos] = card;
      used[card] = true;
      backtrack(k + 1);
      used[card] = false;
      assignment[pos] = -1;
    }
  }

  backtrack(0);
  if (!best) throw new Error("No valid assignment found");
  const cardMark = {};
  for (let pos = 0; pos < 9; pos += 1) {
    cardMark[best[pos]] = targetMarks[pos];
  }
  return { targetPos: best, cardMark, bestSwaps };
}

function resetState() {
  state.initialPos = Array.from({ length: 9 }, (_, i) => i);
  shuffleInPlace(state.initialPos);
  state.targetMarks = randomTopicMarks();
  const result = findTargetArrangement(state.initialPos, state.targetMarks);
  state.targetPos = result.targetPos;
  state.cardMark = result.cardMark;
  state.swapOps = computeSwaps(state.initialPos, state.targetPos);
  state.states = [state.initialPos.slice()];
  let cur = state.initialPos.slice();
  for (const [a, b] of state.swapOps) {
    cur = cur.slice();
    [cur[a], cur[b]] = [cur[b], cur[a]];
    state.states.push(cur);
  }
  state.stepIndex = 0;
  updateViews();
}

function stepForward() {
  if (state.stepIndex < state.swapOps.length) {
    state.stepIndex += 1;
    updateViews();
  }
}

function updateViews() {
  const leftMarks = marksForArrangement(state.initialPos);
  const midMarks = marksForArrangement(state.states[state.stepIndex]);
  const rightMarks = marksForArrangement(state.targetPos);
  const leftIds = idsForArrangement(state.initialPos);
  const midIds = idsForArrangement(state.states[state.stepIndex]);
  const rightIds = idsForArrangement(state.targetPos);
  setGrid(leftCells, leftMarks, leftIds);
  setGrid(midCells, midMarks, midIds);
  setGrid(rightCells, rightMarks, rightIds);

  infoEl.textContent = `swap: ${state.swapOps.length} | step: ${state.stepIndex}/${state.swapOps.length}`;
  stepBtn.disabled = state.stepIndex >= state.swapOps.length;
  statusEl.textContent =
    state.swapOps.length <= 5
      ? "swap count is within 5"
      : "swap count exceeded 5 (check assignment)";
}

function setGrid(cells, marks, ids) {
  for (let i = 0; i < cells.length; i += 1) {
    setTile(cells[i], marks[i], ids[i]);
  }
}

function marksForArrangement(arrangement) {
  return arrangement.map((card) => state.cardMark[card]);
}

function idsForArrangement(arrangement) {
  return arrangement.map((card) => `e${card + 1}`);
}

function shuffleInPlace(arr) {
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}