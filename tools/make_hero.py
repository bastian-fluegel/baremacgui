"""Build docs/hero.png: example code on the left, the real window screenshot on the right.

Usage: python tools/make_hero.py   (needs Pillow, which is a dev tool only, not a dependency)

The window comes from docs/screenshots/settings.png (CI capture). That capture has a 2 px black
margin and black corners, so the margin is cropped and the dark corner pixels are flooded away into an alpha mask
before it is composited with a soft shadow.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SIZE = (1632, 668)
BG = (233, 236, 242)
PANEL = (30, 33, 40)
FG = (212, 216, 224)
KEYWORD = (198, 120, 221)
STRING = (152, 195, 121)
COMMENT = (110, 118, 132)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
KEYWORDS = {"with", "as", "from", "import"}
CODE_FIRST, CODE_LAST = "with Window", "save = Button"
MARGIN = 3


def code_lines():
    lines = (ROOT / "examples" / "02_settings.py").read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(CODE_FIRST))
    end = next(i for i, l in enumerate(lines) if CODE_LAST in l)
    return ["app = App(\"Settings\")", ""] + lines[start:end + 1] + ["", "# examples/02_settings.py (the button handlers follow)"]


def draw_code(draw, box, lines, font):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=18, fill=PANEL)
    step = font.getlength("m")
    y = y0 + 24
    for line in lines:
        x = x0 + 24
        if line.startswith("#"):
            draw.text((x, y), line, font=font, fill=COMMENT)
        else:
            indent = len(line) - len(line.lstrip())
            x += indent * step
            i, text = 0, line.lstrip()
            while i < len(text):
                if text[i] == '"':
                    j = text.index('"', i + 1) + 1
                    draw.text((x, y), text[i:j], font=font, fill=STRING)
                    x += (j - i) * step
                    i = j
                elif text[i].isalpha() or text[i] == "_":
                    j = i
                    while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                        j += 1
                    word = text[i:j]
                    draw.text((x, y), word, font=font, fill=KEYWORD if word in KEYWORDS else FG)
                    x += (j - i) * step
                    i = j
                else:
                    draw.text((x, y), text[i], font=font, fill=FG)
                    x += step
                    i += 1
        y += 20


def window_image():
    shot = Image.open(ROOT / "docs" / "screenshots" / "settings.png").convert("RGB")
    w, h = shot.size
    shot = shot.crop((MARGIN, MARGIN, w - MARGIN, h - MARGIN))
    w, h = shot.size
    out = shot.convert("RGBA")
    mask = Image.new("L", (w, h), 255)
    gray = shot.convert("L")
    # Flood the dark corner pixels from each corner; the window itself is light there.
    for cx, cy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        sx, sy = (1 if cx == 0 else -1), (1 if cy == 0 else -1)
        seen, todo = set(), [(cx, cy)]
        while todo:
            x, y = todo.pop()
            if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or abs(x - cx) > 30 or abs(y - cy) > 30:
                continue
            seen.add((x, y))
            if gray.getpixel((x, y)) > 200:
                continue
            mask.putpixel((x, y), 0)
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    out.putalpha(mask)
    return out


def main():
    img = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(img)
    lines = code_lines()
    draw_code(draw, (30, 30, 963, SIZE[1] - 30), lines, ImageFont.truetype(MONO, 13))
    win = window_image()
    k = 1.25
    win = win.resize((round(win.width * k), round(win.height * k)), Image.LANCZOS)
    x = 963 + (SIZE[0] - 963 - win.width) // 2
    y = (SIZE[1] - win.height) // 2
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 90), (x, y + 14), win.getchannel("A"))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    base = img.convert("RGBA")
    base.alpha_composite(shadow)
    base.alpha_composite(win, (x, y))
    base.convert("RGB").save(ROOT / "docs" / "hero.png", optimize=True)


if __name__ == "__main__":
    main()
