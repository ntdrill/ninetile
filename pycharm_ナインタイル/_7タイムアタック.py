import time
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
# from matplotlib.widgets import Button # Buttonは今回使用しない
import matplotlib.patches as patches # マス選択用
import winsound  # Windows のビープ音・効果音用

matplotlib.use('Tkagg')
matplotlib.rcParams['font.family'] = 'MS Gothic' # 日本語フォント設定

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

# 暖色マークの定義 (ナインタイル理論より)
warm_colors = ["Maru", "Cookie", "Sakura"]
# 寒色マークの定義 (暖色以外)
all_marks = list(image_mapping.keys())
cold_colors = [m for m in all_marks if m not in warm_colors]


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
current_warm_color_count = 0 # 現在の問題の暖色マークの総数
feedback_text = None  # 正誤/タイム表示用テキスト
trial_count = 0 # 試行回数カウンター
trial_times = [] # 各試行のタイムを記録するリスト

# タイマー & 音用
start_time = time.time()
last_second = -1  # 前回ビープした秒

# --- マス選択関連 ---
selected_tiles_indices = [] # 選択されたマスのインデックス (0-8)
clickable_rects = [] # クリック判定用の透明な矩形
selection_overlays = [] # 選択状態を示す半透明の黒い矩形
tile_data = [] # 各マスの情報 (mark, key, is_warm)
judging = False # 判定中フラグ

# --- 効果音ファイルパス ---
# 絶対パスを使用。環境に合わせて変更してください。
correct_sound_path = r"D:\pythonProject7\ゲーム\ナインタイル\correct_sound.wav"
incorrect_sound_path = r"D:\pythonProject7\ゲーム\ナインタイル\incorrect_sound_soft.wav"

# 図のセットアップ
fig, ax = plt.subplots(figsize=(2.5,2.5))
ax.axis('off')
timer_text = fig.text(0.5, 0.95, "00:00:00.00", ha='center', va='center', fontsize=16)
feedback_text = fig.text(0.5, 0.90, "", ha='center', va='center', fontsize=16, color='green') # 正誤/タイム表示用

def reset_selection():
    """選択状態をリセットする"""
    global selected_tiles_indices, judging
    selected_tiles_indices.clear()
    for overlay in selection_overlays:
        overlay.set_visible(False)
    judging = False # 判定終了
    # fig.canvas.draw_idle() # 必要に応じて呼び出す

def draw_pattern():
    """新しいパターンを描画し、関連する状態をリセットする"""
    global overlay_texts, current_warm_color_count, feedback_text
    global clickable_rects, selection_overlays, tile_data
    # --- リセット処理 ---
    overlay_texts.clear()
    if feedback_text: # feedback_textがNoneでないことを確認
        feedback_text.set_text("")
    reset_selection() # 選択状態もリセット
    clickable_rects.clear()
    selection_overlays.clear()
    tile_data.clear()
    ax.clear(); ax.axis('off')
    # --------------------

    # ランダム抽出
    pattern = filtered_patterns.sample(n=1).to_numpy()[0]
    tiles = []
    warm_count = 0
    for i, bit in enumerate(pattern):
        pair = bit_mapping_romaji[i+1]
        mark = pair[bit]
        is_warm = mark in warm_colors
        if is_warm:
            warm_count += 1
        key = reverse_sorted_mapping[tuple(pair)]
        tiles.append({"mark": mark, "key": key, "is_warm": is_warm, "original_index": i}) # 元のインデックスも保持

    # 暖色マークの数を保存 (3-6の範囲のはず)
    if 3 <= warm_count <= 6:
         current_warm_color_count = warm_count
    else:
         # 想定外のケース（デバッグ用）
         print(f"警告: 暖色マーク数が想定外です ({warm_count}枚)")
         current_warm_color_count = -1 # 不正な値

    random.shuffle(tiles) # シャッフルして配置
    # 背景
    ax.imshow(np.ones((3,3)), cmap="gray", alpha=0.1, extent=(-0.5,2.5,2.5,-0.5))
    # タイル描画とクリック用要素の準備
    for r in range(3):
        for c in range(3):
            idx = r * 3 + c # グリッド上のインデックス (0-8)
            tile_info = tiles[idx]
            tile_data.append(tile_info) # マス情報を保存 (シャッフル後の順序で)

            mark, key = tile_info["mark"], tile_info["key"]
            path = image_mapping[mark]
            if path not in image_cache:
                try:
                    image_cache[path] = plt.imread(path)
                except FileNotFoundError:
                    print(f"エラー: 画像ファイルが見つかりません: {path}")
                    # 代替表示などを検討
                    image_cache[path] = np.zeros((10, 10, 4)) # ダミー画像

            img = image_cache[path]
            im = OffsetImage(img, zoom=0.05)
            ax.add_artist(AnnotationBbox(im, (c,r), frameon=False, zorder=1)) # 画像を前面に

            # キー表示 (確認モード用)
            txt = ax.text(c, r, key, fontsize=12, color='white',
                          ha='center', va='center', weight='bold',
                          visible=config['confirm_mode'], zorder=3) # テキストは最前面に
            overlay_texts.append(txt)

            # クリック用透明矩形
            rect = patches.Rectangle((c-0.5, r-0.5), 1, 1, linewidth=0, facecolor='none', picker=True, zorder=2) # クリック判定用
            rect.grid_idx = idx # グリッドインデックス情報を付与
            ax.add_patch(rect)
            clickable_rects.append(rect)

            # 選択状態オーバーレイ（最初は非表示）
            sel_overlay = patches.Rectangle((c-0.5, r-0.5), 1, 1, linewidth=0, facecolor='black', alpha=0.3, visible=False, zorder=2) # 画像の上に表示
            ax.add_patch(sel_overlay)
            selection_overlays.append(sel_overlay)

    fig.canvas.draw_idle()

def update_timer():
    """タイマー表示を更新し、ビープ音を鳴らす"""
    global last_second
    if not timer_running or judging: # タイマーが停止しているか、判定中は更新しない
        return
    elapsed = time.time() - start_time
    hrs = int(elapsed//3600)
    mins = int((elapsed%3600)//60)
    secs = int(elapsed%60)
    cs = int((elapsed - int(elapsed)) * 100)
    timer_text.set_text(f"{hrs:02d}:{mins:02d}:{secs:02d}.{cs:02d}")
    # 毎秒1回だけビープ
    cur = int(elapsed)
    if cur != last_second:
        try:
            if cur % 3 == 0:
                winsound.Beep(1000, 100)  # 3秒ごとに1000Hz
            else:
                winsound.Beep(500, 100)   # それ以外の秒は500Hz
        except Exception as e:
            print(f"ビープ音再生エラー: {e}") # winsoundが使えない環境への配慮
        last_second = cur
    # fig.canvas.draw_idle() # ここで呼ぶと重くなる可能性があるので注意

# Matplotlibタイマー設定
# intervalを少し長くして負荷軽減？ (16ms -> 50ms)
timer = fig.canvas.new_timer(interval=50)
timer.add_callback(update_timer)

def update_pattern_and_reset(event):
    """新しいパターンを描画し、タイマー開始時刻をリセット"""
    global start_time, feedback_text
    start_time = time.time() # 次の試行の開始時刻をリセット
    if feedback_text:
        feedback_text.set_text("")
    draw_pattern() # これで選択状態などもリセットされる

# ボタン関連のコードは削除
# ax_button = plt.axes([0.4, 0.01, 0.2, 0.075])
# button = Button(ax_button, "次のお題")
# button.on_clicked(on_button_click)

timer_running = False # 最初はタイマーを停止状態に

def check_answer():
    """3枚選択された時点で呼び出され、正誤判定とフィードバックを行う"""
    global feedback_text, current_warm_color_count, judging

    if len(selected_tiles_indices) != 3:
        return # 3枚選択されていない場合は何もしない

    judging = True # 判定開始

    selected_warm_count = 0
    selected_cold_count = 0
    for idx in selected_tiles_indices:
        # tile_data のインデックスは 0-8 (グリッド上の位置に対応)
        if tile_data[idx]["is_warm"]:
            selected_warm_count += 1
        else:
            selected_cold_count += 1

    # 正解条件の計算
    required_warm = 0
    required_cold = 0
    warm_total = current_warm_color_count
    if warm_total == 6: # 暖色6枚
        required_warm, required_cold = 3, 0
    elif warm_total == 5: # 暖色5枚
        required_warm, required_cold = 2, 1
    elif warm_total == 4: # 暖色4枚
        required_warm, required_cold = 1, 2
    elif warm_total == 3: # 暖色3枚
        required_warm, required_cold = 0, 3
    else: # 想定外ケース
        print(f"エラー: 正解条件の計算に失敗 (暖色数: {warm_total})")
        judging = False
        return

    is_correct = (selected_warm_count == required_warm and selected_cold_count == required_cold)

    if is_correct:
        print("正解！")
        feedback_text.set_text("正解！")
        feedback_text.set_color('green')
        sound_path = correct_sound_path
    else:
        print("不正解...")
        feedback_text.set_text("不正解...")
        feedback_text.set_color('red')
        sound_path = incorrect_sound_path

    fig.canvas.draw_idle() # フィードバック表示を更新

    # 効果音再生
    try:
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        print(f"効果音再生エラー: {e}")

    # 正誤判定後、少し待ってから選択をリセット（次のクリックを可能にするため）
    # 遅延実行用のタイマーを設定 (700ミリ秒後にリセット)
    timer_reset = fig.canvas.new_timer(interval=700, callbacks=[(reset_selection_and_redraw, [], {})])
    timer_reset.single_shot = True # 1回だけ実行
    timer_reset.start()

def reset_selection_and_redraw():
    """選択状態をリセットして再描画するコールバック関数"""
    reset_selection()
    fig.canvas.draw_idle()


def on_click(event):
    """マウスクリックイベント処理"""
    global selected_tiles_indices
    # クリック位置がax内か、ボタン上か、判定中でないかを確認
    if event.inaxes != ax or judging:
        return

    clicked_rect = None
    for rect in clickable_rects:
        contains, _ = rect.contains(event)
        if contains:
            clicked_rect = rect
            break

    if clicked_rect:
        idx = clicked_rect.grid_idx # Rectangleに格納したグリッドインデックスを取得
        if idx in selected_tiles_indices:
            # 選択解除
            selected_tiles_indices.remove(idx)
            selection_overlays[idx].set_visible(False)
        else:
            # 新規選択 (最大3つまで)
            if len(selected_tiles_indices) < 3:
                selected_tiles_indices.append(idx)
                selection_overlays[idx].set_visible(True)

        fig.canvas.draw_idle()

        # 3枚選択されたら判定
        if len(selected_tiles_indices) == 3:
            check_answer()


def on_key_press(event):
    """キーボードイベント処理"""
    print(f"Key pressed: {event.key}") # デバッグ用プリント
    global timer_running, start_time, config, trial_count, trial_times, feedback_text, judging

    if judging: return # 判定中はキー操作を無視

    if event.key == 'c':
        config['confirm_mode'] = not config['confirm_mode']
        for txt in overlay_texts:
            txt.set_visible(config['confirm_mode'])
        fig.canvas.draw_idle()
        print(f"確認モード：{'ON' if config['confirm_mode'] else 'OFF'}")

    elif event.key == ' ':
        # スペースキー: 最初の1回だけタイマーを開始
        if trial_count == 0 and not timer_running:
            print("スペースキーによりタイマースタート！")
            start_time = time.time() # 開始時刻を記録
            timer.start()
            timer_running = True
            if feedback_text: feedback_text.set_text("") # メッセージクリア
            fig.canvas.draw_idle()

    elif event.key in ['enter', 'return']:
        # Enterキー: タイマー停止 & タイム記録 & 次の問題へ
        if timer_running: # タイマー動作中のみ処理
            elapsed_at_enter = time.time() # Enterキー押下時の時刻
            timer.stop() # タイマー停止
            timer_running = False
            print("Enterキーによりタイム記録")

            trial_time = elapsed_at_enter - start_time # タイムを計算
            trial_times.append(trial_time)
            trial_count += 1

            # タイムと試行回数をフィードバック表示
            if feedback_text:
                feedback_text.set_text(f"記録: {trial_time:.2f}秒 ({trial_count}/30)")
                feedback_text.set_color('blue') # タイム記録表示は青色に
            fig.canvas.draw_idle() # 描画更新

            print(f"タイム記録: {trial_time:.2f}秒")
            print(f"試行回数: {trial_count}/30")

            # 30回に達したら終了処理
            if trial_count >= 30:
                average_time = sum(trial_times) / len(trial_times) if trial_times else 0
                print(f"\n--- 30回終了 ---")
                print(f"平均タイム: {average_time:.2f} 秒")
                plt.close(fig) # 図を閉じる
                return # イベントハンドラを抜ける
            else:
                # 30回未満なら次の問題へ
                print("次の問題へ...")
                update_pattern_and_reset(event) # 次の問題を描画 & start_time をリセット
                # タイマーは停止したまま。次のスペースキーで再開されるのを待つか、
                # あるいは即座に再開するか。元の挙動に合わせて即座に再開する。
                start_time = time.time() # 新しい問題の開始時刻
                timer.start()
                timer_running = True
                # feedback_textはupdate_pattern_and_resetでクリアされる

        # else: # タイマー停止中にEnterが押されても（最初のスペース前など）、何もしない

# イベント接続
fig.canvas.mpl_connect('key_press_event', on_key_press)
fig.canvas.mpl_connect('button_press_event', on_click) # クリックイベントを追加

# 初回描画
draw_pattern()
# timer.start() # 自動開始はしない

plt.show() 