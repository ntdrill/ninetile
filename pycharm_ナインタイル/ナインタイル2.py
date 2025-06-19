
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

_player = None

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
    def __init__(self, info: Dict, callback):
        super().__init__(frame=(0, 0, 90, 90))
        self.info = info
        self.callback = callback
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
        self.callback(self)

    def reset(self):
        self.overlay.hidden = True

    @property
    def selected(self):
        return not self.overlay.hidden
        
class NineTileApp(ui.View):
    def __init__(self):
        super().__init__(bg_color='#202124')
        self.flex = 'WH'
        self.frame = (0, 0, ui.get_screen_size()[0], ui.get_screen_size()[1])
        
        self.pattern: Optional[List[int]] = None
        self.tiles: List[Tile] = []
        self.selected_idx: List[int] = []
        self.warm_total = 0
        self.trial = 0
        self.times: List[float] = []

        self.start_t = 0.0
        self.running = False
        self._timer_active = False
        self.last_sec = -1

        self.logs: deque[str] = deque(maxlen=3)

        self._build_ui()
        self._next_pattern()

    def _build_ui(self):
        screen_w, screen_h = ui.get_screen_size()
        self.frame = (0, 0, screen_w, screen_h)
    
        tile_margin = 10
        tile_total_size = min(screen_w, screen_h - 180)
        self.TILE = (tile_total_size - tile_margin * 7.5) // 3
        
    
        gx = (screen_w - (self.TILE * 3 + tile_margin * 2)) / 2
        gy = 60
        gh = self.TILE * 3 + tile_margin * 2
        self.grid = ui.View(frame=(gx, gy, self.TILE * 3, self.TILE * 3))
        self.add_subview(self.grid)
    
        self.lbl_timer = ui.Label(frame=(0, 20, screen_w, 24), alignment=ui.ALIGN_CENTER,
                                  font=('Menlo', 16), text='00:00:00.00', text_color='white')
        self.add_subview(self.lbl_timer)
    
        self.lbl_feedback = ui.Label(frame=(0, gy + gh + 4, screen_w, 24), alignment=ui.ALIGN_CENTER,
                                     text_color='skyblue', text='Tap START →')
        self.add_subview(self.lbl_feedback)
    
        self.lbl_log = ui.Label(frame=(4, screen_h - 60, screen_w - 8, 60), font=('Menlo', 10),
                                number_of_lines=3, text_color='gray')
        self.add_subview(self.lbl_log)
    
        bw = (screen_w - 60) / 2
        by = gy + gh + 36
        self.btn_start = ui.Button(title='START', frame=(20, by, bw, 32), action=self._on_start)
        self.btn_next = ui.Button(title='NEXT', frame=(40 + bw, by, bw, 32), action=self._on_pause)
        for b in (self.btn_start, self.btn_next):
            b.bg_color = '#4A4A4A'
            b.tint_color = 'white'
            b.border_width = 0.5
            b.corner_radius = 6
        self.btn_next.enabled = False
        self.add_subview(self.btn_start)
        self.add_subview(self.btn_next)

    def _next_pattern(self):
        if self.trial >= 30:
            return self._finish()
        for v in list(self.grid.subviews):
            if hasattr(v, 'remove_from_superview'):
                v.remove_from_superview()

        self.tiles.clear()
        self.selected_idx.clear()

        self.pattern = random.choice(PATTERNS)
        infos = []
        warm_count = 0
        for i, bit in enumerate(self.pattern):
            mark = BIT_ROMAJI[i + 1][bit]
            warm = mark in WARM_MARKS
            warm_count += warm
            infos.append({'mark': mark, 'is_warm': warm, 'key': REV_KEY[tuple(BIT_ROMAJI[i + 1])]} )
        self.warm_total = warm_count
        random.shuffle(infos)

        for idx, info in enumerate(infos):
            r, c = divmod(idx, 3)
            tile = Tile(info, callback=self._on_tile)
            tile.x = c * self.TILE
            tile.y = r * self.TILE
            self.grid.add_subview(tile)
            self.tiles.append(tile)

        self._log(f'Warm={warm_count}')
        self.lbl_feedback.text = 'Tap START →'
        self.lbl_feedback.text_color = 'skyblue'
        self.btn_start.enabled = True
        self.btn_next.enabled = False

    def _on_tile(self, tile: Tile):
        idx = self.tiles.index(tile)
        if tile.selected:
            self.selected_idx.append(idx)
        else:
            self.selected_idx.remove(idx)
        if len(self.selected_idx) == 3:
            self._check_answer()

    def _tick_loop(self):
        if not self.running or not self._timer_active:
            return
        self._tick(None)
        if self._timer_active:
            ui.delay(self._tick_loop, 0.05)

    def _tick(self, sender):
        el = time.perf_counter() - self.start_t
        h, m = divmod(el, 3600)
        m, s = divmod(m, 60)
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
        ui.cancel_delays(self._tick_loop)

    def _on_start(self, sender):
        self.btn_start.enabled = False
        self.btn_next.enabled = True
        self.lbl_feedback.text = ''
        for t in self.tiles:
            t.reset()
        self.selected_idx.clear()
        self._start_timer()

    def _check_answer(self):
        self._stop_timer()
        marks = {self.tiles[i].info['mark'] for i in self.selected_idx}
        warm_sel = sum(self.tiles[i].info['is_warm'] for i in self.selected_idx)
        cold_sel = 3 - warm_sel
        conflict = any(pair.issubset(marks) for pair in CROSS_PAIRS)
        req_warm, req_cold = {6: (3, 0), 5: (2, 1), 4: (1, 2), 3: (0, 3)}.get(self.warm_total, (-1, -1))
        correct = (not conflict) and warm_sel == req_warm and cold_sel == req_cold and len(marks) == 3

        play_effect(SE_CORRECT if correct else SE_CONFLICT if conflict else SE_INCORRECT)
        el = time.perf_counter() - self.start_t
        self.times.append(el)
        self.trial += 1
        msg = '✅ Correct!' if correct else '❌ Incorrect' + (' (Conflict)' if conflict else '')
        self.lbl_feedback.text = f"{msg} | {el:.2f}s ({self.trial}/30)"
        self.lbl_feedback.text_color = '#00C853' if correct else '#FF5252'

        self.btn_start.enabled = True
        self.btn_next.enabled = False
        self.btn_start.title = 'NEXT'
        self.btn_start.action = self._on_resume

    def _on_pause(self, sender):
        if not self.running:
            return
        self._stop_timer()
        el = time.perf_counter() - self.start_t
        self.times.append(el)
        self.trial += 1
        play_effect(BEEP_SHORT)
        self.lbl_feedback.text = f'⏸ {el:.2f}s recorded – tap NEXT again →'
        self.lbl_feedback.text_color = 'orange'
        self.btn_next.action = self._on_resume

    def _on_resume(self, sender):
        self.btn_next.action = self._on_pause
        self._next_pattern()
        self._start_timer()

    def _log(self, msg):
        self.logs.append(msg)
        self.lbl_log.text = '\n'.join(self.logs)

    def _finish(self):
        self._stop_timer()
        if _player:
            _player.stop()
        avg = sum(self.times) / len(self.times) if self.times else 0.0
        self.lbl_feedback.text = f'🎉 Finished! Average: {avg:.2f}s'
        self.lbl_feedback.text_color = 'plum'
        self.btn_start.hidden = self.btn_next.hidden = True
        self._log('-- Game finished --')
        ui.delay(self.close, 2.5)
    def will_close(self):
        self._stop_timer()
        if _player:
            _player.stop()
        sound.stop_all_effects()          # 必要なら


if __name__ == '__main__':
    app = NineTileApp()
    app.present(style='sheet')
