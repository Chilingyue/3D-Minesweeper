"""生成站点图标与社交分享图（用于搜索引擎结果图标 + 链接预览卡片）。

用法：
    python tools/make_brand_assets.py

输出（web/imgs/）：
    favicon.ico            16/32/48 多尺寸，浏览器标签页与搜索结果左侧图标
    icon-192.png           192x192，Android 主屏
    apple-touch-icon.png   180x180，iOS 主屏
    og-cover.png           1200x630，Open Graph / Twitter 分享大图
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "web" / "imgs"

FONT_BOLD = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_REG = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"

GOLD_STOPS = [
    (0.00, (255, 253, 235)),
    (0.12, (255, 240, 178)),
    (0.30, (253, 212, 96)),
    (0.55, (247, 189, 55)),
    (0.78, (252, 206, 88)),
    (1.00, (255, 233, 165)),
]
TEXT_GOLD_STOPS = [
    (0.00, (255, 235, 150)),
    (0.30, (255, 204, 62)),
    (0.70, (247, 173, 30)),
    (1.00, (255, 214, 90)),
]


def vertical_gradient(w, h, stops):
    ys = np.linspace(0.0, 1.0, h)
    pos = [s[0] for s in stops]
    chans = [np.interp(ys, pos, [s[1][c] for s in stops]) for c in range(3)]
    arr = np.stack(chans, axis=1).astype(np.uint8)[:, None, :]
    return Image.fromarray(np.repeat(arr, w, axis=1), mode="RGB")


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def gradient_text(text, font, stops, spacing=0):
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    widths = [tmp.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    ascent, descent = font.getmetrics()

    mask = Image.new("L", (int(total) + 12, ascent + descent + 12), 0)
    md = ImageDraw.Draw(mask)
    x = 6
    for ch, w in zip(text, widths):
        md.text((x, 6), ch, font=font, fill=255)
        x += w + spacing

    grad = vertical_gradient(mask.width, mask.height, stops)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out.crop(out.getbbox())


def make_icon(size: int) -> Image.Image:
    """方形应用图标：金底 + 深色内块 + 金色 3D 字样。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r = int(size * 0.215)

    plate = vertical_gradient(size, size, GOLD_STOPS)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    layer.paste(plate, (0, 0), rounded_mask((size, size), r))
    img.alpha_composite(layer)

    d = ImageDraw.Draw(img)
    inset = max(1, int(size * 0.014))
    d.rounded_rectangle(
        [inset, inset, size - 1 - inset, size - 1 - inset],
        radius=r - inset,
        outline=(196, 138, 22, 255),
        width=max(1, int(size * 0.018)),
    )

    inner = [int(size * 0.115), int(size * 0.185), int(size * 0.885), int(size * 0.815)]
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    ir = int(size * 0.115)
    dark = vertical_gradient(iw, ih, [(0.0, (44, 44, 44)), (0.4, (24, 24, 24)), (1.0, (14, 14, 14))])
    dl = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    dl.paste(dark, (0, 0), rounded_mask((iw, ih), ir))
    img.alpha_composite(dl, (inner[0], inner[1]))

    # 16px 时 "3D" 会糊成一团，改为单个 "3" 更易辨认
    text = "3" if size <= 24 else "3D"
    font = ImageFont.truetype(FONT_BOLD, int(size * (0.74 if text == "3" else 0.40)))
    font.set_variation_by_name("Black")
    txt = gradient_text(text, font, TEXT_GOLD_STOPS, spacing=0)
    if txt.width > iw * 0.88 or txt.height > ih * 0.86:
        ratio = iw * 0.86 / txt.width
        txt = txt.resize((int(txt.width * ratio), int(txt.height * ratio)), Image.LANCZOS)
    img.alpha_composite(txt, (inner[0] + (iw - txt.width) // 2, inner[1] + (ih - txt.height) // 2))
    return img


def make_og_cover(w=1200, h=630) -> Image.Image:
    """深色渐变的分享卡片：中间铭牌 logo + 一行卖点文案。"""
    bg = vertical_gradient(w, h, [(0.0, (26, 26, 26)), (0.55, (16, 16, 16)), (1.0, (8, 8, 8))]).convert("RGBA")

    # 中心柔光，避免整块死黑
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w * 0.12, -h * 0.15, w * 0.88, h * 0.85], fill=(90, 68, 20, 120))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))

    logo = Image.open(ROOT / "web" / "imgs" / "logo.png").convert("RGBA")
    lw = int(w * 0.52)
    logo = logo.resize((lw, round(lw * logo.height / logo.width)), Image.LANCZOS)
    bg.alpha_composite(logo, ((w - logo.width) // 2, int(h * 0.115)))

    font = ImageFont.truetype(FONT_REG, 44)
    font.set_variation_by_name("Medium")
    line = "免费 · 免安装 · Windows 多层立体扫雷"

    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    tw = tmp.textbbox((0, 0), line, font=font)[2]
    ty = int(h * 0.735)
    d = ImageDraw.Draw(bg)
    d.text(((w - tw) // 2, ty), line, font=font, fill=(238, 232, 218, 255))

    # 底部金色细线，呼应铭牌配色
    d.rounded_rectangle([w * 0.5 - 46, ty + 78, w * 0.5 + 46, ty + 82], radius=2, fill=(246, 194, 70, 255))
    return bg.convert("RGB")


def save_ico(path: Path, images) -> None:
    """手写多尺寸 ICO：每帧按目标尺寸单独渲染并 PNG 编码，避免缩放糊字。"""
    import io
    import struct

    pngs = []
    for im in images:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        pngs.append(buf.getvalue())

    n = len(images)
    header = struct.pack("<HHH", 0, 1, n)
    offset = 6 + 16 * n
    entries = b""
    payload = b""
    for im, png in zip(images, pngs):
        size = im.width
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
        payload += png
    path.write_bytes(header + entries + payload)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ico_sizes = [16, 32, 48, 64]
    save_ico(OUT_DIR / "favicon.ico", [make_icon(s) for s in ico_sizes])

    make_icon(192).save(OUT_DIR / "icon-192.png", optimize=True)
    make_icon(180).save(OUT_DIR / "apple-touch-icon.png", optimize=True)
    make_icon(512).save(OUT_DIR / "icon-512.png", optimize=True)
    make_og_cover().save(OUT_DIR / "og-cover.png", optimize=True)

    for f in ["favicon.ico", "icon-192.png", "apple-touch-icon.png", "icon-512.png", "og-cover.png"]:
        p = OUT_DIR / f
        print(f"{f:22s} {p.stat().st_size / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
