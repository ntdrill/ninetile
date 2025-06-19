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
from collections import deque # ログ表示用にdequeを追加

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

# クロスエッジペア (コンフリクト判定用)
cross_edge_pairs = [
    {"Maru", "Brocco"}, # キー F
    {"Lime", "Sakura"}, # キー C
    {"Cookie", "Hanabana"} # キー α
]

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

# --- ログ表示関連 ---
MAX_LOG_LINES = 3 # ログ表示の最大行数
game_log = deque(maxlen=MAX_LOG_LINES)
log_display = None # ログ表示用テキストオブジェクト

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
incorrect_alt_sound_path = r"D:\pythonProject7\ゲーム\ナインタイル\incorrect_sound_alt.wav" # コンフリクト用効果音

# 図のセットアップ
fig, ax = plt.subplots(figsize=(2.5,2.5))
ax.axis('off')
timer_text = fig.text(0.5, 0.95, "00:00:00.00", ha='center', va='center', fontsize=16)
feedback_text = fig.text(0.5, 0.90, "", ha='center', va='center', fontsize=16, color='green') # 正誤/タイム表示用
log_display = fig.text(0.05, 0.01, "", ha='left', va='bottom', fontsize=8, color='gray') # ログ表示エリア

def update_log_display():
    """ゲームログ表示を更新する"""
    if log_display:
        log_text = "\n".join(game_log)
        log_display.set_text(log_text)
        fig.canvas.draw_idle()

def add_log_message(message):
    """ログにメッセージを追加し、表示を更新する"""
    game_log.append(message)
    update_log_display()

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
         add_log_message(f"警告: 暖色マーク数 {warm_count}") # ログに追加
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
                    add_log_message(f"エラー: 画像なし {path}") # ログに追加
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

    # --- ★★★ お題の内容を標準出力 ★★★ ---
    print("--- 新しいお題 ---")
    grid_marks = [tile_data[i*3 + j]["mark"] for i in range(3) for j in range(3)]
    for i in range(3):
        print(f"[{grid_marks[i*3]:<8} {grid_marks[i*3+1]:<8} {grid_marks[i*3+2]:<8}]")
    print(f"暖色: {current_warm_color_count}枚") # 暖色の総数も表示
    print("---------------")
    # -------------------------------------

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
            add_log_message(f"ビープ音再生エラー: {e}") # ログに追加
        last_second = cur
    fig.canvas.draw_idle() # ここで呼ぶと重くなる可能性があるので注意 -> 描画更新のためにコメント解除

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

    selected_marks = set()
    selected_warm_count = 0
    selected_cold_count = 0
    for idx in selected_tiles_indices:
        tile_info = tile_data[idx]
        selected_marks.add(tile_info["mark"])
        if tile_info["is_warm"]:
            selected_warm_count += 1
        else:
            selected_cold_count += 1

    # ★★★ 選択されたカードのマークを標準出力に追加 ★★★
    print(f"選択されたカード: {selected_marks}")
    # ---------------------------------------------

    # --- コンフリクト判定 (クロスエッジペア) ---
    is_conflict = False
    for pair in cross_edge_pairs:
        if pair.issubset(selected_marks):
            is_conflict = True
            print(f"コンフリクト検出: {pair}")
            add_log_message(f"競合検出: {pair}") # ログに追加
            break
    # --------------------------------------

    # --- 正解条件の計算 (暖色/寒色) ---
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
        # コンフリクトがなくてもエラー時は次に進ませない方が良いか？
        # ここではひとまず進めるが、エラー表示はしたい
        add_log_message(f"計算エラー({warm_total})") # ログに追加
        feedback_text.set_text(f"計算エラー({warm_total})")
        feedback_text.set_color('orange')
        is_correct = False # エラー時は不正解扱いとする
        # judging = False # 判定は終了とする
        # return # ここで return すると proceed_to_next_pattern が呼ばれない
        # エラーでも proceed_to_next_pattern は呼ばれるようにする

    # 最終的な正誤判定
    # コンフリクトがなく、かつ暖色/寒色の組み合わせが正しい場合のみ正解
    # ★★★ さらに、選択されたマークの種類が3種類であることも条件に追加 ★★★
    is_correct_final = not is_conflict and \
                       (selected_warm_count == required_warm and selected_cold_count == required_cold) and \
                       len(selected_marks) == 3 # ★★★ 追加 ★★★

    if is_conflict:
        print("不正解 (コンフリクト)...")
        add_log_message(f"競合 {pair}")
        feedback_text.set_text(f"不正解(競合) {pair}") # コンフリクト時のメッセージ
        feedback_text.set_color('red')
        sound_path = incorrect_alt_sound_path # コンフリクト時は別の効果音
    elif is_correct_final:
        print("正解！")
        add_log_message("正解！")
        feedback_text.set_text("正解！")
        feedback_text.set_color('green')
        sound_path = correct_sound_path
    else: # コンフリクトなし、でも暖色/寒色が違う場合
        print("不正解...")
        add_log_message("不正解")
        feedback_text.set_text("不正解") # 通常の不正解メッセージ
        feedback_text.set_color('red')
        sound_path = incorrect_sound_path # 通常の不正解効果音

    # エラーケースで is_correct_final が False になる場合もあるが、
    # その場合は上の else ブロックで処理される (不正解表示)
    # エラー表示は上書きされる可能性があるが、ひとまず許容する

    fig.canvas.draw_idle() # フィードバック表示を更新

    # 効果音再生
    try:
        # 効果音再生を同期的にするか、少しだけ待つか検討。
        # 非同期(ASYNC)だと音が鳴り終わる前に次に進む可能性が高い。
        # 同期的(SND_SYNC)だと音が終わるまでブロックされる。
        # ここでは非同期のまま、直後に移行。
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        print(f"効果音再生エラー: {e}")
        add_log_message(f"効果音再生エラー: {e}") # ログに追加

    # 正誤判定後、すぐに次の問題へ移行
    proceed_to_next_pattern()

def proceed_to_next_pattern():
    """タイム記録（タイマー作動中の場合）と次のパターンへの移行処理"""
    global timer_running, start_time, trial_count, trial_times, feedback_text, judging

    was_timer_running = timer_running # 移行処理前のタイマー状態を保持

    if was_timer_running:
        elapsed_at_proceed = time.time() # 移行時の時刻
        timer.stop()
        timer_running = False
        print("自動進行によりタイム記録")
        # add_log_message("タイム記録") # proceed_to_next_pattern で記録される

        trial_time = elapsed_at_proceed - start_time # タイムを計算
        trial_times.append(trial_time)
        trial_count += 1

        # タイムと試行回数をフィードバック表示 (一時的)
        time_feedback_msg = f"記録: {trial_time:.2f}秒 ({trial_count}/30)"
        if feedback_text:
            feedback_text.set_text(time_feedback_msg)
            feedback_text.set_color('blue') # タイム記録表示は青色に
        add_log_message(time_feedback_msg) # ログにも記録
        # fig.canvas.draw_idle() # update_log_display内で呼ばれる

        print(f"タイム記録: {trial_time:.2f}秒")
        print(f"試行回数: {trial_count}/30")

        # 30回に達したら終了処理
        if trial_count >= 30:
            average_time = sum(trial_times) / len(trial_times) if trial_times else 0
            print(f"\n--- 30回終了 ---")
            add_log_message("--- 30回終了 ---")
            print(f"平均タイム: {average_time:.2f} 秒")
            add_log_message(f"平均: {average_time:.2f} 秒")
            # 少し待ってからウィンドウを閉じる（最後のフィードバックが見えるように）
            timer_close = fig.canvas.new_timer(interval=1500, callbacks=[(plt.close, [fig], {})])
            timer_close.single_shot = True
            timer_close.start()
            return # 移行処理を終了

    # --- 30回未満、またはタイマーが作動していなかった場合 --- 
    # 次の問題へ (update_pattern_and_reset内で judging=False になる)
    print("次の問題へ...")
    add_log_message("次の問題へ...")
    update_pattern_and_reset(None) # 次の問題を描画

    # もし移行前にタイマーが作動していたなら、新しい問題のためにタイマーを再開
    if was_timer_running and trial_count < 30: # 30回到達チェックを再度行う
        start_time = time.time() # 新しい問題の開始時刻
        timer.start()
        timer_running = True
        # feedback_text は update_pattern_and_reset でクリアされる
    # else: タイマーが作動していなかった場合、停止したまま


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
    # print(f"Key pressed: {event.key}") # デバッグ用プリント -> ログが冗長になるためコメントアウト推奨
    # add_log_message(f"キー: {event.key}") # 必要ならコメント解除
    global timer_running, start_time, config, trial_count, trial_times, feedback_text, judging

    if judging: return # 判定中はキー操作を無視

    if event.key == 'c':
        config['confirm_mode'] = not config['confirm_mode']
        for txt in overlay_texts:
            txt.set_visible(config['confirm_mode'])
        # fig.canvas.draw_idle() # update_log_display内で呼ばれる
        mode_msg = f"確認モード: {'ON' if config['confirm_mode'] else 'OFF'}"
        print(f"確認モード：{'ON' if config['confirm_mode'] else 'OFF'}")
        add_log_message(mode_msg)

    elif event.key == ' ':
        # スペースキー: 最初の1回だけタイマーを開始
        if trial_count == 0 and not timer_running:
            print("スペースキーによりタイマースタート！")
            add_log_message("タイマースタート!")
            start_time = time.time() # 開始時刻を記録
            timer.start()
            timer_running = True
            if feedback_text: feedback_text.set_text("") # メッセージクリア
            fig.canvas.draw_idle() # ログ以外も更新するので呼ぶ

    elif event.key in ['enter', 'return']:
        # Enterキー: タイマー停止 & タイム記録 & 次の問題へ (手動操作用)
        # 自動進行があるため、基本的には不要だが、タイマー作動中に手動で進めたい場合のために残す
        if timer_running: # タイマー動作中のみ処理
            proceed_to_next_pattern() # 移行処理を直接呼び出す
        # else: # タイマー停止中にEnterが押されても何もしない

# イベント接続
fig.canvas.mpl_connect('key_press_event', on_key_press)
fig.canvas.mpl_connect('button_press_event', on_click) # クリックイベントを追加

# 初回描画
draw_pattern()
add_log_message("ゲーム開始") # 初期メッセージ
# timer.start() # 自動開始はしない

plt.show() 