const ICON_BASE = "./icons";

const MARKS = {
  maru: { icon: "donut.svg", label: "Maru" },
  cookie: { icon: "cookie.svg", label: "Cookie" },
  sakura: { icon: "sakura.svg", label: "Sakura" },
  lime: { icon: "lime.svg", label: "Lime" },
  hanabi: { icon: "hanabi.svg", label: "Hanabi" },
  block: { icon: "block.svg", label: "Block" },
};

const CARDS = [
  ["maru", "cookie"], // e1
  ["maru", "sakura"], // e2
  ["maru", "block"], // e3
  ["lime", "hanabi"], // e4
  ["lime", "sakura"], // e5
  ["lime", "block"], // e6
  ["cookie", "hanabi"], // e7
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

const leftCells = createGrid(gridLeft);
const midCells = createGrid(gridMid);
const rightCells = createGrid(gridRight);
const midOverlay = createOverlay(gridMid);

resetBtn.addEventListener("click", () => resetState());
stepBtn.addEventListener("click", () => stepForward());
window.addEventListener("resize", () => updateViews());

init();

function init() {
  state.patterns = generateValidPatterns();
  statusEl.textContent = `Generated patterns: ${state.patterns.length}`;
  resetState();
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

function createOverlay(container) {
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.classList.add("overlay");

  const warmLine = document.createElementNS(svgNS, "polyline");
  warmLine.setAttribute("fill", "none");
  warmLine.setAttribute("stroke", "#ff5252");
  warmLine.setAttribute("stroke-linecap", "round");
  warmLine.setAttribute("stroke-linejoin", "round");

  const warmStart = document.createElementNS(svgNS, "circle");
  warmStart.setAttribute("fill", "#ff5252");

  const coldLine = document.createElementNS(svgNS, "polyline");
  coldLine.setAttribute("fill", "none");
  coldLine.setAttribute("stroke", "#4fc3f7");
  coldLine.setAttribute("stroke-linecap", "round");
  coldLine.setAttribute("stroke-linejoin", "round");

  const coldStart = document.createElementNS(svgNS, "circle");
  coldStart.setAttribute("fill", "#4fc3f7");

  svg.appendChild(warmLine);
  svg.appendChild(warmStart);
  svg.appendChild(coldLine);
  svg.appendChild(coldStart);
  container.appendChild(svg);

  return { svg, warmLine, warmStart, coldLine, coldStart };
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

function generateValidPatterns() {
  const patterns = [];
  for (let i = 0; i < 512; i += 1) {
    const bits = [];
    for (let b = 8; b >= 0; b -= 1) {
      bits.push((i >> b) & 1);
    }
    const marks = bits.map((bit, idx) => CARDS[idx][bit]);
    const counts = {};
    for (const m of marks) counts[m] = (counts[m] || 0) + 1;
    const maxCount = Math.max(...Object.values(counts));
    if (maxCount < 3) patterns.push(bits);
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
  updateMidOverlay(state.states[state.stepIndex]);

  infoEl.textContent = `swap: ${state.swapOps.length} | step: ${state.stepIndex}/${state.swapOps.length}`;
  stepBtn.disabled = state.stepIndex >= state.swapOps.length;
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

function updateMidOverlay(arrangement) {
  if (!midOverlay || !arrangement) return;
  const containerRect = gridMid.getBoundingClientRect();
  const width = containerRect.width;
  const height = containerRect.height;
  midOverlay.svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  midOverlay.svg.setAttribute("width", width);
  midOverlay.svg.setAttribute("height", height);

  const tileRect = midCells[0].tile.getBoundingClientRect();
  const lineWidth = Math.max(2, tileRect.width * 0.08);
  const dotRadius = Math.max(4, tileRect.width * 0.14);
  midOverlay.warmLine.setAttribute("stroke-width", lineWidth);
  midOverlay.coldLine.setAttribute("stroke-width", lineWidth);
  midOverlay.warmStart.setAttribute("r", dotRadius);
  midOverlay.coldStart.setAttribute("r", dotRadius);

  const warmCards = [0, 7, 1]; // e1 -> e8 -> e2
  const coldCards = [3, 8, 5]; // e4 -> e9 -> e6
  const warmPoints = warmCards.map((cardId) =>
    centerForCard(arrangement, cardId, containerRect),
  );
  const coldPoints = coldCards.map((cardId) =>
    centerForCard(arrangement, cardId, containerRect),
  );

  midOverlay.warmLine.setAttribute("points", pointsToString(warmPoints));
  midOverlay.coldLine.setAttribute("points", pointsToString(coldPoints));
  midOverlay.warmStart.setAttribute("cx", warmPoints[0].x);
  midOverlay.warmStart.setAttribute("cy", warmPoints[0].y);
  midOverlay.coldStart.setAttribute("cx", coldPoints[0].x);
  midOverlay.coldStart.setAttribute("cy", coldPoints[0].y);
}

function centerForCard(arrangement, cardId, containerRect) {
  const pos = arrangement.indexOf(cardId);
  const cell = midCells[pos];
  const rect = cell.tile.getBoundingClientRect();
  return {
    x: rect.left + rect.width / 2 - containerRect.left,
    y: rect.top + rect.height / 2 - containerRect.top,
  };
}

function pointsToString(points) {
  return points.map((p) => `${p.x},${p.y}`).join(" ");
}

function shuffleInPlace(arr) {
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
