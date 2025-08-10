# ナインタイル タイマー & クロスエッジ判定Web（React + TypeScript + Vite）

ナインタイルのタイムアタック練習用Webアプリです。Pythonista版のロジックを移植し、ブラウザ上で動作します。

## 必要環境
- Node.js 18+（推奨: 20 以上）

## セットアップと実行
```bash
cd web
npm install
npm run dev
```
- ローカル開発サーバが立ち上がります。LAN 共有したい場合は `npm run dev -- --host` を利用してください。

### 本番ビルドとプレビュー
```bash
npm run build
npm run preview


## WSLでの利用
Windows上のWSL2でも問題なく動作します。ブラウザはWindows側で開いてください。

### 手順（WSLのシェル）
```bash
# Nodeの導入（例: nvm）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm use --lts

# プロジェクトへ移動（例: Dドライブのこのプロジェクト）
cd /mnt/d/pythonProject7/ゲーム/ナインタイル/web

# 依存のインストール
npm install

# 開発サーバ起動（Windowsブラウザからアクセスする場合は --host を付与）
npm run dev -- --host
```

- アクセス: Windowsのブラウザで `http://localhost:5173`
- つながらない場合: `npm run dev -- --host 0.0.0.0` を試す、または `ip addr` でWSLのIPを確認し `http://<WSL_IP>:5173` にアクセス
- パフォーマンス: `/mnt/*` 上のプロジェクトはI/Oが遅くなることがあります。必要に応じてWSLのホーム配下に複製して作業してください。

```

## 遊び方（操作）
- START: 計測開始。9枚から3枚を選択して答えるとクロスエッジ判定が行われ、NEXT待機に移行します。
- STOP: 通常通りナインタイルのタイムを測りたい場合、手元のナインタイルを解いてSTOPします。
- NEXT: 次の問題へ進みます。
- 30 トライアル終了後、平均タイムが表示されます。

## 遊び方

### 1) ナインタイルのタイマーとして使う（実物のパズルで計測）
- START を押す
- 手元のナインタイルを解く
- できたら STOP を押して計測終了（タイムが記録されます）
- NEXT を押して次の問題へ（合計 30 トライアルで平均が算出されます）

ポイント: 画面の9枚はあくまでダミー表示です。選択操作は不要です（STOPで記録）。

### 2) クロスエッジ判定の練習として使う（画面内で3枚選択）
- START を押す
- 画面上の9枚から3枚をタップで選択
- 自動で判定（正解なら✅、不正解/クロスなら❌を表示）。タイムが記録され、PAUSEDへ
- NEXT を押して次の問題へ（合計 30 トライアルで平均が算出されます）

判定条件の要約は下記「クロスエッジ判定」を参照してください。

## クロスエッジ判定
3 枚選んだタイルについて、以下をすべて満たすと正解です。
- 3 枚がすべて異なるマークである
- 次のクロス対を同時に含まない
  - Maru × Brocco
  - Lime × Sakura
  - Cookie × Hanabana
- その問題に含まれる「暖色（Maru/Cookie/Sakura）」の総数に応じ、選ぶ 3 枚に含める暖色/寒色の枚数が以下に一致する
  - 暖色合計 6 → (暖3, 寒0)
  - 暖色合計 5 → (暖2, 寒1)
  - 暖色合計 4 → (暖1, 寒2)
  - 暖色合計 3 → (暖0, 寒3)

## 効果音とタイマー
- 計測中、1 秒ごとに短音、3 秒ごとに長音が鳴ります（初回操作時に音声を解放）。
- 正解/不正解の効果音はアセットが `public/assets/` に用意されています（必要に応じて有効化可能）。

## データとアセット
- パターンCSV: `public/data/512_Patterns_of_Nine_Tile.csv`
- 画像: `public/assets/{maru,cookie,sakura,lime,hanabi,block}.png`
- 効果音: `public/assets/{correct_sound.wav, incorrect_sound_alt.wav, incorrect_sound_soft.wav}`

## 主要ファイル
- `src/App.tsx`: 画面構成とゲーム進行（START/RUNNING/PAUSED）
- `src/components/Tile.tsx`: タイル表示と選択UI
- `src/logic/constants.ts`: マーク定義・画像パス・クロス関係
- `src/logic/patterns.ts`: CSV読込・ビット→マーク展開・バリデーション
- `src/logic/judge.ts`: 選択3枚の正誤判定
- `src/logic/timer.ts`: タイマーとビープ音生成

## よくある質問
- 画像が表示されない: `public/assets` パス配下に画像が存在するか確認してください。
- 音が鳴らない: ブラウザの自動再生制限のため、初回に画面操作が必要です。iOS Safari はサイレントモードの影響も受けます。

## デプロイ（例）
- 任意の静的ホスティングで `web/` をビルドし、生成される `dist/` を配信。
- Vercel / Netlify の場合はプロジェクトルートを `web/`、ビルドコマンド `npm run build`、出力 `dist` に設定してください。