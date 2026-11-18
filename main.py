#!/usr/bin/env python3
"""Draw Tuesday 17 November 2026's world news as one front-page poster image.

Pure Python 3.13 standard library: no network, no clock, no randomness, so
every run writes byte-identical PNG output to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png when set).

The poster is a newspaper front page: a masthead naming the day, one lead
story (Ukraine's second strike on the Kerch Bridge), four more stories from
four regions/beats, and an "also today" strip - all events first reported on
Tuesday 17 November 2026, as reported by BBC, Reuters, Al Jazeera, AP, CNN.
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)   # warm newsprint
CARD = (255, 253, 248)    # story card white
INK = (22, 21, 19)        # headline ink
NAVY = (22, 35, 63)       # masthead / footer band
NAVY_LT = (38, 54, 88)
GOLD = (217, 164, 65)     # masthead date
RED = (179, 39, 30)       # accent / lead rule
BLUE = (46, 90, 136)      # links of water / story accents
TEAL = (31, 122, 107)
GRAY = (107, 101, 92)     # secondary text
LINE = (201, 193, 176)    # hairlines
ORANGE = (214, 106, 24)   # explosion
SMOKE = (120, 118, 112)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 bits, '#' = ink. Uppercase only; all copy is
# written in capitals, which suits a newspaper poster.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    ';': ("00000", "01100", "00000", "01100", "00000", "00100", "01000"),
    ':': ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per char)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.px[o:o + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.px[o:o + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square thickness t."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        half = t // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if (r - 1) ** 2 <= d2 <= r * r:
                        self.set(xx, yy, color)

    def triangle(self, p0, p1, p2, color):
        """Filled triangle via scanline fill."""
        pts = sorted([p0, p1, p2], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            t1 = (y - ay) / (cy - ay) if cy != ay else 0
            x_left = ax + (cx - ax) * t1
            if y < by:
                t2 = (y - ay) / (by - ay) if by != ay else 0
                x_right = ax + (bx - ax) * t2
            else:
                t2 = (y - by) / (cy - by) if cy != by else 0
                x_right = bx + (cx - bx) * t2
            xa, xb = sorted([int(round(x_left)), int(round(x_right))])
            self.fill_rect(xa, y, xb - xa + 1, 1, color)

    def star(self, cx, cy, r_out, r_in, points, color):
        """Spiky starburst polygon (explosion)."""
        import math
        verts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points - math.pi / 2
            verts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
        for i in range(1, len(verts) - 1):
            self.triangle(verts[0], verts[i], verts[i + 1], color)

    # ------------------------------------------------------------ text
    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT['?']
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '1':
                    self.fill_rect(x + rx * scale, y + ry * scale,
                                   scale, scale, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        for ch in s:
            self.glyph(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_center(self, cx, y, s, scale, color):
        x = cx - text_width(s.upper(), scale) // 2
        return self.text(x, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, leading=None):
        """Wrapped paragraph; returns y just below the last line."""
        lh = leading if leading is not None else 7 * scale + 4
        for line in wrap_text(s, scale, max_width):
            self.text(x, y, line, scale, color)
            y += lh
        return y


# --------------------------------------------------------------------- PNG
def encode_png(canvas):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


# ------------------------------------------------------------------- icons
# Small flat pictograms, drawn with the same primitives as the text.

def draw_bridge(cv, x, y, w, h):
    """Kerch Bridge: two towers, deck, a broken middle span, smoke."""
    deck_y = y + int(h * 0.52)
    # water
    cv.fill_rect(x, deck_y + 46, w, h - (deck_y + 46) - y, (214, 228, 238))
    for i, wy in enumerate((deck_y + 62, deck_y + 78, deck_y + 94)):
        cv.line(x + 8 + i * 30, wy, x + 60 + i * 30, wy, BLUE, 3)
        cv.line(x + w - 70 - i * 30, wy, x + w - 18 - i * 30, wy, BLUE, 3)
    # towers
    for tx in (x + 34, x + w - 58):
        cv.fill_rect(tx, y + 26, 24, deck_y - y - 26 + 8, NAVY)
        cv.fill_rect(tx - 4, y + 18, 32, 10, NAVY)
    # deck: left and right spans, broken gap in the middle
    gap = 64
    mid = x + w // 2
    cv.fill_rect(x + 6, deck_y, mid - x - gap // 2 - 6, 12, INK)
    cv.fill_rect(mid + gap // 2, deck_y, x + w - 6 - (mid + gap // 2), 12, INK)
    # jagged broken ends
    cv.triangle((mid - gap // 2 - 6, deck_y), (mid - gap // 2 + 8, deck_y),
                (mid - gap // 2 - 2, deck_y + 26), INK)
    cv.triangle((mid + gap // 2 + 6, deck_y), (mid + gap // 2 - 8, deck_y),
                (mid + gap // 2 + 2, deck_y + 26), INK)
    # cables
    cv.line(x + 46, y + 26, x + 10, deck_y, GRAY, 2)
    cv.line(x + 46, y + 26, mid - gap // 2 - 6, deck_y, GRAY, 2)
    cv.line(x + w - 46, y + 26, mid + gap // 2 + 6, deck_y, GRAY, 2)
    cv.line(x + w - 46, y + 26, x + w - 10, deck_y, GRAY, 2)
    # smoke puffs above the gap
    for sx, sy, sr in ((mid - 30, y + 22, 15), (mid + 2, y + 10, 19),
                       (mid + 32, y + 26, 13)):
        cv.circle(sx, sy, sr, SMOKE)
        cv.circle(sx - 5, sy - 4, sr - 7, (150, 148, 142))
    # explosion starburst at the break
    cv.star(mid, deck_y - 6, 36, 15, 8, ORANGE)
    cv.star(mid, deck_y - 6, 19, 8, 8, RED)
    cv.circle(mid, deck_y - 6, 7, (255, 214, 90))


def draw_drone_radar(cv, x, y, w, h):
    """Quadcopter drone over radar arcs."""
    cx, cy = x + w // 2, y + h // 2 - 8
    # radar arcs
    for r in (52, 40, 28):
        cv.circle(cx, cy + 46, r, TEAL, fill=False)
    cv.line(cx, cy + 46, cx + 44, cy + 8, TEAL, 2)
    cv.circle(cx, cy + 46, 4, RED)
    # drone body
    cv.fill_rect(cx - 16, cy - 8, 32, 14, INK)
    cv.fill_rect(cx - 6, cy - 12, 12, 6, INK)
    for dx, dy in ((-26, -16), (26, -16), (-26, 10), (26, 10)):
        cv.line(cx, cy, cx + dx, cy + dy, INK, 3)
        cv.circle(cx + dx, cy + dy, 9, INK, fill=False)
        cv.line(cx + dx - 12, cy + dy, cx + dx + 12, cy + dy, INK, 2)
    cv.circle(cx, cy - 1, 4, RED)


def draw_flags(cv, x, y, w, h):
    """Three flags on poles: United States, China, Russia."""
    pole_y0, pole_y1 = y + 6, y + h - 8
    flags = [
        ("US", (x + 2, y + 16)),
        ("CN", (x + 35, y + 10)),
        ("RU", (x + 68, y + 16)),
    ]
    for name, (fx, fy) in flags:
        fw, fh = 30, 20
        cv.line(fx - 2, pole_y0, fx - 2, pole_y1, INK, 3)
        if name == "US":
            for i in range(5):
                cv.fill_rect(fx, fy + i * 4, fw, 4,
                             RED if i % 2 == 0 else WHITE)
            cv.fill_rect(fx, fy, 13, 11, NAVY)
            for sx in (3, 8):
                for sy in (3, 8):
                    cv.circle(fx + sx, fy + sy, 1, WHITE)
        elif name == "CN":
            cv.fill_rect(fx, fy, fw, fh, RED)
            cv.star(fx + 7, fy + 7, 5, 2, 5, GOLD)
            for sx, sy in ((18, 4), (23, 7), (23, 12), (18, 15)):
                cv.circle(fx + sx, fy + sy, 1, GOLD)
        else:
            cv.fill_rect(fx, fy, fw, 7, WHITE)
            cv.fill_rect(fx, fy + 7, fw, 6, BLUE)
            cv.fill_rect(fx, fy + 13, fw, 7, RED)
        cv.rect(fx, fy, fw, fh, INK, 1)
    cv.fill_rect(x, pole_y1, w, 3, INK)


def draw_jet(cv, x, y, w, h):
    """Fighter jet in profile, climbing."""
    cx, cy = x + w // 2, y + h // 2
    # fuselage
    cv.triangle((cx - 52, cy + 6), (cx + 54, cy - 14), (cx + 54, cy - 4),
                NAVY)
    cv.triangle((cx - 52, cy + 6), (cx - 30, cy + 16), (cx + 54, cy - 4),
                NAVY)
    # nose tip
    cv.triangle((cx + 54, cy - 14), (cx + 66, cy - 8), (cx + 54, cy - 4),
                RED)
    # main wing
    cv.triangle((cx - 6, cy - 6), (cx + 10, cy - 6), (cx - 34, cy + 34),
                NAVY_LT)
    cv.triangle((cx - 6, cy - 6), (cx - 34, cy + 34), (cx - 44, cy + 34),
                NAVY_LT)
    # tail fin
    cv.triangle((cx - 34, cy - 2), (cx - 20, cy - 2), (cx - 44, cy - 30),
                NAVY_LT)
    # cockpit
    cv.circle(cx + 34, cy - 10, 5, (180, 210, 235))
    # roundel
    cv.circle(cx - 2, cy + 2, 7, WHITE)
    cv.circle(cx - 2, cy + 2, 5, RED)
    # speed lines
    for i, ly in enumerate((cy + 26, cy + 34, cy + 42)):
        cv.line(cx - 62, ly, cx - 62 + 26 - i * 6, ly, GRAY, 2)


def draw_document_seal(cv, x, y, w, h):
    """Sanctions order: a document with a red seal."""
    dx, dy, dw, dh = x + 12, y + 8, w - 24, h - 16
    cv.fill_rect(dx, dy, dw, dh, WHITE)
    cv.rect(dx, dy, dw, dh, INK, 2)
    # folded corner
    cv.triangle((dx + dw - 16, dy), (dx + dw, dy + 16), (dx + dw, dy),
                LINE)
    # text lines
    for i in range(4):
        cv.fill_rect(dx + 10, dy + 14 + i * 12, dw - 20 - i * 8, 4, GRAY)
    # red seal with ribbon
    sx, sy = dx + dw - 26, dy + dh - 26
    cv.line(sx - 8, sy + 12, sx - 16, sy + 30, RED, 4)
    cv.line(sx + 8, sy + 12, sx + 16, sy + 30, RED, 4)
    cv.circle(sx, sy, 16, RED)
    cv.circle(sx, sy, 11, WHITE, fill=False)
    cv.text(sx - 9, sy - 10, "$", 3, RED)


def draw_globe(cv, cx, cy, r):
    """Small globe for the masthead: circle, meridians, land blobs."""
    cv.circle(cx, cy, r, GOLD, fill=False)
    cv.circle(cx, cy, r - 2, GOLD, fill=False)
    # meridians: vertical chords of the circle
    for dx in (-r // 2, 0, r // 2):
        half = int((r * r - dx * dx) ** 0.5)
        cv.line(cx + dx, cy - half, cx + dx, cy + half, GOLD, 1)
    cv.line(cx - r, cy, cx + r, cy, GOLD, 1)
    # land blobs
    cv.circle(cx - r // 3, cy - r // 4, r // 4, GOLD)
    cv.circle(cx + r // 3, cy + r // 5, r // 5, GOLD)
    cv.circle(cx + r // 4, cy - r // 2, r // 6, GOLD)


# ------------------------------------------------------------------ poster
def draw_card(cv, x0, y0, accent, tag, headline, body, icon):
    cv.fill_rect(x0, y0, 488, 196, CARD)
    cv.rect(x0, y0, 488, 196, LINE, 1)
    cv.fill_rect(x0, y0, 488, 6, accent)
    icon(cv, x0 + 10, y0 + 46, 100, 110)
    tx = x0 + 122
    tw = 488 - 122 - 14
    cv.text(tx, y0 + 16, tag, 2, accent)
    y = cv.para(tx, y0 + 38, headline, 3, INK, tw, leading=25)
    cv.para(tx, y0 + 118, body, 2, GRAY, tw, leading=18)


def draw_poster():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ---------------------------------------------------
    cv.fill_rect(0, 0, W, 116, NAVY)
    draw_globe(cv, 62, 58, 34)
    cv.text_center(560, 16, "THE WORLD IN ONE IMAGE", 6, WHITE)
    cv.text_center(560, 70, "TUESDAY 17 NOVEMBER 2026", 3, GOLD)
    cv.fill_rect(0, 116, W, 4, RED)

    # ---- lead story: Kerch Bridge -----------------------------------
    cv.text(36, 138, "LEAD STORY - EUROPE", 2, RED)
    cv.text(36, 164, "UKRAINE STRIKES", 4, INK)
    cv.text(36, 198, "KERCH BRIDGE AGAIN", 4, INK)
    cv.fill_rect(36, 234, 200, 4, RED)
    cv.para(36, 250, "ROAD SPAN COLLAPSES IN A SECOND STRIKE IN TWO "
           "DAYS. KYIV SAYS THE OPERATION TOOK WEEKS TO PLAN; MOSCOW "
           "VOWS TO REBUILD - AND HITS BRIDGES IN KYIV IN REPLY.",
           2, INK, 600, leading=19)
    cv.rect(36, 330, 600, 42, LINE, 1)
    cv.fill_rect(36, 330, 6, 42, RED)
    cv.text(52, 343, "ZELENSKYY HAILS 'AN UNPRECEDENTED OPERATION'", 2,
            NAVY)
    draw_bridge(cv, 680, 128, 312, 252)
    cv.text_center(836, 388, "THE KERCH BRIDGE, HIT", 2, GRAY)
    cv.text_center(836, 406, "FOR A SECOND DAY RUNNING", 2, GRAY)

    # ---- four more stories ------------------------------------------
    draw_card(cv, 16, 440, RED, "MIDDLE EAST - IRAN",
              "IRAN FIRES DRONES AT U.S. RADAR BASE IN BAHRAIN",
              "TEHRAN SAYS IT HIT THE SHEIKH ISA BASE. BAHRAIN: "
              "INTERCEPTED, NO CASUALTIES.",
              draw_drone_radar)
    draw_card(cv, 520, 440, BLUE, "ASIA - DIPLOMACY",
              "TRUMP IN MANILA; THREE-WAY SUMMIT SET FOR THURSDAY",
              "CHINA CONFIRMS XI, TRUMP AND PUTIN WILL MEET IN "
              "SHENZHEN ON THURSDAY.",
              draw_flags)
    draw_card(cv, 16, 648, TEAL, "ASIA-PACIFIC - SECURITY",
              "JAPAN SCRAMBLES JETS AFTER RUSSIAN AIRSPACE INCURSION",
              "TOKYO PROTESTS AFTER TWO SUSPECTED RUSSIAN AIRCRAFT "
              "CROSS IN.",
              draw_jet)
    draw_card(cv, 520, 648, NAVY, "MIDDLE EAST - GAZA",
              "UK SANCTIONS FIRMS BUILDING ISRAELI SETTLEMENTS",
              "EIGHT BUILDERS HIT; ALLIES URGE ISRAEL TO OPEN GAZA "
              "AID CROSSINGS.",
              draw_document_seal)

    # ---- also today ---------------------------------------------------
    cv.text(16, 858, "ALSO TODAY", 3, RED)
    cv.fill_rect(16, 884, 992, 2, LINE)
    items = [
        "ESTONIA TO SHUT ITS RUSSIA BORDER CROSSINGS FROM 1 DEC AFTER "
        "A FOILED PLOT TO BOMB A DRONE PLANT",
        "HOUTHI ADVANCE PUSHES YEMEN'S GOVERNMENT FORCES BACK "
        "TOWARD ADEN",
        "JPMORGAN BLAMES A SOFTWARE BUG, NOT HACKERS, FOR MONDAY'S "
        "BANKING OUTAGE",
    ]
    y = 890
    for item in items:
        for line in wrap_text(item, 2, 960):
            cv.fill_rect(16, y + 4, 8, 8, RED)
            cv.text(36, y, line, 2, INK)
            y += 17

    # ---- footer -------------------------------------------------------
    cv.fill_rect(0, 960, W, 64, NAVY)
    cv.text_center(512, 972, "ALL STORIES FIRST REPORTED TUESDAY "
                   "17 NOVEMBER 2026", 2, WHITE)
    cv.text_center(512, 996, "SOURCES: BBC - REUTERS - AL JAZEERA - "
                   "AP - CNN", 2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(draw_poster())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
