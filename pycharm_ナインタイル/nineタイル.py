import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Tkagg')


# 各ビットに対応する辺（エッジ）
edges = [
    ("マル", "クッキー"),  # bit 0
    ("マル", "サクラ"),    # bit 1
    ("マル", "ブロッコ"),  # bit 2
    ("ライム", "花々"),    # bit 3
    ("ライム", "サクラ"),  # bit 4
    ("ライム", "ブロッコ"),# bit 5
    ("クッキー", "花々"),  # bit 6
    ("クッキー", "サクラ"),# bit 7
    ("花々", "ブロッコ")   # bit 8
]

# 任意のお題カードの例（ビット表現）
# 例えば: "010101010" のような9ビット（ここでは例として適当なパターン）
pattern = "010101010"

G = nx.Graph()

# グラフの頂点を追加
G.add_nodes_from(["マル", "クッキー", "サクラ", "ライム", "花々", "ブロッコ"])

# ビットが "1" の場合のみエッジを追加
for bit, edge in zip(pattern, edges):
    if bit == "1":
        G.add_edge(*edge)

# グラフを描画
nx.draw_networkx(G, with_labels=True, node_color='lightblue', edge_color='gray')
plt.title(f"Graph Pattern: {pattern}")
plt.show()




ビット1: マル – クッキー
ビット2: マル – サクラ
ビット3: マル – ブロッコ
ビット4: ライム – 花々
ビット5: ライム – サクラ
ビット6: ライム – ブロッコ
ビット7: クッキー – 花々
ビット8: クッキー – サクラ
ビット9: 花々 – ブロッコ



【3周期ループ】
(マル, クッキー, サクラ)
000xxxxxx
1xxxxx00x
x1xx1xx1x

(ライム, 花々, ブロッコ)
xxx000xxx
xxx1xx1x0
xx1xx1xx1

【4周期ループ】
(マル, クッキー, 花々, ブロッコ)
000xxxxxx
1xxxxx00x
xxx1xx1x0
xx1xx1xx1

(マル, サクラ, ライム, ブロッコ)
000xxxxxx
x1xx1xx1x
xxx000xxx
xx1xx1xx1

(クッキー, サクラ, ライム, 花々)
1xxxxx00x
x1xx1xx1x
xxx000xxx
xxx1xx1x0

【5周期ループ】
(マル, クッキー, 花々, ライム, サクラ)
000xxxxxx
1xxxxx00x
xxx1xx1x0
xxx000xxx
x1xx1xx1x

(マル, サクラ, ライム, 花々, ブロッコ)
000xxxxxx
x1xx1xx1x
xxx000xxx
xxx1xx1x0
xx1xx1xx1

(マル, クッキー, サクラ, ライム, ブロッコ)
000xxxxxx
1xxxxx00x
x1xx1xx1x
xxx000xxx
xx1xx1xx1

(ライム, クッキー, 花々, ブロッコ, サクラ)
xxx000xxx
1xxxxx00x
xxx1xx1x0
xx1xx1xx1
x1xx1xx1x

【6周期ループ (ハミルトン閉路)】
(マル, クッキー, サクラ, ライム, 花々, ブロッコ, マル)
000xxxxxx
1xxxxx00x
x1xx1xx1x
xxx000xxx
xxx1xx1x0
xx1xx1xx1
000xxxxxx


📌 単純閉路（ループ）の周期別整理（整理した形）：

▶︎ 3周期（トライアングル）
三角形A: (マル, クッキー, サクラ)
三角形B: (ライム, 花々, ブロッコ)

▶︎ 4周期（クロスエッジを用いたループ）
(マル, クッキー, 花々, ブロッコ)
(マル, サクラ, ライム, ブロッコ)
(クッキー, サクラ, ライム, 花々)

▶︎ 5周期（1つのクロスエッジ＋2つの三角形を渡るループ）
(マル, クッキー, 花々, ライム, サクラ)
(マル, サクラ, ライム, 花々, ブロッコ)
(マル, クッキー, サクラ, ライム, ブロッコ)

▶︎ 6周期（全頂点を一周するハミルトン閉路）
(マル, クッキー, サクラ, ライム, 花々, ブロッコ, マル)



0xxxx00xx
10xxxxxx0
x11xxx1xx
xx00xxx0x
xxx10xxx1
xxxx11x1x
