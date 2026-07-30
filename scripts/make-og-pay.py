#!/usr/bin/env python3
"""
Generate assets/og-pay.png — the branded link-preview image for SYNK
payment links (used as OG_IMAGE_URL for /bill-join and /pay style pages).

Matches the house style established by og-card.png / og-card-v2.png:
dark ground, rose->orange glow bleeding from a corner, the coin mark +
wordmark top-left, a bold white headline, a grey subline, and the
synk.money domain tag bottom-left — plus (to mirror how og-card-v2
shows the pool UI) a small "share row" product card on the right that
shows what a pay link actually looks like: a name, an amount, and a
gradient Pay pill.

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
CARD_BG = (0x15, 0x16, 0x1C)
CARD_BORDER = (0x26, 0x27, 0x2E)

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


def linear_gradient(w, h, c0, c1, horizontal=True):
    """Solid rose->orange linear gradient, opaque, size (w, h)."""
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    for x in range(w):
        r = g = b = 0
        if horizontal:
            t = x / max(1, w - 1)
            r = int(c0[0] * (1 - t) + c1[0] * t)
            g = int(c0[1] * (1 - t) + c1[1] * t)
            b = int(c0[2] * (1 - t) + c1[2] * t)
        for y in range(h):
            if not horizontal:
                t2 = y / max(1, h - 1)
                r = int(c0[0] * (1 - t2) + c1[0] * t2)
                g = int(c0[1] * (1 - t2) + c1[1] * t2)
                b = int(c0[2] * (1 - t2) + c1[2] * t2)
            px[x, y] = (r, g, b)
    return grad


def rounded_mask(w, h, radius):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    return mask


def gradient_pill(w, h, radius):
    grad = linear_gradient(w, h, ROSE, ORANGE, horizontal=True).convert("RGBA")
    grad.putalpha(rounded_mask(w, h, radius))
    return grad


def gradient_circle(diameter):
    grad = linear_gradient(diameter, diameter, ROSE, ORANGE, horizontal=False).convert("RGBA")
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, diameter - 1, diameter - 1], fill=255)
    grad.putalpha(mask)
    return grad


def text_size(draw, text, fnt):
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    return r - l, b - t, l, t


def draw_centered_text(draw, cx, cy, text, fnt, fill):
    w, h, l, t = text_size(draw, text, fnt)
    draw.text((cx - w / 2 - l, cy - h / 2 - t), text, font=fnt, fill=fill)


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
    hy = mark_y + mark_size + 64
    draw.text((MARGIN, hy), headline, font=headline_font, fill=WHITE)
    _, hh, _, ht = text_size(draw, headline, headline_font)

    # --- subline (wrapped to two lines so it doesn't run under the card) ---
    sub_font = font(REG_FONT, 32)
    subline_1 = "Pay your share in the browser —"
    subline_2 = "no app needed."
    sy = hy + hh - ht + 34
    draw.text((MARGIN, sy), subline_1, font=sub_font, fill=GREY)
    _, sh1, _, st1 = text_size(draw, subline_1, sub_font)
    sy2 = sy + sh1 - st1 + 14
    draw.text((MARGIN, sy2), subline_2, font=sub_font, fill=GREY)

    # --- domain tag, bottom-left, matching og-card house style ---
    domain_font = font(BOLD_FONT, 30)
    domain = "synk.money"
    dw, dh, dl, dt = text_size(draw, domain, domain_font)
    dy = H - MARGIN - dh - dt
    draw.text((MARGIN, dy), domain, font=domain_font, fill=WHITE)

    # ================= product-anchor card, right side =================
    # A small "share row" mock — this is what a real synk.money/pay link
    # looks like: who it's for, what they owe, and the pill to pay it.
    card_w, card_h = 400, 268
    card_x2 = W - MARGIN
    card_x1 = card_x2 - card_w
    card_cy = H // 2
    card_y1 = card_cy - card_h // 2
    card_y2 = card_y1 + card_h
    radius = 20
    pad = 32

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(card)
    cdraw.rounded_rectangle(
        [0, 0, card_w - 1, card_h - 1], radius=radius, fill=(*CARD_BG, 255)
    )
    cdraw.rounded_rectangle(
        [0, 0, card_w - 1, card_h - 1], radius=radius, outline=(*CARD_BORDER, 255), width=2
    )

    # Avatar + name/status row
    avatar_d = 64
    avatar = gradient_circle(avatar_d)
    card.alpha_composite(avatar, (pad, pad))
    initials_font = font(BOLD_FONT, 24)
    draw_centered_text(
        cdraw, pad + avatar_d / 2, pad + avatar_d / 2, "DA", initials_font, WHITE
    )

    name_font = font(BOLD_FONT, 30)
    name_x = pad + avatar_d + 20
    cdraw.text((name_x, pad - 2), "Daniella", font=name_font, fill=WHITE)
    status_font = font(REG_FONT, 20)
    cdraw.text((name_x, pad + 34), "requests a payment", font=status_font, fill=GREY)

    # Divider
    div_y = pad + avatar_d + 28
    cdraw.line([(pad, div_y), (card_w - pad, div_y)], fill=CARD_BORDER, width=2)

    # Amount label + value
    label_font = font(BOLD_FONT, 16)
    label_y = div_y + 24
    cdraw.text((pad, label_y), "AMOUNT DUE", font=label_font, fill=GREY)

    amount_font = font(BOLD_FONT, 52)
    amount_y = label_y + 22
    cdraw.text((pad, amount_y), "$41.75", font=amount_font, fill=WHITE)

    # Pay pill, bottom-right of the card, gradient rose -> orange
    pill_w, pill_h = 128, 56
    pill_x1 = card_w - pad - pill_w
    pill_y1 = card_h - pad - pill_h
    pill = gradient_pill(pill_w, pill_h, radius=pill_h // 2)
    card.alpha_composite(pill, (pill_x1, pill_y1))
    pay_font = font(BOLD_FONT, 26)
    draw_centered_text(
        cdraw,
        pill_x1 + pill_w / 2,
        pill_y1 + pill_h / 2,
        "Pay",
        pay_font,
        WHITE,
    )

    img.alpha_composite(card, (card_x1, card_y1))

    out_path = os.path.join(ASSETS, "og-pay.png")
    img.convert("RGB").save(out_path, "PNG")
    print(f"wrote {out_path} ({W}x{H})")


if __name__ == "__main__":
    main()
