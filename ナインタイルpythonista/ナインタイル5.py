# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import random
from pathlib import Path

import ui

SCRIPT_DIR = Path(__file__).resolve().parent
ICON_DIR = Path('/Users/numaoryuutarou/cursor/ninetile/ナインタイル解説doc/imgs/icons')
CSV_PATH = SCRIPT_DIR / '512_Patterns_of_Nine_Tile.csv'

CARDS = [
    ('Maru', 'Cookie'),   # e1
    ('Maru', 'Sakura'),   # e2
    ('Maru', 'Brocco'),   # e3 (cross)
    ('Lime', 'Hanabana'), # e4
    ('Lime', 'Sakura'),   # e5 (cross)
    ('Lime', 'Brocco'),   # e6
    ('Cookie', 'Hanabana'), # e7 (cross)
    ('Cookie', 'Sakura'), # e8
    ('Hanabana', 'Brocco')# e9
]

ICON_FILES = {
    'Maru': 'donut.svg',
    'Cookie': 'cookie.svg',
    'Sakura': 'sakura.svg',
    'Lime': 'lime.svg',
    'Hanabana': 'hanabi.svg',
    'Brocco': 'block.svg',
}


def load_patterns() -> list[list[int]]:
    patterns: list[list[int]] = []
    if not CSV_PATH.exists():
        raise SystemExit(f'CSV not found: {CSV_PATH}')
    with CSV_PATH.open(newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            bits = [int(x) if x else 0 for x in row]
            if len(bits) < 9:
                bits += [0] * (9 - len(bits))
            bits = bits[:9]
            marks = [CARDS[i][bit] for i, bit in enumerate(bits)]
            if max(marks.count(m) for m in set(marks)) < 3:
                patterns.append(bits)
    if not patterns:
        raise SystemExit('No valid patterns found in CSV')
    return patterns


PATTERNS = load_patterns()


def random_topic_marks() -> list[str]:
    bits = random.choice(PATTERNS)
    marks = [CARDS[i][bit] for i, bit in enumerate(bits)]
    random.shuffle(marks)
    return marks


def min_swaps(start: list[int], target: list[int]) -> int:
    target_index = {card: i for i, card in enumerate(target)}
    visited = [False] * len(start)
    cycles = 0
    for i in range(len(start)):
        if visited[i]:
            continue
        j = i
        while not visited[j]:
            visited[j] = True
            j = target_index[start[j]]
        cycles += 1
    return len(start) - cycles


def compute_swaps(start: list[int], target: list[int]) -> list[tuple[int, int]]:
    cur = start[:]
    pos_of_card = {card: i for i, card in enumerate(cur)}
    swaps: list[tuple[int, int]] = []
    for i in range(len(cur)):
        desired = target[i]
        if cur[i] == desired:
            continue
        j = pos_of_card[desired]
        swaps.append((i, j))
        cur[i], cur[j] = cur[j], cur[i]
        pos_of_card[cur[i]] = i
        pos_of_card[cur[j]] = j
    return swaps


class TileCell(ui.View):
    def __init__(self, size: float):
        super().__init__(frame=(0, 0, size, size))
        self.img_view = ui.ImageView(frame=self.bounds, flex='WH', content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
        self.lbl = ui.Label(frame=self.bounds, flex='WH', alignment=ui.ALIGN_CENTER,
                            font=('Menlo', max(10, int(size * 0.2))), text_color='white')
        self.add_subview(self.img_view)
        self.add_subview(self.lbl)

    def set_mark(self, mark: str, image: ui.Image | None):
        self.img_view.image = image
        if image is None:
            self.lbl.text = mark
            self.lbl.hidden = False
        else:
            self.lbl.hidden = True


class NineTileSwapApp(ui.View):
    def __init__(self):
        super().__init__(bg_color='#202124')
        self.present_style = 'fullscreen'
        self.mark_images = self._load_images()

        self.left_cells: list[TileCell] = []
        self.mid_cells: list[TileCell] = []
        self.right_cells: list[TileCell] = []

        self.initial_pos: list[int] = []
        self.target_marks: list[str] = []
        self.target_pos: list[int] = []
        self.card_mark: dict[int, str] = {}
        self.swap_ops: list[tuple[int, int]] = []
        self.states: list[list[int]] = []
        self.step_index = 0

        self._build_ui()
        self._reset()

    def _load_images(self) -> dict[str, ui.Image | None]:
        images: dict[str, ui.Image | None] = {}
        base = ICON_DIR
        for mark, fname in ICON_FILES.items():
            path = base / fname
            img = None
            try:
                img = ui.Image.named(str(path))
            except Exception:
                img = None
            images[mark] = img
        return images

    def _build_ui(self):
        screen_w, screen_h = ui.get_screen_size()
        self.frame = (0, 0, screen_w, screen_h)

        gap = 10
        grid_w = (screen_w - gap * 4) / 3
        tile = grid_w / 3
        label_h = 24
        top = 20
        grid_y = top + label_h + 6

        titles = ['初期状態', '変換（スワップ）', 'お題']
        grids = []
        for i in range(3):
            x = gap + i * (grid_w + gap)
            lbl = ui.Label(frame=(x, top, grid_w, label_h), alignment=ui.ALIGN_CENTER,
                           text=titles[i], text_color='white')
            self.add_subview(lbl)
            grid = ui.View(frame=(x, grid_y, grid_w, grid_w))
            self.add_subview(grid)
            grids.append(grid)

        self.left_cells = self._make_grid_cells(grids[0], tile)
        self.mid_cells = self._make_grid_cells(grids[1], tile)
        self.right_cells = self._make_grid_cells(grids[2], tile)

        btn_y = grid_y + grid_w + 16
        btn_w = 140
        self.btn_reset = ui.Button(title='RESET', frame=(gap, btn_y, btn_w, 36), action=self._on_reset)
        self.btn_step = ui.Button(title='STEP', frame=(gap + btn_w + 12, btn_y, btn_w, 36), action=self._on_step)
        for b in (self.btn_reset, self.btn_step):
            b.bg_color = '#4A4A4A'
            b.tint_color = 'white'
            b.corner_radius = 6
        self.add_subview(self.btn_reset)
        self.add_subview(self.btn_step)

        self.lbl_info = ui.Label(frame=(gap, btn_y + 44, screen_w - gap * 2, 22),
                                 alignment=ui.ALIGN_LEFT, text_color='gray')
        self.add_subview(self.lbl_info)

    def _make_grid_cells(self, grid: ui.View, tile: float) -> list[TileCell]:
        cells: list[TileCell] = []
        for idx in range(9):
            r, c = divmod(idx, 3)
            cell = TileCell(tile)
            cell.frame = (c * tile, r * tile, tile, tile)
            grid.add_subview(cell)
            cells.append(cell)
        return cells

    def _find_target_arrangement(self) -> tuple[list[int], dict[int, str], int]:
        candidates: list[list[int]] = []
        for mark in self.target_marks:
            candidates.append([i for i, pair in enumerate(CARDS) if mark in pair])
        order = sorted(range(9), key=lambda i: len(candidates[i]))

        used = [False] * 9
        assignment: list[int] = [-1] * 9
        best: list[int] | None = None
        best_swaps = 99

        def backtrack(k: int):
            nonlocal best, best_swaps
            if k == 9:
                target_pos = assignment[:]
                swaps = min_swaps(self.initial_pos, target_pos)
                if swaps < best_swaps:
                    best_swaps = swaps
                    best = target_pos[:]
                return
            pos = order[k]
            for card in candidates[pos]:
                if used[card]:
                    continue
                assignment[pos] = card
                used[card] = True
                backtrack(k + 1)
                used[card] = False
            assignment[pos] = -1

        backtrack(0)
        if best is None:
            raise SystemExit('No valid assignment found')
        card_mark: dict[int, str] = {}
        for pos, card in enumerate(best):
            card_mark[card] = self.target_marks[pos]
        return best, card_mark, best_swaps

    def _reset(self):
        self.initial_pos = list(range(9))
        random.shuffle(self.initial_pos)
        self.target_marks = random_topic_marks()
        self.target_pos, self.card_mark, _ = self._find_target_arrangement()

        self.swap_ops = compute_swaps(self.initial_pos, self.target_pos)
        self.states = [self.initial_pos[:]]
        cur = self.initial_pos[:]
        for a, b in self.swap_ops:
            cur = cur[:]
            cur[a], cur[b] = cur[b], cur[a]
            self.states.append(cur)
        self.step_index = 0
        self._update_views()

    def _on_reset(self, sender):
        self._reset()

    def _on_step(self, sender):
        if self.step_index < len(self.swap_ops):
            self.step_index += 1
            self._update_views()

    def _marks_for_arrangement(self, arrangement: list[int]) -> list[str]:
        return [self.card_mark[card] for card in arrangement]

    def _update_grid(self, cells: list[TileCell], marks: list[str]):
        for cell, mark in zip(cells, marks):
            cell.set_mark(mark, self.mark_images.get(mark))

    def _update_views(self):
        left_marks = self._marks_for_arrangement(self.initial_pos)
        mid_marks = self._marks_for_arrangement(self.states[self.step_index])
        self._update_grid(self.left_cells, left_marks)
        self._update_grid(self.mid_cells, mid_marks)
        self._update_grid(self.right_cells, self.target_marks)
        self.lbl_info.text = f'swap: {len(self.swap_ops)}   step: {self.step_index}/{len(self.swap_ops)}'


if __name__ == '__main__':
    NineTileSwapApp().present(hide_title_bar=True)
