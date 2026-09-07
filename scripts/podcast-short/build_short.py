#!/usr/bin/env python3
"""ポッドキャストの切り抜きから縦型ショート動画（1080x1920）を作る．

3 段構え:
  1) plan   … whisper の word timestamps から字幕案を TSV に出す
  2)（人手）TSV の text 列を直す（whisper は固有名詞をだいたい間違える）
  3) render … TSV から動画を焼く

Pillow が要るので **/usr/bin/python3 で実行すること**．
Homebrew の ffmpeg が libass / freetype 無しビルドなので，
字幕は ffmpeg ではなく Pillow で描いて生フレームを ffmpeg に流し込む．

  /usr/bin/python3 build_short.py plan   --words clip.json --out captions.tsv
  /usr/bin/python3 build_short.py render --audio clip.mp3 --captions captions.tsv \
      --out short-01.mp4 --show "雨宿りとWEBの小噺" --handle "@kkeeth  #WEB小噺" \
      --art artwork.jpg
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

# ---- 見た目 -------------------------------------------------------------
W, H = 1080, 1920
FPS = 30
BG_TOP = (18, 26, 42)          # 背景（上）
BG_BOTTOM = (8, 11, 18)        # 背景（下）
ACCENT = (255, 194, 75)        # アクセント #FFC24B
CAP_ON = (255, 255, 255)       # 発話済みの字幕
CAP_OFF = (122, 133, 150)      # まだ喋っていない字幕
FOOT = (108, 120, 138)
TITLE_COL = (150, 162, 180)

FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_MID = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

CAP_SIZE = 72
CAP_LINE_H = 104
CAP_MAX_W = W - 130
SHOW_SIZE = 42
TITLE_SIZE = 40
FOOT_SIZE = 34

ART_SIZE = 320                 # 上に置くアートワークカードの一辺
ART_RADIUS = 56
BG_BLUR = 52                   # 背景に敷くアートワークのぼかし
BG_SCRIM = (0.86, 0.95)        # 背景を暗くする度合い（上, 下）

WAVE_H = 190                   # 波形の最大振幅
WAVE_BARS = 116
WAVE_DIM = (52, 62, 80)

# アートワークの有無でタテの割り付けを変える
LAYOUT_PLAIN = {"art_y": None, "show_y": 150, "title_y": 232,
                "cap_y": 860, "wave_y": 1380}
LAYOUT_ART = {"art_y": 300, "show_y": 560, "title_y": 632,
              "cap_y": 1000, "wave_y": 1450}

# ---- 字幕の切り方 -------------------------------------------------------
MAX_CHARS_PER_CUE = 24
GAP_SPLIT = 0.35               # これより長い無音で割る
BREAK_AFTER = "，．、。？！?! "


# =========================================================================
# plan
# =========================================================================
def load_words(json_path):
    data = json.loads(Path(json_path).read_text())
    return [{"t": w["word"].strip(), "s": w["start"], "e": w["end"]}
            for seg in data["segments"] for w in seg.get("words", [])
            if w["word"].strip()]


def chunk(words):
    cues, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = "".join(x["t"] for x in cur)
        gap = words[i + 1]["s"] - w["e"] if i + 1 < len(words) else 99
        if (len(text) >= MAX_CHARS_PER_CUE
                or gap > GAP_SPLIT
                or (w["t"][-1] in BREAK_AFTER and len(text) >= 8)):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)

    # はぐれた短い行は前に戻す（「よね」だけの字幕を作らない）
    merged = []
    for c in cues:
        text = "".join(x["t"] for x in c)
        if merged and len(text) < 7:
            prev = "".join(x["t"] for x in merged[-1])
            if len(prev) + len(text) <= MAX_CHARS_PER_CUE + 10:
                merged[-1] = merged[-1] + c
                continue
        merged.append(c)

    return [{"s": c[0]["s"], "e": c[-1]["e"], "text": "".join(x["t"] for x in c)}
            for c in merged]


def cmd_plan(args):
    cues = chunk(load_words(args.words))
    out = ["#start\tend\ttext"]
    out += ["%.3f\t%.3f\t%s" % (c["s"], c["e"], c["text"]) for c in cues]
    Path(args.out).write_text("\n".join(out) + "\n")
    print("wrote %s (%d cues)" % (args.out, len(cues)))
    for c in cues:
        print("  %6.2f-%6.2f  %s" % (c["s"], c["e"], c["text"]))



# =========================================================================
# align … 手直ししたテキストを元の文字起こしに突き合わせて時刻を振り直す
# =========================================================================
def char_stream(words):
    """whisper の word を 1 文字ずつに割って (文字, 開始, 終了) にする．"""
    out = []
    for w in words:
        n = len(w["t"])
        span = (w["e"] - w["s"]) / max(n, 1)
        for i, ch in enumerate(w["t"]):
            out.append((ch, w["s"] + i * span, w["s"] + (i + 1) * span))
    return out


def cmd_align(args):
    import difflib
    stream = char_stream(load_words(args.words))
    src = "".join(c[0] for c in stream)

    lines = [l.strip() for l in Path(args.text).read_text().splitlines() if l.strip()]
    dst = "".join(strip_marks(l) for l in lines)

    # 手直し後 → 元 の文字位置対応表を作る
    m = difflib.SequenceMatcher(None, dst, src, autojunk=False)
    idx = [None] * (len(dst) + 1)
    for a, b, n in m.get_matching_blocks():
        for k in range(n):
            idx[a + k] = b + k
    # 対応が取れなかった位置は前後から補間する
    last = 0
    for i in range(len(idx)):
        if idx[i] is None:
            idx[i] = last
        else:
            last = idx[i]

    cues, pos = [], 0
    for line in lines:
        n = len(strip_marks(line))
        s_i, e_i = idx[pos], idx[min(pos + n, len(dst)) - 1]
        cues.append((stream[s_i][1], stream[min(e_i, len(stream) - 1)][2], line))
        pos += n

    out = ["#start\tend\ttext"]
    out += ["%.3f\t%.3f\t%s" % c for c in cues]
    Path(args.out).write_text("\n".join(out) + "\n")
    print("wrote %s (%d cues)" % (args.out, len(cues)))
    for c in cues:
        print("  %6.2f-%6.2f  %s" % c)


# =========================================================================
# render
# =========================================================================
def read_cues(path):
    cues = []
    for ln in Path(path).read_text().splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        s, e, text = ln.split("\t", 2)
        cues.append({"s": float(s), "e": float(e), "text": text.strip()})
    return cues


def strip_marks(text):
    """幅・文字数の計算から外す記号（空白と明示改行）を落とす．"""
    for ch in (" ", "\u3000", "|"):
        text = text.replace(ch, "")
    return text


def _greedy(text, font, max_w, max_chars):
    lines, line = [], ""
    for ch in text:
        trial = line + ch
        over = font.getlength(trial.replace(" ", "")) > max_w
        if (over or len(trial.strip()) > max_chars) and line.strip():
            lines.append(line.strip())
            line = "" if ch == " " else ch
        else:
            line = trial
    if line.strip():
        lines.append(line.strip())
    return lines


def wrap_lines(text, font, max_w):
    """幅を実測して折り返す．最終行が 1〜2 文字で孤立しないよう行数で均す．

    `|` が入っていればそこで必ず改行する（文節で割りたいときに使う）．
    """
    if "|" in text:
        out = []
        for part in text.split("|"):
            out += _greedy(part.strip(), font, max_w, 99) or [""]
        return [l for l in out if l]
    lines = _greedy(text, font, max_w, 99)
    if len(lines) < 2:
        return lines
    n = len(lines)
    target = -(-len("".join(lines)) // n)
    balanced = _greedy(text, font, max_w, target)
    return balanced if len(balanced) <= n else lines


def cover(Image, img, w, h):
    """アスペクトを保って w x h を埋めるように切り抜く．"""
    src_r, dst_r = img.width / img.height, w / h
    if src_r > dst_r:
        nw = int(img.height * dst_r)
        img = img.crop(((img.width - nw) // 2, 0, (img.width + nw) // 2, img.height))
    else:
        nh = int(img.width / dst_r)
        img = img.crop((0, (img.height - nh) // 2, img.width, (img.height + nh) // 2))
    return img.resize((w, h), Image.LANCZOS)


def rounded(Image, ImageDraw, img, size, radius):
    """正方形に切ってカドを丸めた RGBA を返す．"""
    sq = cover(Image, img, size, size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                           radius=radius, fill=255)
    sq.putalpha(mask)
    return sq


def make_background(Image, ImageDraw, ImageFilter, art):
    """アートワークがあればぼかして敷き，無ければ単色グラデーション．"""
    if art is None:
        bg = Image.new("RGB", (W, H), BG_BOTTOM)
        d = ImageDraw.Draw(bg)
        for y in range(H):
            k = y / H
            d.line([(0, y), (W, y)], fill=tuple(
                int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3)))
        return bg

    bg = cover(Image, art, W, H).filter(ImageFilter.GaussianBlur(BG_BLUR)).convert("RGB")
    # 字幕が乗るので上から下へ濃くなる暗幕をかける
    scrim = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(scrim)
    for y in range(H):
        k = y / H
        a = int(255 * (BG_SCRIM[0] + (BG_SCRIM[1] - BG_SCRIM[0]) * k))
        col = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3))
        d.line([(0, y), (W, y)], fill=col + (a,))
    return Image.alpha_composite(bg.convert("RGBA"), scrim).convert("RGB")


def draw_static(Image, ImageDraw, ImageFilter, base, L, art,
                show, title, handle, f_show, f_title, f_foot):
    d = ImageDraw.Draw(base)
    if art is not None and L["art_y"] is not None:
        card = rounded(Image, ImageDraw, art, ART_SIZE, ART_RADIUS)
        x, y = (W - ART_SIZE) // 2, L["art_y"] - ART_SIZE // 2
        # 影を先に落としてからカードを置く
        shadow = Image.new("RGBA", (W, H))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [x, y + 14, x + ART_SIZE, y + ART_SIZE + 14],
            radius=ART_RADIUS, fill=(0, 0, 0, 150))
        base.paste(Image.alpha_composite(base.convert("RGBA"),
                                         shadow.filter(ImageFilter.GaussianBlur(22))
                                         ).convert("RGB"), (0, 0))
        base.paste(card, (x, y), card)
        d = ImageDraw.Draw(base)

    if show:
        d.text((W // 2, L["show_y"]), show, font=f_show, fill=ACCENT, anchor="mm")
        w = f_show.getlength(show)
        for dx in (-1, 1):
            x0 = W // 2 + dx * (w / 2 + 18)
            d.line([(x0, L["show_y"]), (x0 + dx * 22, L["show_y"])],
                   fill=ACCENT, width=3)
    if title:
        d.text((W // 2, L["title_y"]), title, font=f_title, fill=TITLE_COL, anchor="mm")
    if handle:
        d.text((W // 2, H - 110), handle, font=f_foot, fill=FOOT, anchor="mm")


def audio_peaks(audio, nbars):
    """音声を nbars 本ぶんのピーク値（0..1）に落とす．"""
    import array
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", audio,
         "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "4000", "-"],
        stdout=subprocess.PIPE, check=True).stdout
    a = array.array("h")
    a.frombytes(raw[:len(raw) // 2 * 2])
    step = max(len(a) // nbars, 1)
    peaks = [max([abs(v) for v in a[i * step:(i + 1) * step]] or [0])
             for i in range(nbars)]
    top = max(peaks) or 1
    return [v / top for v in peaks]


def cmd_render(args):
    sys.path.insert(0, "/usr/lib/python3/dist-packages")
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    cues = read_cues(args.captions)
    dur = cues[-1]["e"] + 0.6

    art = Image.open(args.art).convert("RGB") if args.art else None
    bg_src = Image.open(args.bg).convert("RGB") if args.bg else art
    L = LAYOUT_ART if art is not None else LAYOUT_PLAIN

    f_cap = ImageFont.truetype(FONT_BOLD, CAP_SIZE, index=0)
    f_show = ImageFont.truetype(FONT_BOLD, SHOW_SIZE, index=0)
    f_title = ImageFont.truetype(FONT_MID, TITLE_SIZE, index=0)
    f_foot = ImageFont.truetype(FONT_MID, FOOT_SIZE, index=0)

    base = make_background(Image, ImageDraw, ImageFilter, bg_src)
    draw_static(Image, ImageDraw, ImageFilter, base, L, art,
                args.show, args.title, args.handle, f_show, f_title, f_foot)

    peaks = audio_peaks(args.audio, WAVE_BARS)
    bar_w = W / WAVE_BARS
    bar_pad = bar_w * 0.34
    wave_y = L["wave_y"]
    cap_y = L["cap_y"]

    for c in cues:
        c["lines"] = wrap_lines(c["text"], f_cap, CAP_MAX_W)
        c["nchars"] = sum(len(l) for l in c["lines"])

    gray_cache = {}

    def gray_tile(ci):
        """発話前のグレー字幕はキューごとに 1 回だけ描いて使い回す"""
        if ci not in gray_cache:
            img = base.copy()
            d = ImageDraw.Draw(img)
            lines = cues[ci]["lines"]
            y0 = cap_y - (len(lines) - 1) * CAP_LINE_H / 2
            for i, line in enumerate(lines):
                x = (W - f_cap.getlength(line)) / 2
                d.text((x, y0 + i * CAP_LINE_H), line, font=f_cap, fill=CAP_OFF,
                       anchor="lm", stroke_width=7, stroke_fill=(6, 9, 15))
            gray_cache[ci] = img
        return gray_cache[ci]

    def draw_wave(d, progress):
        """再生済みをアクセント色，未再生をくすませて出す．"""
        played = progress * WAVE_BARS
        for i, v in enumerate(peaks):
            h = max(WAVE_H * v, 4)
            x = i * bar_w + bar_pad / 2
            w = bar_w - bar_pad
            box = [x, wave_y - h / 2, x + w, wave_y + h / 2]
            col = ACCENT if i <= played else WAVE_DIM
            # 角丸の半径はバーの短辺を超えられない
            r = int(min(w, h) / 2) - 1
            if r >= 1:
                d.rounded_rectangle(box, radius=r, fill=col)
            else:
                d.rectangle(box, fill=col)

    nframes = int(dur * FPS)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
        "-r", str(FPS), "-i", "-",
        "-i", args.audio,
        "-map", "0:v", "-map", "1:a", "-t", "%.2f" % dur,
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "20", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", args.out,
    ], stdin=subprocess.PIPE)

    ci = 0
    for n in range(nframes):
        t = n / FPS
        while ci < len(cues) and t > cues[ci]["e"] + 0.12:
            ci += 1
        cur = cues[ci] if ci < len(cues) and t >= cues[ci]["s"] else None
        img = (gray_tile(ci) if cur else base).copy()
        d = ImageDraw.Draw(img)
        if cur:
            prog = (t - cur["s"]) / max(cur["e"] - cur["s"], 0.01)
            spoken = min(cur["nchars"], int(cur["nchars"] * prog) + 1)
            y0 = cap_y - (len(cur["lines"]) - 1) * CAP_LINE_H / 2
            seen = 0
            for i, line in enumerate(cur["lines"]):
                k = max(0, min(len(line), spoken - seen))
                if k:
                    x = (W - f_cap.getlength(line)) / 2
                    d.text((x, y0 + i * CAP_LINE_H), line[:k], font=f_cap,
                           fill=CAP_ON, anchor="lm", stroke_width=7,
                           stroke_fill=(6, 9, 15))
                seen += len(line)
        draw_wave(d, t / dur)
        ff.stdin.write(img.tobytes())
        if n % 600 == 0:
            print("  %d/%d frames" % (n, nframes), file=sys.stderr)
    ff.stdin.close()
    ff.wait()
    print("done:", args.out, "(%.1fs)" % dur)


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd")
a = sub.add_parser("plan")
a.add_argument("--words", required=True)
a.add_argument("--out", required=True)
a.set_defaults(fn=cmd_plan)
c = sub.add_parser("align")
c.add_argument("--words", required=True, help="whisper の json")
c.add_argument("--text", required=True, help="手直ししたテキスト（1 行 = 字幕 1 枚）")
c.add_argument("--out", required=True)
c.set_defaults(fn=cmd_align)
b = sub.add_parser("render")
b.add_argument("--audio", required=True)
b.add_argument("--captions", required=True)
b.add_argument("--out", required=True)
b.add_argument("--show", default="")
b.add_argument("--title", default="")
b.add_argument("--handle", default="")
b.add_argument("--art", default=None, help="番組アートワーク（上のカード＋背景に使う）")
b.add_argument("--bg", default=None, help="背景に敷く画像（配信回の画像など．--art と別にしたいとき）")
b.set_defaults(fn=cmd_render)
args = p.parse_args()
if not getattr(args, "fn", None):
    p.print_help(); sys.exit(1)
args.fn(args)
