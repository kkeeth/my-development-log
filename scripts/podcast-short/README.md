# ポッドキャストのショート動画

配信済みの回から，X / YouTube 向けの縦型ショート（1080x1920）を作る．

## 準備（1 回だけ）

文字起こしは Apple Silicon の GPU を使う `mlx-whisper` を推奨する．
CPU のみの `openai-whisper` に比べて体感 5〜10 倍速く，`large-v3` が現実的に回せるので
字幕の手直しも減る．

```
uv tool install mlx-whisper
```

入れなくても動く（`openai-whisper` に自動で落ちる）が，27 分の回で 15 分ほどかかる．

Pillow が要る．`/usr/bin/python3` に入っているので，**このスクリプトはシステム Python で動かす**．

## 収録後（回ごとに 1 回）

回まるごとを単語タイムスタンプ付きで文字起こしして残す．
これを取っておけば，2 本目以降のショートで文字起こしを回さずに済む．

```
/usr/bin/python3 scripts/podcast-short/build_short.py transcribe \
  --audio ~/Downloads/'9. 「プログラミングが大嫌い」な人が作った言語.mp3' \
  --out transcripts/php-creator-was-a-perl-user.json
```

`transcripts/` は `.gitignore` 済み（音源から作り直せる派生物なので）．

## 1 本作る

### 1. 切り出しどころを決める

台本（`src/PODCASTS/WEB小噺/Season5/published/<slug>.md`）を読んで，
単体で完結していてオチのある箇所を選ぶ．

**台本の文字位置から時刻を推定してはいけない．**
収録でアドリブが入るぶん台本と実音声は等速ではなく，EP.9 では 17%（112 秒）ずれていた．

`find` に台本の言い回しをそのまま投げる．あいまい一致なので，
whisper 側が固有名詞を外していても当たる．

```
build_short.py find --transcript transcripts/<slug>.json \
  --query "プログラミングが大嫌いだ．でも問題を解決するのが好きだ"
```

### 2. 区間を切り出す

音声側．SNS 向けに -14 LUFS へ揃える．離れた 2 箇所を繋ぐなら `acrossfade` で 0.3 秒重ねる．

```
ffmpeg -i <episode>.mp3 -ss 800.7 -to 830.6 \
  -af "afade=t=in:st=0:d=0.15,loudnorm=I=-14:TP=-1.5:LRA=11" \
  -c:a libmp3lame -q:a 2 clip.mp3
```

文字起こし側．全文から同じ区間を抜いて 0 秒起点に直す．

```
build_short.py slice --transcript transcripts/<slug>.json \
  --start 800.7 --end 830.6 --out clip.json
```

### 3. 字幕を作る

`plan` で叩き台を出し，テキストを手で直す．
**台本がある回は台本の言い回しを写すのが早い**（whisper は固有名詞をだいたい外す）．

1 行 = 字幕 1 枚．`|` を入れるとそこで必ず改行する（文節の途中で割れるのを防ぐ）．
句読点はショートの慣習で落とし，半角スペースで間を取る．

```
build_short.py plan --words clip.json --out draft.tsv
# draft.tsv の text 列を captions.txt（1 行 1 枚）に書き直す
build_short.py align --words clip.json --text captions.txt --out captions.tsv
```

`align` は difflib で元の文字起こしと突き合わせ，時刻だけ引き継ぐ．
多少書き換えても時刻はずれない．

### 4. 焼く

```
build_short.py render \
  --audio clip.mp3 --captions captions.tsv --out short-01.mp4 \
  --art ~/Downloads/'9. カバー画像.jpeg' \
  --show "EP.9" --title "「プログラミングが大嫌い」な人が作った言語" \
  --handle "@kkeeth   #WEB小噺"
```

- `--art` … 上のカードと背景の両方に使う
- `--bg` … 背景だけ別画像にしたいとき（回ごとのイメージ画像など）

尺は 30 秒前後．50 秒でも X なら通るが，短いほうが最後まで見られる．

## なぜ ffmpeg に字幕を焼かせないのか

Homebrew の ffmpeg が libass / freetype 無しビルドで，`subtitles` も `drawtext` も無い．
入れ直しても得はしない．波形を再生位置で塗り分ける，アートワークを角丸で合成する，
日本語の行分けを文字数で均す — どれも ASS のタグでは書けず，結局こちら側で描くことになる．

なので Pillow で 1 フレームずつ描き，生フレームを ffmpeg に流し込んでいる．
