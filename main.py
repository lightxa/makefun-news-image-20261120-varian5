"""World Clock: Friday 20 November 2026 in one image.

A 24-hour clock dial. Eight verified stories of 20 November 2026 sit
at eight points of the dial, each with a short factual label, and the
date fills the top banner so it cannot be missed.

Pure Python standard library. No network, no randomness at run time
beyond a fixed-seed star field, so two runs write identical bytes.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# A small 5x7 pixel font, drawn from my own bitmaps. Uppercase only,
# plus digits and the punctuation the labels need.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


# ------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, thick, color):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = math.hypot(xx - cx, yy - cy)
                if r - thick <= d <= r + thick:
                    self.set(xx, yy, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            t = i / steps
            x = int(round(x0 + dx * t))
            y = int(round(y0 + dy * t))
            half = width // 2
            for oy in range(-half, half + 1):
                for ox in range(-half, half + 1):
                    self.set(x + ox, y + oy, color)

    def text(self, x, y, scale, color, text):
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(
                            cx + col * scale, y + row * scale, scale, scale, color
                        )
            cx += 6 * scale

    def text_center(self, cx, y, scale, color, text):
        self.text(cx - text_width(text, scale) // 2, y, scale, color, text)


def vgrad(canvas, top, bottom):
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            canvas.set(x, y, c)


# -------------------------------------------------------------- png out
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------ art
NAVY = (11, 30, 58)
NAVY2 = (19, 44, 82)
CREAM = (247, 243, 232)
INK = (27, 42, 74)
GOLD = (242, 193, 78)
WHITE = (232, 236, 242)
PANEL = (16, 31, 56)

CX, CY = 512, 540

# Eight verified stories of Friday 20 November 2026, clockwise from
# the top of the dial. Each entry: angle, colour, title, three lines.
STORIES = [
    (0, (215, 38, 61), "POLAND",
     ["RUSSIAN MISSILES", "LAND IN POLAND", "NATO: GRAVE BREACH"]),
    (45, (244, 96, 54), "UKRAINE",
     ["400+ DRONES AND", "111 MISSILES HIT", "KYIV. 8 KILLED"]),
    (90, (233, 180, 76), "MARKETS",
     ["S&P 500 -3.7%", "DOW IN CORRECTION", "NASDAQ -5.3%"]),
    (135, (176, 125, 43), "PERU",
     ["6.7 QUAKE SHAKES", "CENTRAL PERU,", "FELT IN LIMA"]),
    (180, (27, 154, 170), "MYANMAR",
     ["REJECTS ICJ", "GENOCIDE RULING", "DAY AFTER VERDICT"]),
    (225, (123, 44, 191), "RIYADH",
     ["DEFENCES DOWN 4", "HOUTHI MISSILES", "DAY AFTER PIF HIT"]),
    (270, (46, 111, 219), "SUMMIT",
     ["TRUMP, XI, PUTIN", "MEET IN SHENZHEN", "US-CHINA AI PACT"]),
    (315, (47, 163, 107), "MERCURY",
     ["BEPICOLOMBO NEARS", "MERCURY AFTER 8", "YEARS. DUE 21 NOV"]),
]


def point(angle_deg, r):
    a = math.radians(angle_deg)
    return (int(round(CX + r * math.sin(a))), int(round(CY - r * math.cos(a))))


def stars(canvas):
    state = 20261120
    for _ in range(110):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        x = state % W
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        y = state % 300
        if y > 130 and math.hypot(x - CX, y - CY) > 300:
            canvas.set(x, y, (70, 100, 140))
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        x2 = state % W
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        y2 = 700 + state % 300
        if math.hypot(x2 - CX, y2 - CY) > 300:
            canvas.set(x2, y2, (70, 100, 140))


def dial(canvas):
    canvas.disc(CX, CY, 262, GOLD)
    canvas.disc(CX, CY, 252, CREAM)
    for m in range(60):
        a = math.radians(m * 6)
        major = m % 5 == 0
        r0 = 238 if major else 244
        x0 = int(round(CX + r0 * math.sin(a)))
        y0 = int(round(CY - r0 * math.cos(a)))
        x1 = int(round(CX + 252 * math.sin(a)))
        y1 = int(round(CY - 252 * math.cos(a)))
        canvas.line(x0, y0, x1, y1, INK, 2 if major else 1)
    for h in range(1, 13):
        x, y = point(h * 30, 195)
        canvas.text_center(x, y - 10, 3, INK, str(h))
    for angle, color, _title, _lines in STORIES:
        x, y = point(angle, 224)
        canvas.disc(x, y, 16, WHITE)
        canvas.disc(x, y, 13, color)
    # Hands at 7:09, the local time of the Peru quake.
    ha = math.radians(217.5)
    ma = math.radians(54)
    canvas.line(CX, CY,
                int(round(CX + 140 * math.sin(ha))),
                int(round(CY - 140 * math.cos(ha))), INK, 9)
    canvas.line(CX, CY,
                int(round(CX + 180 * math.sin(ma))),
                int(round(CY - 180 * math.cos(ma))), INK, 6)
    canvas.disc(CX, CY, 85, (20, 38, 63))
    canvas.ring(CX, CY, 85, 2, GOLD)
    canvas.text_center(CX, CY - 42, 7, GOLD, "20")
    canvas.text_center(CX, CY + 18, 3, WHITE, "NOV")
    canvas.text_center(CX, CY + 44, 2, GOLD, "2026")


def label(canvas, angle, color, title, lines):
    bx, by = point(angle, 382)
    x0, y0 = bx - 120, by - 44
    canvas.rect(x0, y0, 240, 88, PANEL)
    canvas.rect(x0, y0, 240, 2, color)
    canvas.rect(x0, y0 + 86, 240, 2, color)
    canvas.rect(x0, y0, 2, 88, color)
    canvas.rect(x0 + 238, y0, 2, 88, color)
    canvas.rect(x0, y0, 8, 88, color)
    canvas.text(x0 + 18, y0 + 10, 3, color, title)
    for i, line in enumerate(lines):
        canvas.text(x0 + 18, y0 + 38 + i * 16, 2, WHITE, line)


def build():
    c = Canvas(W, H)
    vgrad(c, NAVY, NAVY2)
    stars(c)
    c.text_center(512, 20, 5, GOLD, "FRIDAY 20 NOVEMBER 2026")
    c.text_center(512, 74, 2, WHITE, "24 HOURS, 8 STORIES, EVERY REGION")
    dial(c)
    for angle, color, title, lines in STORIES:
        x0, y0 = point(angle, 262)
        x1, y1 = point(angle, 368)
        c.line(x0, y0, x1, y1, color, 3)
    for angle, color, title, lines in STORIES:
        label(c, angle, color, title, lines)
    c.text_center(512, 972, 2, GOLD,
                  "ALSO TODAY: COP31 CLIMATE TALKS STALL IN ANTALYA")
    c.text_center(512, 994, 2, WHITE,
                  "UK-EU DEALS SIGNED. NIKKEI -5.1%")
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(build(), path)
    print("wrote", path, size, "bytes")


if __name__ == "__main__":
    main()
