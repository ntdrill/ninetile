import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image, ImageTk, ImageDraw, ImageColor

# 画像ファイルのパス（環境に合わせて調整してください）
image_paths = {
    "クッキー": "72E9D2DD-601D-4957-888C-96F5154F751E_enhanced.png",
    "サクラ": "F0D33901-6A6F-42B3-ACC8-9D33606B2DE1_enhanced.png",
    "ライム": "D33BA323-0F6B-471D-8BE0-B270826361B0_enhanced.png",
    "花火": "22291B2F-363C-4336-A63B-98FA2A4EB481_enhanced.png",
    "ブロック": "1239A389-4458-4F42-AA7B-DBA449C517D7_enhanced.png",
    "丸": "B18578DF-AD1D-4405-B261-6A5F53A232C6_enhanced.png",
}

# マークごとの正解リスト（正解数3つ）
answer_map = {
    "クッキー": ["花火", "丸", "サクラ"],
    "サクラ": ["クッキー", "丸", "ライム"],
    "ライム": ["サクラ", "ブロック", "花火"],
    "花火": ["ライム", "クッキー", "ブロック"],
    "ブロック": ["花火", "ライム", "丸"],
    "丸": ["ブロック", "サクラ", "クッキー"],
}

# 確認モード時の各マーク用の色指定
confirmation_colors = {
    "クッキー": "yellow",
    "サクラ": "pink",
    "ライム": "lime",
    "花火": "blue",
    "ブロック": "brown",
    "丸": "orange",
}

# 上側に表示する6つのマーク
all_marks = list(image_paths.keys())

# PIL画像を読み込む関数
def load_pil_image(filename):
    path = f"{filename}"
    try:
        img = Image.open(path)
        img = img.resize((100, 100), Image.Resampling.LANCZOS)
    except Exception as e:
        messagebox.showerror("Image Load Error", f"画像 {path} の読み込みに失敗しました:\n{e}")
        img = Image.new("RGB", (100, 100), color="gray")
    return img

class MarkMatchingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("マークマッチングゲーム")
        # PIL画像とPhotoImageを作成
        self.pil_images = {mark: load_pil_image(image_paths[mark]) for mark in all_marks}
        self.images = {mark: ImageTk.PhotoImage(self.pil_images[mark]) for mark in all_marks}
        # 確認モード用のオーバーレイ画像（指定色）と黒オーバーレイ画像を作成
        self.overlay_images = {}
        self.black_overlay_images = {}
        for mark in all_marks:
            self.overlay_images[mark] = ImageTk.PhotoImage(self.create_overlay(self.pil_images[mark], confirmation_colors[mark]))
            self.black_overlay_images[mark] = ImageTk.PhotoImage(self.create_overlay(self.pil_images[mark], "black"))

        # 上部のボタン配置用フレーム
        self.frame_top = tk.Frame(root)
        self.frame_top.grid(row=0, column=0, padx=10, pady=10)

        # 下部の表示エリア用フレーム
        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.grid(row=1, column=0, padx=10, pady=10)

        # 各マークのボタンを作成
        self.mark_buttons = {}
        for idx, mark in enumerate(all_marks):
            btn = tk.Button(self.frame_top, image=self.images[mark],
                            command=lambda m=mark: self.select_mark(m),
                            bd=2, relief=tk.RAISED)
            btn.grid(row=0, column=idx, padx=5)
            self.mark_buttons[mark] = btn

        # 下部の指示ラベルと表示画像（正解数3つに変更）
        self.instruction_label = tk.Label(self.frame_bottom, text="下のマークに対応する3つをクリックしてください", font=("Arial", 14))
        self.instruction_label.pack(pady=(0, 10))
        self.bottom_label = tk.Label(self.frame_bottom)
        self.bottom_label.pack()

        # 確認モード用チェックボタン
        self.confirmation_var = tk.IntVar()
        self.confirmation_check = tk.Checkbutton(self.frame_bottom, text="確認モード", variable=self.confirmation_var,
                                                 command=self.update_button_images)
        self.confirmation_check.pack(pady=(10, 0))

        # リフレッシュボタン
        self.refresh_button = tk.Button(self.frame_bottom, text="リフレッシュ", command=self.new_game)
        self.refresh_button.pack(pady=(10, 0))

        self.new_game()

    def create_overlay(self, pil_img, color, alpha=128):
        # PIL画像をRGBAに変換
        img = pil_img.convert("RGBA")
        # 透明なオーバーレイ画像を作成
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        # 色文字列からRGBA値を取得し、半透明にする
        base_color = ImageColor.getcolor(color, "RGBA")
        half_transparent_color = base_color[:3] + (alpha,)
        # 画像全体に矩形を描画
        draw = ImageDraw.Draw(overlay)
        draw.rectangle([0, 0, img.size[0], img.size[1]], fill=half_transparent_color)
        # 元画像とオーバーレイを合成
        combined = Image.alpha_composite(img, overlay)
        return combined

    def new_game(self):
        self.selected = []
        for mark, btn in self.mark_buttons.items():
            btn.config(image=self.images[mark], bd=2, relief=tk.RAISED)
        self.bottom_mark = random.choice(all_marks)
        print("出題マーク:", self.bottom_mark)
        self.correct_answers = answer_map[self.bottom_mark]
        self.bottom_label.config(image=self.images[self.bottom_mark])
        self.update_button_images()

    def select_mark(self, mark):
        btn = self.mark_buttons[mark]
        if mark in self.selected:
            self.selected.remove(mark)
            btn.config(relief=tk.RAISED)
        elif len(self.selected) < 3:
            self.selected.append(mark)
            btn.config(relief=tk.SUNKEN)
        self.update_button_images()
        if len(self.selected) == 3:
            self.root.after(200, self.check_answer)

    def update_button_images(self):
        # 確認モード中なら、正解の柄は指定色の半透明、他は黒の半透明画像に切り替え
        for mark, btn in self.mark_buttons.items():
            if self.confirmation_var.get() == 1:
                if mark in self.correct_answers:
                    btn.config(image=self.overlay_images[mark])
                else:
                    btn.config(image=self.black_overlay_images[mark])
            else:
                btn.config(image=self.images[mark])
            # 選択状態に応じた枠線の変更
            if mark in self.selected:
                btn.config(bd=4, relief=tk.SUNKEN)
            else:
                btn.config(bd=2, relief=tk.RAISED)

    def check_answer(self):
        if set(self.selected) == set(self.correct_answers):
            result = "正解！"
        else:
            result = f"不正解！ 正しい組み合わせは {self.correct_answers[0]}、{self.correct_answers[1]}、{self.correct_answers[2]} です。"
        if messagebox.askyesno("結果", f"{result}\nもう一度遊びますか？"):
            self.new_game()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    game = MarkMatchingGame(root)
    root.mainloop()
