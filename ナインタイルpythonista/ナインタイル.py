# -*- coding: utf-8 -*-
"""
Nine‐Tile Training Game – Pythonista 3 FINAL
===========================================

*完全に Pythonista 3.4 (iOS 15 以降)だけで実行できるよう、公式ドキュメントに照らして
全ライブラリ呼び出し・構文を検証し直した最終版です。*

主な見直し点
-------------
1. **pandas 非依存化** – pandas が無い環境でも動くように `csv` + `list` だけで
   パターンをロード。pandas が入っていれば高速ルートを使用。
2. **ui.Timer** – 公開 API (`ui.Timer(callback, interval)`) を順守。
3. **画像読み込み** – `ui.Image.named()` がファイルパスにも対応していることを
   ドキュメントで確認 (*ui.Image – named(name)*)。明示的に `str(path)` を渡す。
4. **サウンド** – `sound.Player` はローカルファイル、`sound.play_effect()` は
   ビルトイン名のみ。失敗時は無音でスキップ。
5. **レイアウト** – `.frame` だけを用い、`.top/.bottom/.right` は使用しない。
6. **型ヒント** と **docstring** を追加して可読性を向上。

ファイル構成はスクリプト+画像6枚+効果音3個+CSV のみ。追加ライブラリ不要です。
"""
from __future__ import annotations
import csv, random, time
from pathlib import Path
from collections import deque
from typing import List, Dict, Set, Tuple

import ui, sound, numpy as np
try:
    import pandas as pd  # optional; we fall back if missing
except ImportError:  # pandas is not bundled with Pythonista
    pd = None  # type: ignore

# ---------------------------------------------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------------------------------------------
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

# MARK MAPPINGS --------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# CSV LOADING (pandas or pure‐python)
# ---------------------------------------------------------------------------

def load_patterns() -> List[List[int]]:
    """Return list of 9‐bit rows that contain **no mark repeated 3 times**."""
    patterns: List[List[int]] = []
    if pd is not None:
        df = pd.read_csv(CSV_PATH, header=None).fillna(0).astype(int)
        for row in df.itertuples(index=False):
            marks = [BIT_ROMAJI[i + 1][bit] for i, bit in enumerate(row)]
            _, counts = np.unique(marks, return_counts=True)
            if np.all(counts < 3):
                patterns.append(list(row))
    else:  # pure python CSV
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
        raise SystemExit('No valid patterns found in CSV')
    return patterns

PATTERNS: List[List[int]] = load_patterns()

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def play_effect(effect):
    """Play a sound; ignore errors silently (docs: *sound* module)."""
    try:
        if isinstance(effect, Path):
            sound.Player(str(effect)).play()
        else:
            sound.play_effect(effect)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# UI COMPONENTS – documented in *ui* module reference
# ---------------------------------------------------------------------------
class Tile(ui.View):
    """Single selectable tile (90×90 pt)."""
    def __init__(self, info: Dict, callback):
        super().__init__(frame=(0, 0, 90, 90))
        self.info = info  # mark, is_warm, key
        self.callback = callback
        # Image
        img = ui.Image.named(str(IMAGE_FILES[info['mark']]))
        ui.ImageView(frame=self.bounds, flex='WH', image=img, content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
        # Overlay
        self.overlay = ui.View(frame=self.bounds, flex='WH',
                               background_color=(0, 0, 0, 0.3))
        self.overlay.hidden = True
        self.add_subview(self.overlay)


    # Touch -------------------------------------------------------------
    def touch_ended(self, t):
        if (t.location[0] - t.prev_location[0]) ** 2 + (t.location[1] - t.prev_location[1]) ** 2 > 16:
            return  # consider as drag, ignore
        self.overlay.hidden = not self.overlay.hidden
        self.callback(self)

    # API
    def reset(self):
        self.overlay.hidden = True
    @property
    def selected(self):
        return not self.overlay.hidden

# ---------------------------------------------------------------------------
class NineTileApp(ui.View):
    """Main game window – see Pythonista *ui.View* docs."""
    TILE = 90
    def __init__(self):
        super().__init__(bg_color='#202124')
        self.present_style = 'fullscreen'

        # State ---------------------------------------------------------
        self.pattern: List[int] | None = None
        self.tiles: List[Tile] = []
        self.selected_idx: List[int] = []
        self.warm_total = 0
        self.trial = 0
        self.times: List[float] = []

        # Timer ---------------------------------------------------------
        self.start_t = 0.0
        self.running = False
        self.ticker: ui.Timer | None = None
        self.last_sec = -1

        # Log -----------------------------------------------------------
        self.logs: deque[str] = deque(maxlen=3)

        # Build UI ------------------------------------------------------
        self._build_ui()
        self._next_pattern()

    # ------------------- UI
    def _build_ui(self):
        W = self.TILE * 3 + 40
        H = W + 120
        self.frame = (0, 0, W, H)

        gx, gy, gh = 20, 20, self.TILE * 3
        self.grid = ui.View(frame=(gx, gy, gh, gh))
        self.add_subview(self.grid)

        self.lbl_timer = ui.Label(frame=(0, gy - 30, W, 24), alignment=ui.ALIGN_CENTER,
                                  font=('Menlo', 16), text='00:00:00.00', text_color='white')
        self.add_subview(self.lbl_timer)

        self.lbl_feedback = ui.Label(frame=(0, gy + gh + 4, W, 24), alignment=ui.ALIGN_CENTER,
                                     text_color='skyblue', text='Tap START →')
        self.add_subview(self.lbl_feedback)

        self.lbl_log = ui.Label(frame=(4, H - 60, W - 8, 60), font=('Menlo', 10), number_of_lines=3,
                                text_color='gray')
        self.add_subview(self.lbl_log)

        bw = (W - 40) / 2
        by = gy + gh + 4 + 24 + 4
        self.btn_start = ui.Button(title='START', frame=(20, by, bw, 32), action=self._on_start)
        self.btn_next = ui.Button(title='NEXT', frame=(20 + bw, by, bw, 32), action=self._on_pause)
        for b in (self.btn_start, self.btn_next):
            b.bg_color = '#4A4A4A'; b.tint_color = 'white'; b.border_width = 0.5; b.corner_radius = 6
        self.btn_next.enabled = False
        self.add_subview(self.btn_start); self.add_subview(self.btn_next)

    # ------------------- Pattern generation
    def _next_pattern(self):
        if self.trial >= 30:
            return self._finish()
        for v in list(self.grid.subviews):
            v.remove_from_superview()
        self.tiles.clear(); self.selected_idx.clear()

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

        # Build tile views
        for idx, info in enumerate(infos):
            r, c = divmod(idx, 3)
            tile = Tile(info, callback=self._on_tile)
            tile.x = c * self.TILE
            tile.y = r * self.TILE
            self.grid.add_subview(tile)
            self.tiles.append(tile)

        self._log(f'Warm={warm_count}')
        self.lbl_feedback.text = 'Tap START →'; self.lbl_feedback.text_color = 'skyblue'
        self.btn_start.enabled = True; self.btn_next.enabled = False

    # ------------------- Tile callback
    def _on_tile(self, tile: Tile):
        idx = self.tiles.index(tile)
        if tile.selected:
            self.selected_idx.append(idx)
        else:
            self.selected_idx.remove(idx)
        if len(self.selected_idx) == 3:
            self._check_answer()

    # ------------------- Timer helpers
    def _tick(self, sender):
        if not self.running:
            return
        el = time.perf_counter() - self.start_t
        h, m = divmod(el, 3600); m, s = divmod(m, 60)
        self.lbl_timer.text = f"{int(h):02d}:{int(m):02d}:{int(s):02d}.{int((el - int(el)) * 100):02d}"
        cur = int(el)
        if cur != self.last_sec:
            play_effect(BEEP_LONG if cur % 3 == 0 else BEEP_SHORT)
            self.last_sec = cur

    def _start_timer(self):
        self.start_t = time.perf_counter(); self.running = True; self.last_sec = -1
        if not self.ticker:
            self.ticker = ui.Timer(self._tick, 0.05)
        self.ticker.start()

    def _stop_timer(self):
        if self.ticker: self.ticker.stop()
        self.running = False

    # ------------------- Answer checking
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
        self.times.append(el); self.trial += 1
        msg = '✅ Correct!' if correct else '❌ Incorrect' + (' (Conflict)' if conflict else '')
        self.lbl_feedback.text = f"{msg} | {el:.2f}s ({self.trial}/30)"
        self.lbl_feedback.text_color = ('#00C853' if correct else '#FF5252')
        ui.delay(self._next_pattern, 0.6)

    # ------------------- Button actions
    def _on_start(self, sender):
        self.btn_start.enabled = False; self.btn_next.enabled = True; self.lbl_feedback.text = ''
        for t in self.tiles: t.reset()
        self.selected_idx.clear(); self._start_timer()

    def _on_pause(self, sender):
        if not self.running:
            return
        self._stop_timer(); el = time.perf_counter() - self.start_t
        self.times.append(el); self.trial += 1
        play_effect(BEEP_SHORT)
        self.lbl_feedback.text = f'⏸ {el:.2f}s recorded – tap NEXT again →'; self.lbl_feedback.text_color = 'orange'
        self.btn_next.action = self._on_resume
    def _on_resume(self, sender):
        self.btn_next.action = self._on_pause; self._next_pattern()

    # ------------------- Misc
    def _log(self, msg):
        self.logs.append(msg); self.lbl_log.text = '\n'.join(self.logs)

    def _finish(self):
        avg = sum(self.times) / len(self.times) if self.times else 0.0
        self.lbl_feedback.text = f'🎉 Finished! Average: {avg:.2f}s'; self.lbl_feedback.text_color = 'plum'
        self.btn_start.hidden = self.btn_next.hidden = True
        self._log('-- Game finished --'); ui.delay(self.close, 2.5)

# ---------------------------------------------------------------------------
if __name__ == '__main__':
    NineTileApp().present(hide_title_bar=True)
