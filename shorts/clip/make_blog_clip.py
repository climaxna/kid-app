"""블로그 글 이미지로 네이버 클립용 세로 영상(1080x1920) 만들기.

사용: python -X utf8 shorts/clip/make_blog_clip.py shorts/clip/specs/<이름>.json
정사각형 블로그 이미지를 가운데 두고, 같은 이미지를 흐리게 키워 위아래를 채운 뒤 큰 자막을 얹는다.
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FONTS = HERE.parent / "bible" / "fonts"
W, H, FPS = 1080, 1920, 30
XFADE = 0.4
FONT_CAP = ImageFont.truetype(str(FONTS / "Pretendard-Bold.otf"), 78)
FONT_SUB = ImageFont.truetype(str(FONTS / "Pretendard-Bold.otf"), 58)


def fit(lines, font, margin=70):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while font.size > 40 and max(d.textlength(t, font=font) for t in lines) > W - 2 * margin:
        font = ImageFont.truetype(font.path, font.size - 4)
    return font


def caption(lines, font, y_center, color=(255, 255, 255, 255)):
    font = fit(lines, font)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    hs = [d.textbbox((0, 0), t, font=font)[3] for t in lines]
    y = y_center - (sum(hs) + 18 * (len(lines) - 1)) // 2
    for t, h in zip(lines, hs):
        sd.text((W / 2 + 3, y + 4), t, font=font, fill=(0, 0, 0, 200), anchor="ma")
        d.text((W / 2, y), t, font=font, fill=color, anchor="ma")
        y += h + 18
    return Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)), layer)


def scene_base(path: Path):
    im = Image.open(path).convert("RGB")
    side = min(im.size)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2))
    blur = im.resize((H, H)).filter(ImageFilter.GaussianBlur(40))
    blur = blur.crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    blur = Image.blend(blur, Image.new("RGB", (W, H), (0, 0, 0)), 0.35)
    return blur, im


def render_scene(blur, im, t, dur):
    zoom = 1.0 + 0.06 * t / dur
    size = int(W * zoom)
    big = im.resize((size, size), Image.BILINEAR)
    off = (size - W) // 2
    frame = blur.copy()
    frame.paste(big.crop((off, off, off + W, off + W)), (0, (H - W) // 2))
    return frame.convert("RGBA")


def main():
    spec_path = Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    scenes = []
    for s in spec["scenes"]:
        blur, im = scene_base(ROOT / s["image"])
        top = caption(s["top"], FONT_CAP, 250) if s.get("top") else None
        bottom = caption(s["bottom"], FONT_SUB, H - 230, (255, 226, 120, 255)) if s.get("bottom") else None
        scenes.append((blur, im, top, bottom, s["seconds"]))
    total = sum(s[4] for s in scenes)

    out = (spec_path.parent / spec["output"]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if spec.get("audio"):
        cmd += ["-i", str((spec_path.parent / spec["audio"]).resolve()), "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def frame_at(i, t):
        blur, im, top, bottom, dur = scenes[i]
        f = render_scene(blur, im, t, dur)
        for layer in (top, bottom):
            if layer is not None:
                f = Image.alpha_composite(f, layer)
        return f

    start = 0.0
    for i, (_, _, _, _, dur) in enumerate(scenes):
        for k in range(int(dur * FPS)):
            t = k / FPS
            f = frame_at(i, t)
            if i + 1 < len(scenes) and t > dur - XFADE:
                f = Image.blend(f, frame_at(i + 1, 0), (t - (dur - XFADE)) / XFADE)
            proc.stdin.write(f.convert("RGB").tobytes())
        start += dur
    proc.stdin.close()
    proc.wait()
    print(f"saved {out} ({total:.1f}s)")


if __name__ == "__main__":
    main()
