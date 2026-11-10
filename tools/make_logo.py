"""生成 3D 扫雷品牌图标（GFPGAN 风格金色铭牌）。

用法：
    python tools/make_logo.py
输出：
    web/imgs/logo.png   1520x772（2x，README 中以 width=440 显示）

设计要点：
- 外层金色金属渐变圆角牌 + 内嵌深色圆角条
- 主字样「3D扫雷」金色渐变粗黑体（Noto Sans SC Black）
- 副标题「MINESWEEPER」黑色衬线 + 宽字距（Georgia），呼应 GFPGAN 的 FACE RESTORATION
- 全部 2x 绘制后不缩放，保证 GitHub 上 Retina 屏清晰
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "imgs" / "logo.png"

W, H = 1520, 772
S = 1.0  # 已经按 2x 尺寸设计

FONT_BOLD = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
FONT_SERIF = r"C:\Windows\Fonts\georgia.ttf"


def vertical_gradient(w: int, h: int, stops) -> Image.Image:
    """按 [(位置0-1, (r,g,b)), ...] 生成竖直渐变图。"""
    ys = np.linspace(0.0, 1.0, h)
    pos = [s[0] for s in stops]
    chans = [np.interp(ys, pos, [s[1][c] for s in stops]) for c in range(3)]
    arr = np.stack(chans, axis=1).astype(np.uint8)[:, None, :]
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr, mode="RGB")


def rounded_mask(size, radius) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def gradient_text(text, font, fill_gradient, spacing=0):
    """用渐变填充文字：先算文字蒙版，再用渐变图着色。"""
    tmp = Image.new("L", (10, 10))
    d = ImageDraw.Draw(tmp)
    widths = []
    for ch in text:
        box = d.textbbox((0, 0), ch, font=font)
        widths.append(box[2] - box[0])
    total = sum(widths) + spacing * (len(text) - 1)

    ascent, descent = font.getmetrics()
    height = ascent + descent
    mask = Image.new("L", (int(total) + 8, height + 8), 0)
    md = ImageDraw.Draw(mask)
    x = 4
    for ch, w in zip(text, widths):
        # 逐字符绘制以获得自定义字距
        box = md.textbbox((0, 0), ch, font=font)
        md.text((x - box[0], 4), ch, font=font, fill=255)
        x += w + spacing

    # 渐变按蒙版文字实际高度展开
    grad = vertical_gradient(mask.width, mask.height, fill_gradient)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def main() -> None:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # ---------- 1. 金色铭牌底板 ----------
    plate_radius = 64
    plate_box = [10, 10, W - 10, H - 10]
    pw, ph = plate_box[2] - plate_box[0], plate_box[3] - plate_box[1]

    gold = vertical_gradient(
        pw,
        ph,
        [
            (0.00, (255, 253, 235)),
            (0.12, (255, 240, 178)),
            (0.30, (253, 212, 96)),
            (0.55, (247, 189, 55)),
            (0.78, (252, 206, 88)),
            (1.00, (255, 233, 165)),
        ],
    )

    # 投影
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [plate_box[0], plate_box[1] + 10, plate_box[2], plate_box[3] + 10],
        radius=plate_radius,
        fill=(120, 84, 10, 90),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))

    plate = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    plate.paste(gold, (0, 0), rounded_mask((pw, ph), plate_radius))
    canvas.alpha_composite(plate, (plate_box[0], plate_box[1]))

    draw = ImageDraw.Draw(canvas)

    # 外描边（深金）+ 内高光（白）
    draw.rounded_rectangle(plate_box, radius=plate_radius, outline=(196, 138, 22, 255), width=4)
    draw.rounded_rectangle(
        [plate_box[0] + 8, plate_box[1] + 8, plate_box[2] - 8, plate_box[3] - 8],
        radius=plate_radius - 6,
        outline=(255, 252, 232, 170),
        width=4,
    )

    # ---------- 2. 内嵌深色条 ----------
    inner = [84, 86, W - 84, 482]
    iw, ih = inner[2] - inner[0], inner[3] - inner[1]
    inner_radius = 40

    inner_shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner_shadow).rounded_rectangle(
        [inner[0], inner[1] + 6, inner[2], inner[3] + 8], radius=inner_radius, fill=(90, 60, 0, 110)
    )
    canvas.alpha_composite(inner_shadow.filter(ImageFilter.GaussianBlur(10)))

    dark = vertical_gradient(iw, ih, [(0.0, (44, 44, 44)), (0.35, (26, 26, 26)), (1.0, (16, 16, 16))])
    dark_layer = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    dark_layer.paste(dark, (0, 0), rounded_mask((iw, ih), inner_radius))
    canvas.alpha_composite(dark_layer, (inner[0], inner[1]))

    draw.rounded_rectangle(inner, radius=inner_radius, outline=(0, 0, 0, 200), width=3)

    # ---------- 3. 主字样 3D扫雷 ----------
    title_font = ImageFont.truetype(FONT_BOLD, 288)
    title_font.set_variation_by_name("Black")
    title = gradient_text(
        "3D扫雷",
        title_font,
        [(0.00, (255, 235, 150)), (0.30, (255, 204, 62)), (0.70, (247, 173, 30)), (1.00, (255, 214, 90))],
        spacing=2,
    )
    title = title.crop(title.getbbox())  # 去掉字形留白，按实际墨迹居中
    tx = inner[0] + (iw - title.width) // 2
    ty = inner[1] + (ih - title.height) // 2
    canvas.alpha_composite(title, (tx, ty))

    # ---------- 4. 副标题 MINESWEEPER ----------
    sub_font = ImageFont.truetype(FONT_SERIF, 104)
    sub = gradient_text("MINESWEEPER", sub_font, [(0.0, (28, 28, 28)), (1.0, (28, 28, 28))], spacing=10)

    # 衬线 + 宽字距，呼应参考图的 FACE RESTORATION
    sub = sub.crop(sub.getbbox())
    sx = (W - sub.width) // 2
    sy = (H - 10) - 52 - sub.height  # 底边留白与参考图一致
    canvas.alpha_composite(sub, (sx, sy))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, optimize=True)
    print(f"saved {OUT} {canvas.size}, {OUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
