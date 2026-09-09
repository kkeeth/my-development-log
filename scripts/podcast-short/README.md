# ポッドキャストのショート動画

配信済みの回から，X / YouTube 向けの縦型ショート（1080x1920）を作る．

すべて `/usr/bin/python3` で動かすこと（Pillow がそこにしか入っていない）．

```
/usr/bin/python3 scripts/podcast-short/build_short.py <サブコマンド>
```

## 作業ディレクトリ

回ごとに 1 つ．**ショート 1 本 = YAML 1 枚**．

```
shorts/<slug>/
  episode.yaml          回の設定（コミットする）
  transcript.json       全文の文字起こし（gitignore）
  media/                音源とカバー（gitignore）
  01-<name>.yaml        切り出し区間＋字幕（コミットする）
  build/                書き出したもの（gitignore）
```

`<slug>` は台本 md と揃える（`src/PODCASTS/WEB小噺/Season5/published/<slug>.md`）．

音源・動画・文字起こしは音源から作り直せるので追わない．
**人が書いたもの（切り出し区間と字幕）だけが git に残る**．

## 準備（1 回だけ）

文字起こしは Apple Silicon の GPU を使う `mlx-whisper` を推奨する．
CPU のみの `openai-whisper` に比べて体感 5〜10 倍速く，`large-v3-turbo` が現実的に回せるので
字幕の手直しも減る．

```
uv tool install mlx-whisper
```

⚠️ **mlx は Metal（GPU）を要求するので，Claude Code のサンドボックス内からは動かない．**
`No Metal device available` で落ちる．`transcribe` は**本人がターミナルで叩く**か，
Claude Code なら `!` を頭に付けて実行する．エージェント側から回したいときは
`--force-cpu` を付けて `openai-whisper` に落とすこと（27 分の回で 15 分ほどかかる）．

## 回を 1 つ用意する

Art19 の RSS から音源とカバーを直接取ってくる．手で落としてこなくてよい．

```
build_short.py fetch --list                     # 最近の回を並べる
build_short.py fetch --slug json-inventor-douglas-crockford --match 5-10 \
  --title 'JSONを「発見しただけ」と言った男の経歴' \
  --script src/PODCASTS/WEB小噺/Season5/published/json-inventor-douglas-crockford.md
```

`--match` はタイトルの一部でも `5-10` のようなシーズン-番号でも通る．`--index` でも選べる．
`show`（`EP.10`）は RSS の `itunes:episode` から，`title` は RSS のタイトルから埋まるので，
台本側のタイトルを使いたいときだけ `--title` を渡す．
カバーは**回ごとの画像**が入っているので，回ごとに絵が変わる．

手元のファイルから作りたいときは `init-episode`（`--audio` と `--cover` を渡す）．

続けて，回まるごとを単語タイムスタンプ付きで文字起こしする（**ターミナルで直接**）。

```
build_short.py transcribe --episode shorts/json-inventor-douglas-crockford
```

これを 1 回取っておけば，その回から何本ショートを作っても文字起こしは回さない．

## 1 本作る

### 1. 切り出しどころを決める

台本を読んで，単体で完結していてオチのある箇所を選ぶ．

**台本の文字位置から時刻を推定してはいけない．**
収録でアドリブが入るぶん台本と実音声は等速ではなく，EP.9 では 17%（112 秒）ずれていた．

`find` に台本の言い回しをそのまま投げる．あいまい一致なので，
whisper 側が固有名詞を外していても当たる．

```
build_short.py find --episode shorts/<slug> \
  --query "プログラミングが大嫌いだ．でも問題を解決するのが好きだ"
```

```
0.81   800.8s - 804.9s  (0:13:20)  ...プログラミングは実は大嫌いだとでも問題を解決するのは好きだと...
0.44   807.5s - 811.9s  (0:13:27)  ...言語作者がプログラミング嫌いってか大嫌いと言ってるのも...
```

**クエリは台本の一文をそのまま貼る．要約したり言い換えたりしない．**
文字の並びで探しているので，内容が合っていても言い回しが違うと当たらない．

| クエリ | 得点 |
| --- | --- |
| 「紙にPHPって大文字で落書きしてたら象っぽく見えた」（台本のまま） | **0.96** |
| 「エレファントという名前で象に見えるという落書きから生まれた」（言い換え） | 0.34 |
| 「パーソナルホームページツールの略でした」（カタカナ） | **0.84** |
| 「最初はPersonal Home Page Toolsの略でした」（英字） | 0.28 |

**英字はカタカナに開く．** 喋った音を whisper がカタカナで書き起こすため，
英字のまま投げると当たらない．

得点は 0.8 以上なら当たり，0.4 台なら別の箇所．次点と 2 倍以上開いていれば安心してよい．

### 2. 下書きを起こす

```
build_short.py draft --episode shorts/<slug> --name hate-programming \
  --start 800.7 --end 830.6
```

`NN-<name>.yaml` ができる．

### 3. 字幕を直す（唯一の手作業）

YAML の `captions` を直す．1 行 = 字幕 1 枚．

- **台本の言い回しを写すのが早い**．whisper は固有名詞をだいたい外す
- `|` を入れるとそこで必ず改行する（文節の途中で割れるのを防ぐ）
- 句読点はショートの慣習で落とし，半角スペースで間を取る

書き換えても時刻はずれない．`build` が difflib で元の文字起こしと突き合わせ，
時刻だけ引き継ぐ．

離れた 2 箇所を繋ぎたいときは `segments` を増やす．0.3 秒のクロスフェードで繋がる．

```yaml
segments:
- [742.5, 760.6]
- [798.4, 830.6]
```

### 4. 焼く

```
build_short.py build shorts/<slug>/01-hate-programming.yaml
```

音の切り出し（-14 LUFS へ正規化）→ 文字起こしの切り出し → 字幕の時刻合わせ →
レンダリングまで通って `build/01-hate-programming.mp4` が出る．

尺は 30 秒前後．50 秒でも X なら通るが，短いほうが最後まで見られる．

## 見た目を変えたい

`build_short.py` 冒頭の定数を触る．

- `BG_SCRIM` … 背景に敷いたカバーをどれだけ暗くするか．カバーが明るいと白字幕が読めなくなる
- `ACCENT` … 波形と `EP.N` の色
- `CAP_SIZE` / `CAP_LINE_H` / `LAYOUT_ART` … 字幕の大きさと配置

`episode.yaml` の `cover` が無ければ，カードを出さない単色グラデーションの配置になる．
背景だけ別画像にしたいときは，ショートの YAML に `bg:` を足す．

## なぜ ffmpeg に字幕を焼かせないのか

Homebrew の ffmpeg が libass / freetype 無しビルドで，`subtitles` も `drawtext` も無い．
入れ直しても得はしない．波形を再生位置で塗り分ける，アートワークを角丸で合成する，
日本語の行分けを文字数で均す — どれも ASS のタグでは書けず，結局こちら側で描くことになる．

なので Pillow で 1 フレームずつ描き，生フレームを ffmpeg に流し込んでいる．
