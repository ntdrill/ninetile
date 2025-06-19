# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, random, time
from pathlib import Path
from collections import deque
from typing import List, Dict, Set, Tuple, Optional

import ui, sound, numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH   = SCRIPT_DIR / '512_Patterns_of_Nine_Tile.csv'

IMAGE_FILES: Dict[str, Path] = {
    'Brocco':   SCRIPT_DIR / 'ブロック.png',
    'Cookie':   SCRIPT_DIR / 'クッキー.png',
    'Maru':     SCRIPT_DIR / '丸.png',
    'Lime':     SCRIPT_DIR / 'ライム.png',
    'Sakura':   SCRIPT_DIR / 'サクラ.png',
    'Hanabana': SCRIPT_DIR / '花火.png',
}

SE_CORRECT   = SCRIPT_DIR / 'correct_sound.wav'
SE_INCORRECT = SCRIPT_DIR / 'incorrect_sound_soft.wav'
SE_CONFLICT  = SCRIPT_DIR / 'incorrect_sound_alt.wav'
BEEP_SHORT   = 'arcade:Coin_2'
BEEP_LONG    = 'arcade:Coin_3'

WARM_MARKS: Set[str] = {'Maru', 'Cookie', 'Sakura'}

BIT_ROMAJI = {
    1: ['Maru', 'Cookie'],
    2: ['Maru', 'Sakura'],
    3: ['Maru', 'Brocco'],
    4: ['Lime', 'Hanabana'],
    5: ['Lime', 'Sakura'],
    6: ['Lime', 'Brocco'],
    7: ['Cookie', 'Hanabana'],
    8: ['Cookie', 'Sakura'],
    9: ['Hanabana', 'Brocco'],
}

KEY_ROMAJI = {
    'A': ['Maru', 'Cookie'],
    'B': ['Cookie', 'Sakura'],
    'C': ['Lime', 'Sakura'],
    'D': ['Lime', 'Hanabana'],
    'E': ['Hanabana', 'Brocco'],
    'F': ['Maru', 'Brocco'],
    'α': ['Cookie', 'Hanabana'],
    'β': ['Maru', 'Sakura'],
    'γ': ['Lime', 'Brocco'],
}
REV_KEY = {tuple(v): k for k, v in KEY_ROMAJI.items()}

CROSS_PAIRS: List[Set[str]] = [
    {'Maru', 'Brocco'},
    {'Lime', 'Sakura'},
    {'Cookie', 'Hanabana'},
]

def load_patterns() -> List[List[int]]:
    patterns: List[List[int]] = []
    if pd is not None:
        df = pd.read_csv(CSV_PATH, header=None).fillna(0).astype(int)
        for row in df.itertuples(index=False):
            marks = [BIT_ROMAJI[i + 1][bit] for i, bit in enumerate(row)]
            _, counts = np.unique(marks, return_counts=True)
            if np.all(counts < 3):
                patterns.append(list(row))
    else:
        with CSV_PATH.open(newline='') as f:
            reader = csv.reader(f)
            for line in reader:
                bits = [int(x) if x else 0 for x in line]
                if len(bits) < 9:
                    bits += [0] * (9 - len(bits))
                marks = [BIT_ROMAJI[i + 1][bit] for i, bit in enumerate(bits)]
                if max(marks.count(m) for m in set(marks)) < 3:
                    patterns.append(bits[:9])
    if not patterns:
        raise ValueError('No valid patterns found in CSV')
    return patterns

PATTERNS: List[List[int]] = load_patterns()
_player: Optional[sound.Player] = None

def play_effect(effect):
    global _player
    try:
        if isinstance(effect, Path):
            _player = sound.Player(str(effect))
            _player.play()
        else:
            sound.play_effect(effect)
    except Exception:
        pass

class Tile(ui.View):
    def __init__(self, info: Dict, callback, problem_index: int):
        super().__init__(frame=(0, 0, 90, 90))
        self.info = info
        self.callback = callback
        self.problem_index = problem_index
        img = ui.Image.named(str(IMAGE_FILES[info['mark']]))
        img_view = ui.ImageView(frame=self.bounds, flex='WH', image=img,
                                content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
        self.add_subview(img_view)
        self.overlay = ui.View(frame=self.bounds, flex='WH', background_color=(0, 0, 0, 0.3))
        self.overlay.hidden = True
        self.add_subview(self.overlay)

    def touch_ended(self, t):
        if (t.location[0] - t.prev_location[0]) ** 2 + (t.location[1] - t.prev_location[1]) ** 2 > 16:
            return
        self.overlay.hidden = not self.overlay.hidden
        self.callback(self, self.problem_index)

    def reset(self):
        self.overlay.hidden = True
        self.touch_enabled = True

    @property
    def selected(self):
        return not self.overlay.hidden

class NineTileApp(ui.View):
    def __init__(self):
        super().__init__(bg_color='#202124')
        self.flex = 'WH'
        
        self.state = 'IDLE'
        self.trial = 0
        self.times: List[float] = []
        self.start_t = 0.0
        self.running = False
        self._timer_active = False
        self.last_sec = -1
        self.logs: deque[str] = deque(maxlen=4)

        # Problem 1 state
        self.pattern1: Optional[List[int]] = None
        self.tiles1: List[Tile] = []
        self.selected_idx1: List[int] = []
        self.warm_total1 = 0
        self.solved1 = False

        # Problem 2 state
        self.pattern2: Optional[List[int]] = None
        self.tiles2: List[Tile] = []
        self.selected_idx2: List[int] = []
        self.warm_total2 = 0
        self.solved2 = False

        self._build_ui()
        self._next_round()

    def _build_ui(self):
        screen_w, screen_h = ui.get_screen_size()
        self.frame = (0, 0, screen_w, screen_h)

        top_margin = 60
        bottom_margin = 150
        container_h = screen_h - top_margin - bottom_margin
        
        panel_w = screen_w / 2
        
        self.panel1 = ui.View(frame=(0, top_margin, panel_w, container_h))
        self.panel2 = ui.View(frame=(panel_w, top_margin, panel_w, container_h))
        self.add_subview(self.panel1)
        self.add_subview(self.panel2)

        self.TILE_SIZE = (panel_w - 40) / 3
        
        self.grid1 = ui.View(frame=(20, 40, self.TILE_SIZE * 3, self.TILE_SIZE * 3))
        self.grid2 = ui.View(frame=(20, 40, self.TILE_SIZE * 3, self.TILE_SIZE * 3))
        self.panel1.add_subview(self.grid1)
        self.panel2.add_subview(self.grid2)

        self.lbl_feedback1 = ui.Label(frame=(0, self.grid1.y + self.grid1.height + 4, panel_w, 24),
                                      alignment=ui.ALIGN_CENTER, text_color='skyblue')
        self.lbl_feedback2 = ui.Label(frame=(0, self.grid2.y + self.grid2.height + 4, panel_w, 24),
                                      alignment=ui.ALIGN_CENTER, text_color='skyblue')
        self.panel1.add_subview(self.lbl_feedback1)
        self.panel2.add_subview(self.lbl_feedback2)

        self.lbl_timer = ui.Label(frame=(0, 20, screen_w, 24), alignment=ui.ALIGN_CENTER,
                                  font=('Menlo', 20), text='00:00:00.00', text_color='white')
        self.add_subview(self.lbl_timer)

        self.lbl_log = ui.Label(frame=(10, screen_h - 60, screen_w - 20, 50), font=('Menlo', 10),
                                number_of_lines=4, text_color='gray')
        self.add_subview(self.lbl_log)

        btn_y = self.panel1.y + container_h + 20
        self.btn_main = ui.Button(title='START', frame=((screen_w-300)/2, btn_y, 300, 50),
                                  action=self._on_main_button, bg_color='#4A4A4A',
                                  tint_color='white', border_width=0.5, corner_radius=6)
        self.add_subview(self.btn_main)

    def _on_main_button(self, sender):
        if self.state == 'IDLE':
            self.state = 'RUNNING'
            self.btn_main.title = 'CHECKING...'
            self.btn_main.enabled = False
            for t in self.tiles1 + self.tiles2: t.reset()
            self._start_timer()
            
        elif self.state == 'PAUSED':
            self._next_round()

    def _setup_problem(self, p_idx: int):
        grid = self.grid1 if p_idx == 1 else self.grid2
        
        for v in list(grid.subviews):
            v.remove_from_superview()

        pattern = random.choice(PATTERNS)
        infos = []
        warm_count = 0
        for i, bit in enumerate(pattern):
            mark = BIT_ROMAJI[i + 1][bit]
            warm = mark in WARM_MARKS
            warm_count += warm
            infos.append({'mark': mark, 'is_warm': warm, 'key': REV_KEY[tuple(BIT_ROMAJI[i + 1])]})
        random.shuffle(infos)
        
        tiles = []
        for idx, info in enumerate(infos):
            r, c = divmod(idx, 3)
            tile = Tile(info, callback=self._on_tile, problem_index=p_idx)
            tile.frame = (c * self.TILE_SIZE, r * self.TILE_SIZE, self.TILE_SIZE, self.TILE_SIZE)
            grid.add_subview(tile)
            tiles.append(tile)

        if p_idx == 1:
            self.pattern1, self.tiles1, self.warm_total1 = pattern, tiles, warm_count
            self.selected_idx1.clear()
            self.solved1 = False
            self.lbl_feedback1.text = ''
        else:
            self.pattern2, self.tiles2, self.warm_total2 = pattern, tiles, warm_count
            self.selected_idx2.clear()
            self.solved2 = False
            self.lbl_feedback2.text = ''

    def _next_round(self):
        if self.trial >= 15: # 15 rounds of 2 problems = 30 total
            return self._finish()

        self.state = 'IDLE'
        self.btn_main.title = 'START'
        self.btn_main.enabled = True
        
        self._setup_problem(1)
        self._setup_problem(2)

        self._log(f"--- Round {self.trial + 1} ---")
        self._log(f"[Left] Warm={self.warm_total1} [Right] Warm={self.warm_total2}")

    def _on_tile(self, tile: Tile, p_idx: int):
        if self.state != 'RUNNING':
            tile.overlay.hidden = not tile.overlay.hidden # revert visual
            return

        selected_idx = self.selected_idx1 if p_idx == 1 else self.selected_idx2
        tiles = self.tiles1 if p_idx == 1 else self.tiles2
        is_solved = self.solved1 if p_idx == 1 else self.solved2

        if is_solved:
            tile.overlay.hidden = not tile.overlay.hidden # revert visual
            return
            
        idx = tiles.index(tile)
        if tile.selected:
            if idx not in selected_idx: selected_idx.append(idx)
        else:
            if idx in selected_idx: selected_idx.remove(idx)
        
        if len(selected_idx) == 3:
            self._check_answer(p_idx)

    def _tick_loop(self):
        if not self._timer_active: return
        self._tick()
        ui.delay(self._tick_loop, 0.05)

    def _tick(self):
        el = time.perf_counter() - self.start_t
        h, m = divmod(el, 3600); m, s = divmod(m, 60)
        self.lbl_timer.text = f"{int(h):02d}:{int(m):02d}:{int(s):02d}.{int((el - int(el)) * 100):02d}"
        cur = int(el)
        if cur != self.last_sec:
            play_effect(BEEP_LONG if cur % 3 == 0 else BEEP_SHORT)
            self.last_sec = cur

    def _start_timer(self):
        self.start_t = time.perf_counter()
        self.running = True
        self._timer_active = True
        self.last_sec = -1
        self._tick_loop()

    def _stop_timer(self):
        self.running = False
        self._timer_active = False

    def _check_answer(self, p_idx: int):
        tiles = self.tiles1 if p_idx == 1 else self.tiles2
        selected_idx = self.selected_idx1 if p_idx == 1 else self.selected_idx2
        warm_total = self.warm_total1 if p_idx == 1 else self.warm_total2
        lbl_feedback = self.lbl_feedback1 if p_idx == 1 else self.lbl_feedback2

        marks = {tiles[i].info['mark'] for i in selected_idx}
        warm_sel = sum(tiles[i].info['is_warm'] for i in selected_idx)
        cold_sel = 3 - warm_sel
        conflict = any(pair.issubset(marks) for pair in CROSS_PAIRS)
        req_warm, req_cold = {6: (3, 0), 5: (2, 1), 4: (1, 2), 3: (0, 3)}.get(warm_total, (-1, -1))
        correct = (not conflict) and warm_sel == req_warm and cold_sel == req_cold and len(marks) == 3

        if correct:
            play_effect(SE_CORRECT)
            lbl_feedback.text = '✅ Correct!'
            lbl_feedback.text_color = '#00C853'
            if p_idx == 1: self.solved1 = True
            else: self.solved2 = True
            
            for i in selected_idx: tiles[i].touch_enabled = False
            for tile in tiles:
                if not tile.selected: tile.reset() # Deselect others
                
        else: # Incorrect
            play_effect(SE_CONFLICT if conflict else SE_INCORRECT)
            msg = '❌ Incorrect' + (' (Conflict)' if conflict else '')
            lbl_feedback.text = msg
            lbl_feedback.text_color = '#FF5252'
            # Reset selection on incorrect
            for i in selected_idx: tiles[i].reset()
            selected_idx.clear()

        if self.solved1 and self.solved2:
            self._stop_timer()
            el = time.perf_counter() - self.start_t
            self.times.append(el)
            self.trial += 1
            
            self._log(f'Time: {el:.2f}s ({self.trial}/15)')
            
            self.state = 'PAUSED'
            self.btn_main.title = 'NEXT'
            self.btn_main.enabled = True


    def _log(self, msg):
        self.logs.append(msg)
        self.lbl_log.text = '\n'.join(self.logs)

    def _finish(self):
        self._stop_timer()
        global _player
        if _player: _player.stop()
        
        self.lbl_timer.text = "Finished!"
        avg = sum(self.times) / len(self.times) if self.times else 0.0
        self.lbl_feedback1.text = f'🎉 Average: {avg:.2f}s'
        self.lbl_feedback2.text = ''
        self.btn_main.hidden = True
        self._log('-- Game finished --')
        ui.delay(self.close, 3.0)

    def will_close(self):
        self._stop_timer()
        sound.stop_all_effects()

if __name__ == '__main__':
    app = NineTileApp()
    app.present('fullscreen') 