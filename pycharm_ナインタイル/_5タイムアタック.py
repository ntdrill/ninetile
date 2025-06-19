import time
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.widgets import Button
import winsound  # Windows のビープ音用

matplotlib.use('Tkagg')

# --- CSVファイルを読み込み、データを整形 ---
file_path = "512_Patterns_of_Nine_Tile.csv"
df = pd.read_csv(file_path, header=None)
df_cleaned = df.fillna(0).astype(int)

# 9ビットマッピング（ROMaji版）
bit_mapping_romaji = {
    1: ["Maru", "Cookie"],
    2: ["Maru", "Sakura"],
    3: ["Maru", "Brocco"],
    4: ["Lime", "Hanabana"],
    5: ["Lime", "Sakura"],
    6: ["Lime", "Brocco"],
    7: ["Cookie", "Hanabana"],
    8: ["Cookie", "Sakura"],
    9: ["Hanabana", "Brocco"],
}

# ユーザー指定キー付きマッピング
sorted_bit_mapping_romaji = {
    "A": ["Maru", "Cookie"],
    "B": ["Cookie", "Sakura"],
    "C": ["Lime", "Sakura"],
    "D": ["Lime", "Hanabana"],
    "E": ["Hanabana", "Brocco"],
    "F": ["Maru", "Brocco"],
    "α": ["Cookie", "Hanabana"],
    "β": ["Maru", "Sakura"],
    "γ": ["Lime", "Brocco"],
}
reverse_sorted_mapping = {tuple(v): k for k, v in sorted_bit_mapping_romaji.items()}

# 画像ファイルパス
image_mapping = {
    "Brocco": "ブロック.png",
    "Cookie": "クッキー.png",
    "Maru": "丸.png",
    "Lime": "ライム.png",
    "Sakura": "サクラ.png",
    "Hanabana": "花火.png",
}

# 3つ揃っていないパターンを抽出
valid_pattern_indices = []
for idx, row in df_cleaned.iterrows():
    mapped = [bit_mapping_romaji[i+1][bit] for i, bit in enumerate(row)]
    unique, counts = np.unique(mapped, return_counts=True)
    if np.all(counts < 3):
        valid_pattern_indices.append(idx)
filtered_patterns = df_cleaned.loc[valid_pattern_indices]
num_valid_patterns = len(filtered_patterns)
if num_valid_patterns == 0:
    raise SystemExit("条件を満たすパターンが見つかりませんでした。")

# 設定
config = {'confirm_mode': False}
overlay_texts = []
image_cache = {}

# タイマー & 音用
start_time = time.time()
last_second = -1  # 前回ビープした秒

# 図のセットアップ
fig, ax = plt.subplots(figsize=(5,5))
ax.axis('off')
timer_text = fig.text(0.5, 0.95, "00:00:00.00", ha='center', va='center', fontsize=16)

def draw_pattern():
    global overlay_texts
    overlay_texts.clear()
    ax.clear(); ax.axis('off')
    # ランダム抽出
    pattern = filtered_patterns.sample(n=1).to_numpy()[0]
    tiles = []
    for i, bit in enumerate(pattern):
        pair = bit_mapping_romaji[i+1]
        mark = pair[bit]
        key = reverse_sorted_mapping[tuple(pair)]
        tiles.append((mark, key))
    random.shuffle(tiles)
    grid = np.array(tiles).reshape(3,3,2)
    # 背景
    ax.imshow(np.ones((3,3)), cmap="gray", alpha=0.1, extent=(-0.5,2.5,2.5,-0.5))
    # タイル描画
    for r in range(3):
        for c in range(3):
            mark, key = grid[r,c]
            path = image_mapping[mark]
            if path not in image_cache:
                image_cache[path] = plt.imread(path)
            img = image_cache[path]
            im = OffsetImage(img, zoom=0.1)
            ax.add_artist(AnnotationBbox(im, (c,r), frameon=False))
            txt = ax.text(c, r, key, fontsize=12, color='white',
                          ha='center', va='center', weight='bold',
                          visible=config['confirm_mode'])
            overlay_texts.append(txt)
    ax.set_title("お題", fontsize=16)
    fig.canvas.draw_idle()

def update_timer():
    global last_second
    elapsed = time.time() - start_time
    hrs = int(elapsed//3600)
    mins = int((elapsed%3600)//60)
    secs = int(elapsed%60)
    cs = int((elapsed - int(elapsed)) * 100)
    timer_text.set_text(f"{hrs:02d}:{mins:02d}:{secs:02d}.{cs:02d}")
    # 毎秒1回だけビープ
    cur = int(elapsed)
    if cur != last_second:
        if cur % 3 == 0:
            winsound.Beep(1000, 100)  # 3秒ごとに1000Hz
        else:
            winsound.Beep(500, 100)   # それ以外の秒は500Hz
        last_second = cur
    fig.canvas.draw_idle()

# Matplotlibタイマー設定
timer = fig.canvas.new_timer(interval=16)
timer.add_callback(update_timer)
timer.start()

def update_pattern_and_reset(event):
    global start_time
    start_time = time.time()
    draw_pattern()

def on_button_click(event):
    global timer_running
    update_pattern_and_reset(event)
    if not timer_running:
        timer.start(); timer_running = True

ax_button = plt.axes([0.4, 0.01, 0.2, 0.075])
button = Button(ax_button, "次のお題")
button.on_clicked(on_button_click)

timer_running = True
def on_key_press(event):
    global timer_running, start_time
    if event.key == 'c':
        config['confirm_mode'] = not config['confirm_mode']
        for txt in overlay_texts:
            txt.set_visible(config['confirm_mode'])
        fig.canvas.draw_idle()
        print(f"確認モード：{'ON' if config['confirm_mode'] else 'OFF'}")
    elif event.key in ['enter', 'return']:
        if timer_running:
            timer.stop(); timer_running = False
            print("タイマー停止")
        else:
            update_pattern_and_reset(event)
            timer.start(); timer_running = True
            print("次のお題＆タイマー再開")

fig.canvas.mpl_connect('key_press_event', on_key_press)

# 初回描画
draw_pattern()

plt.show()
