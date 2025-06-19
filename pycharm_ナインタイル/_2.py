import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Tkagg')


# ファイルを読み込む
file_path = "512_Patterns_of_Nine_Tile.csv"
df = pd.read_csv(file_path, header=None)

# データを数値型に変換し、NaNを0に置換
df_cleaned = df.fillna(0).astype(int)

# 9ビットのマッピング（0:左側、1:右側）
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

# 色のマッピング
color_mapping = {
    "Maru": "orange",
    "Lime": "yellowgreen",
    "Sakura": "pink",
    "Hanabana": "blue",
    "Cookie": "yellow",
    "Brocco": "brown",
}

# 頭文字表記
first_letter_mapping = {
    "Maru": "M",
    "Lime": "L",
    "Sakura": "S",
    "Hanabana": "H",
    "Cookie": "C",
    "Brocco": "B",
}

# 3つ揃っていないパターンを正しく抽出
valid_pattern_indices = []

for index, pattern in df_cleaned.iterrows():
    mapped_patterns = [bit_mapping_romaji[idx + 1][bit] for idx, bit in enumerate(pattern)]
    unique, counts = np.unique(mapped_patterns, return_counts=True)

    # どの柄も3つ以上含まないパターンを選択
    if np.all(counts < 3):
        valid_pattern_indices.append(index)

# フィルタリング後のデータセット
filtered_patterns = df_cleaned.loc[valid_pattern_indices]

# フィルタリング後のパターン数を確認
num_valid_patterns = len(filtered_patterns)

# 生成するパターン数
num_samples = min(5, num_valid_patterns)

if num_valid_patterns > 0:
    # 条件を満たすパターンからランダムに選択
    selected_patterns = filtered_patterns.sample(n=num_samples, random_state=None).to_numpy()

    # 3x3のグリッドとして表示（頭文字 & 大きめのフォント）
    fig, axes = plt.subplots(1, num_samples, figsize=(15, 5))

    for i, pattern in enumerate(selected_patterns):
        grid = np.array(pattern).reshape(3, 3)

        # 各タイルのマークを取得し、ランダムにシャッフル
        shuffled_texts = [
            bit_mapping_romaji[idx + 1][bit] for idx, bit in enumerate(pattern)
        ]
        random.shuffle(shuffled_texts)

        # 頭文字に変換
        text_grid = np.array([first_letter_mapping[text] for text in shuffled_texts]).reshape(3, 3)

        ax = axes[i]
        ax.imshow(np.ones((3, 3)), cmap="gray", alpha=0.1)  # 背景

        # 各セルにマークを表示（頭文字＋色＋大きいフォント）
        for row in range(3):
            for col in range(3):
                text = text_grid[row, col]
                color = color_mapping.get(shuffled_texts[row * 3 + col], "black")
                ax.text(col, row, text, ha='center', va='center', fontsize=24, fontweight="bold", color=color)

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"Pattern {i+1}", fontsize=14)

    plt.tight_layout()
    plt.show()
else:
    print("条件を満たすパターンが見つかりませんでした。")
