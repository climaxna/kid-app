from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import json

source = Path('C:/Users/kim/Downloads')
out = Path('C:/blog/output/imagegen/time-edits/original-quality')
out.mkdir(exist_ok=True)
ref = Image.open(source / '1번방_1.png').convert('RGB')
two = Image.open(source / '2번방2진짜.png').convert('RGB')
bg = (41, 42, 45)

def stamp(minute):
    tile = Image.new('RGB', (55, 10), bg)
    # Reuse original screenshot glyph pixels without resizing or font rendering.
    tile.paste(ref.crop((629, 223, 652, 233)), (0, 0))  # 오전
    tile.paste(ref.crop((675, 223, 682, 233)), (25, 0)) # 9
    tile.paste(ref.crop((667, 223, 670, 233)), (32, 0)) # :
    tile.paste(ref.crop((654, 223, 660, 233)), (34, 0)) # 1
    if minute == '10':
        tile.paste(ref.crop((660, 223, 667, 233)), (40, 0)) # 0
    else:
        tile.paste(two.crop((669, 211, 676, 221)), (40, 0)) # 2
    return tile

report = []
for name, minute in [('2번방.png', '10'), ('2번방1.png', '12'), ('2번방2진짜.png', '12')]:
    original = Image.open(source / name).convert('RGB')
    edited = original.copy()
    rows = []
    for y in range(205, original.height):
        active = any(max(abs(a-b) for a,b in zip(original.getpixel((x,y)), bg)) > 30 for x in range(628,686))
        if active:
            if not rows or y > rows[-1][-1]+1:
                rows.append([y])
            else:
                rows[-1].append(y)
    mask = Image.new('L', original.size, 0)
    draw = ImageDraw.Draw(mask)
    tile = stamp(minute)
    assert len(rows) == 26 and all(len(row) == 10 for row in rows)
    for row in rows:
        y = row[0]
        edited.paste(tile, (629, y))
        draw.rectangle((629,y,683,y+9), fill=255)
    diff = ImageChops.difference(original, edited)
    outside = ImageChops.multiply(diff, ImageChops.invert(mask).convert('RGB'))
    assert outside.getbbox() is None
    destination = out / (Path(name).stem + '_오전9시' + minute + '분.png')
    edited.save(destination, format='PNG')
    saved = Image.open(destination).convert('RGB')
    assert ImageChops.difference(saved, edited).getbbox() is None
    assert saved.size == (1920,1080)
    report.append({'file':str(destination),'size':saved.size,'format':'PNG','edited_rows':len(rows),'pixels_outside_time_boxes_identical':True})
    if minute == '10':
        edited.crop((620, rows[0][0]-5, 695, rows[0][0]+15)).resize((900,240), Image.Resampling.NEAREST).save(out / 'timestamp-detail.png')
        tile.resize((660,120), Image.Resampling.NEAREST).save(out / 'time-0910-detail.png')
stamp('12').resize((660,120), Image.Resampling.NEAREST).save(out / 'time-0912-detail.png')
(out/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
