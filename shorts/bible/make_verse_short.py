"""성경 구절 세로 쇼츠(1080x1920) 만들기.

사용: python -X utf8 shorts/bible/make_verse_short.py shorts/bible/specs/<이름>.json
spec 예시는 shorts/bible/specs/isaiah-41-10.json. 본문은 개역한글 원문을 한 글자도 바꾸지 않는다.
audio가 있으면 그 길이에 맞추고, cards의 start(초)를 쓰면 그 시각에 해당 카드가 나온다.
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
FADE = 0.6
FONT_BIG = ImageFont.truetype(str(HERE / "fonts" / "Pretendard-Bold.otf"), 92)
FONT_REF = ImageFont.truetype(str(HERE / "fonts" / "Pretendard-Bold.otf"), 62)
FONT_SMALL = ImageFont.truetype(str(HERE / "fonts" / "Pretendard-Medium.otf"), 34)


def cover(im: Image.Image, w: int, h: int) -> Image.Image:
    scale = max(w / im.width, h / im.height)
    return im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)


def fit_font(lines: list[str], font, margin: int = 90):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = font.size
    while size > 40 and max(d.textlength(t, font=font) for t in lines) > W - 2 * margin:
        size -= 4
        font = ImageFont.truetype(font.path, size)
    return font


def text_layer(lines: list[str], font, y_center: int, spacing: int = 26) -> Image.Image:
    font = fit_font(lines, font)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    heights = [d.textbbox((0, 0), t, font=font)[3] for t in lines]
    total = sum(heights) + spacing * (len(lines) - 1)
    y = y_center - total // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for t, h in zip(lines, heights):
        sd.text((W / 2 + 3, y + 4), t, font=font, fill=(0, 0, 0, 170), anchor="ma")
        d.text((W / 2, y), t, font=font, fill=(255, 255, 255, 255), anchor="ma")
        y += h + spacing
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(shadow, layer)


def fade_alpha(t: float, start: float, end: float) -> float:
    if t < start or t > end:
        return 0.0
    return max(0.0, min(1.0, (t - start) / FADE, (end - t) / FADE))


def audio_seconds(path: str) -> float:
    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path], capture_output=True, text=True).stderr
    hms = out.split("Duration: ")[1].split(",")[0]
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main() -> None:
    spec_path = Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    root = spec_path.parent
    bg = cover(Image.open((root / spec["background"]).resolve()).convert("RGB"), int(W * 1.1), int(H * 1.1))
    audio = spec.get("audio")
    cards = spec["cards"]
    outro = spec.get("outro_seconds", 2.5)

    if not all("start" in c for c in cards):
        per = spec.get("card_seconds", 4.5)
        for i, c in enumerate(cards):
            c["start"] = 0.4 + i * per
    for i, c in enumerate(cards):
        c["end"] = cards[i + 1]["start"] if i + 1 < len(cards) else c["start"] + spec.get("card_seconds", 4.5)
    total = max(cards[-1]["end"] + outro, audio_seconds(str((root / audio).resolve())) + 0.8 if audio else 0)

    dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dim)
    for y in range(H):
        a = int(95 * max(0.0, 1 - abs(y - H * 0.45) / (H * 0.35)))
        dd.line((0, y, W, y), fill=(0, 0, 0, a))
    card_layers = [text_layer(c["lines"], FONT_BIG, int(H * 0.42)) for c in cards]
    ref_layer = text_layer([spec["reference"]], FONT_REF, int(H * 0.42))
    footer = text_layer([spec.get("footer", "성경전서 개역한글판")], FONT_SMALL, int(H * 0.9))
    channel = text_layer([spec["channel"]], FONT_SMALL, int(H * 0.86)) if spec.get("channel") else None

    out = (root / spec["output"]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", str((root / audio).resolve())]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += [str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    frames = int(total * FPS)
    ref_start = cards[-1]["end"]
    for f in range(frames):
        t = f / FPS
        zoom = 1.0 + 0.08 * t / total
        cw, ch = int(W * 1.1 / zoom), int(H * 1.1 / zoom)
        x0, y0 = (bg.width - cw) // 2, (bg.height - ch) // 2
        frame = bg.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        frame = Image.alpha_composite(frame, dim)
        for c, layer in zip(cards, card_layers):
            a = fade_alpha(t, c["start"], c["end"])
            if a > 0:
                frame = Image.alpha_composite(frame, Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), layer, a))
        a = fade_alpha(t, ref_start, total + FADE)
        if a > 0:
            frame = Image.alpha_composite(frame, Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), ref_layer, a))
        frame = Image.alpha_composite(frame, footer)
        if channel:
            frame = Image.alpha_composite(frame, channel)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"saved {out} ({total:.1f}s)")


if __name__ == "__main__":
    main()
