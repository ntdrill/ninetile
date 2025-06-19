import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

matplotlib.use('Tkagg')

# ファイルを読み込む
file_path = "512_Patterns_of_Nine_Tile.csv"
df = pd.read_csv(file_path, header=None)

# データを数値型に変換し、NaNを0に置換
df_cleaned = df.fillna(0).astype(int)

# 元の9ビットのマッピング（0:左側、1:右側）
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

# ユーザー指定のキー付きマッピング（確認用）
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
# 逆引き辞書：各組み合わせに対応するキーを取得
reverse_sorted_mapping = {tuple(v): k for k, v in sorted_bit_mapping_romaji.items()}

# 画像ファイルのパスリスト
image_files = [
    "ブロック.png",  # ブロック (Brocco)
    "クッキー.png",  # クッキー (Cookie)
    "丸.png",  # マル (Maru)
    "ライム.png",  # ライム (Lime)
    "サクラ.png",  # 桜 (Sakura)
    "花火.png"   # 花火 (Hanabana)
]

# マークと画像パスの対応辞書
image_mapping = {
    "Brocco": image_files[0],
    "Cookie": image_files[1],
    "Maru": image_files[2],
    "Lime": image_files[3],
    "Sakura": image_files[4],
    "Hanabana": image_files[5],
}

# 3つ揃っていないパターンを正しく抽出
valid_pattern_indices = []
for index, pattern in df_cleaned.iterrows():
    mapped_patterns = [bit_mapping_romaji[idx + 1][bit] for idx, bit in enumerate(pattern)]
    unique, counts = np.unique(mapped_patterns, return_counts=True)
    if np.all(counts < 3):
        valid_pattern_indices.append(index)

# フィルタリング後のデータセット
filtered_patterns = df_cleaned.loc[valid_pattern_indices]
num_valid_patterns = len(filtered_patterns)

# 生成するパターン数（最大5件）
num_samples = min(5, num_valid_patterns)

# 初期の確認モード設定（Trueならキーを表示）
config = {'confirm_mode': False}

# キーのテキストオーバーレイオブジェクトを保持するリスト
overlay_texts = []

if num_valid_patterns > 0:
    # 条件を満たすパターンからランダムに選択
    selected_patterns = filtered_patterns.sample(n=num_samples, random_state=None).to_numpy()

    fig, axes = plt.subplots(1, num_samples, figsize=(15, 5))
    # 画像の再読み込みを避けるためのキャッシュ
    image_cache = {}

    # axes が 1 つの場合もリストとして扱う
    if num_samples == 1:
        axes = [axes]

    for i, pattern in enumerate(selected_patterns):
        tile_data = []
        for idx, bit in enumerate(pattern):
            pair = bit_mapping_romaji[idx + 1]   # 例: ["Maru", "Cookie"]
            mark = pair[bit]                     # 選ばれたマーク
            letter = reverse_sorted_mapping[tuple(pair)]  # 対応するキー（例："A"）
            tile_data.append((mark, letter))
        # 各タイルの順番をランダムにシャッフル
        random.shuffle(tile_data)
        grid_data = np.array(tile_data).reshape(3, 3, 2)

        ax = axes[i]
        ax.imshow(np.ones((3, 3)), cmap="gray", alpha=0.1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"Pattern {i + 1}", fontsize=14)

        for row in range(3):
            for col in range(3):
                mark = grid_data[row, col, 0]
                letter = grid_data[row, col, 1]
                image_path = image_mapping[mark]
                if image_path in image_cache:
                    img = image_cache[image_path]
                else:
                    img = plt.imread(image_path)
                    image_cache[image_path] = img
                im = OffsetImage(img, zoom=0.07)
                ab = AnnotationBbox(im, (col, row), frameon=False)
                ax.add_artist(ab)
                # キーのテキストオーバーレイを追加（初期状態は config['confirm_mode'] に従う）
                text_obj = ax.text(col, row, letter, fontsize=12, color='white',
                                   ha='center', va='center', weight='bold', visible=config['confirm_mode'])
                overlay_texts.append(text_obj)

    plt.tight_layout()

    # キープレスイベントで確認モードを切り替える関数
    def on_key_press(event):
        if event.key == 'c':  # 'c' キーで切り替え
            config['confirm_mode'] = not config['confirm_mode']
            for txt in overlay_texts:
                txt.set_visible(config['confirm_mode'])
            fig.canvas.draw_idle()
            mode_status = "ON" if config['confirm_mode'] else "OFF"
            print(f"確認モードが切り替わりました: {mode_status}")

    # イベントハンドラを接続
    fig.canvas.mpl_connect('key_press_event', on_key_press)
    print("実行中に 'c' キーを押すと確認モードが切り替わります。")
    plt.show()
else:
    print("条件を満たすパターンが見つかりませんでした。")
