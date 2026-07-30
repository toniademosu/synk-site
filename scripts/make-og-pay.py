#!/usr/bin/env python3
"""
Generate assets/og-pay.png — the branded link-preview image for SYNK
payment links (used as OG_IMAGE_URL for /bill-join and /pay style pages).

Matches the house style established by og-card.png / og-card-v2.png:
dark ground, rose->orange glow bleeding from a corner, the coin mark +
wordmark top-left, a bold white headline, a grey subline, and the
synk.money domain tag bottom-left.

Usage: python3 scripts/make-og-pay.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

W, H = 1200, 630
MARGIN = 60

GROUND = (0x0C, 0x0D, 0x11)
ROSE = (0xF4, 0x3F, 0x5E)
ORANGE = (0xFB, 0x92, 0x3C)
GREY = (0x9C, 0xA3, 0xAF)
WHITE = (0xFF, 0xFF, 0xFF)

FONT_DIR = "/System/Library/Fonts/Supplemental"
BOLD_FONT = os.path.join(FONT_DIR, "Arial Bold.ttf")
REG_FONT = os.path.join(FONT_DIR, "Arial.ttf")


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_corner_glow(size=900, alpha_max=130):
    """Rose -> orange radial bloom, anchored so it bleeds from a corner
    of the tile. Built at low-res and upsampled for a smooth falloff."""
    n = 160
    grad = Image.new("RGB", (n, n))
    alpha = Image.new("L", (n, n))
    gpx = grad.load()
    apx = alpha.load()
    for y in range(n):
        for x in range(n):
            dx = x
            dy = (n - y)
            dist = math.sqrt(dx * dx + dy * dy) / n
            dist = min(dist, 1.0)
            t = x / n  # rose (left) -> orange (right) hue drift
            r = int(ROSE[0] * (1 - t) + ORANGE[0] * t)
            g = int(ROSE[1] * (1 - t) + ORANGE[1] * t)
            b = int(ROSE[2] * (1 - t) + ORANGE[2] * t)
            gpx[x, y] = (r, g, b)
            falloff = max(0.0, 1.0 - dist) ** 1.6
            apx[x, y] = int(falloff * alpha_max)
    grad.putalpha(alpha)
    grad = grad.resize((size, size), Image.LANCZOS)
    grad = grad.filter(ImageFilter.GaussianBlur(6))
    return grad


def text_size(draw, text, fnt):
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    return r - l, b - t, l, t


def main():
    img = Image.new("RGB", (W, H), GROUND)

    # --- glow, bleeding from the bottom-left corner ---
    glow = make_corner_glow(size=820, alpha_max=120)
    img = img.convert("RGBA")
    img.alpha_composite(glow, (-140, H - 820 + 170))

    draw = ImageDraw.Draw(img)

    # --- coin mark + wordmark, upper-left ---
    mark_size = 120
    mark = Image.open(os.path.join(ASSETS, "logo-mark.png")).convert("RGBA")
    mark = mark.resize((mark_size, mark_size), Image.LANCZOS)
    mark_x, mark_y = MARGIN, MARGIN
    img.alpha_composite(mark, (mark_x, mark_y))

    word_font = font(BOLD_FONT, 56)
    word_text = "Synk"
    ww, wh, wl, wt = text_size(draw, word_text, word_font)
    word_x = mark_x + mark_size + 24
    word_y = mark_y + (mark_size - wh) // 2 - wt
    draw.text((word_x, word_y), word_text, font=word_font, fill=WHITE)

    # --- headline ---
    headline_font = font(BOLD_FONT, 64)
    headline = "Split it. Settle it."
    hy = mark_y + mark_size + 56
    draw.text((MARGIN, hy), headline, font=headline_font, fill=WHITE)
    _, hh, _, ht = text_size(draw, headline, headline_font)

    # --- subline ---
    sub_font = font(REG_FONT, 32)
    subline = "Pay your share in the browser — no app needed."
    sy = hy + hh - ht + 30
    draw.text((MARGIN, sy), subline, font=sub_font, fill=GREY)

    # --- domain tag, bottom-left, matching og-card house style ---
    domain_font = font(BOLD_FONT, 30)
    domain = "synk.money"
    dw, dh, dl, dt = text_size(draw, domain, domain_font)
    dy = H - MARGIN - dh - dt
    draw.text((MARGIN, dy), domain, font=domain_font, fill=WHITE)

    out_path = os.path.join(ASSETS, "og-pay.png")
    img.convert("RGB").save(out_path, "PNG")
    print(f"wrote {out_path} ({W}x{H})")


if __name__ == "__main__":
    main()
