"""The Daily Sum -- Sunday 22 November 2026 world news in one image.

A procedural newspaper front page drawn with the Python standard
library only. Every pixel is computed in this file: a hand-written
3-by-5 pixel font, small geometric pictograms for each story, and a
hand-rolled PNG encoder built on zlib and struct. The program writes
exactly one file, entry.png, into MAKEFUN_OUTPUT_DIR. The output is
deterministic: two runs write byte-identical files.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (250, 244, 230)
INK = (20, 20, 24)
NAVY = (18, 38, 74)
RED = (178, 34, 34)
TEAL = (14, 110, 110)
GOLD = (186, 138, 38)
GREY = (104, 104, 100)
LIGHT = (238, 231, 216)
SKY = (132, 186, 222)
GREEN = (36, 118, 62)
WHITE = (255, 255, 255)

# A 3 by 5 pixel font, drawn by hand. Each glyph is five rows of three
# cells; '#' is ink and '.' is empty. Lowercase maps to capitals.
FONT = {
    "A": (".#.", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": (".##", "#..", "#..", "#..", ".##"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": (".##", "#..", "#.#", "#.#", ".##"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", ".#."),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("#.#", "###", "#.#", "#.#", "#.#"),
    "O": (".#.", "#.#", "#.#", "#.#", ".#."),
    "P": ("##.", "#.#", "##.", "#..", "#.."),
    "Q": (".#.", "#.#", "#.#", "##.", "..#"),
    "R": ("##.", "#.#", "##.", "#.#", "#.#"),
    "S": (".##", "#..", ".#.", "..#", "##."),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "0": (".#.", "#.#", "#.#", "#.#", ".#."),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("##.", "..#", ".#.", "#..", "###"),
    "3": ("##.", "..#", ".#.", "..#", "##."),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "##.", "..#", "##."),
    "6": (".##", "#..", "##.", "#.#", ".#."),
    "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": (".#.", "#.#", ".#.", "#.#", ".#."),
    "9": (".#.", "#.#", ".##", "..#", "##."),
    ".": ("...", "...", "...", "...", ".#."),
    ",": ("...", "...", "...", ".#.", "#.."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    ";": ("...", ".#.", "...", ".#.", "#.."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    "?": ("##.", "..#", ".#.", "...", ".#."),
    "-": ("...", "...", "###", "...", "..."),
    "'": (".#.", ".#.", "...", "...", "..."),
    '"': ("#.#", "#.#", "...", "...", "..."),
    "(": ("..#", ".#.", ".#.", ".#.", "..#"),
    ")": ("#..", ".#.", ".#.", ".#.", "#.."),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    "&": (".#.", "#.#", ".#.", "#.#", ".##"),
    "%": ("#.#", "..#", ".#.", "#..", "#.#"),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "$": (".#.", "###", ".#.", "###", ".#."),
    "=": ("...", "###", "...", "###", "..."),
    "*": ("...", "#.#", ".#.", "#.#", "..."),
    " ": ("...", "...", "...", "...", "..."),
}


def text_width(text, scale):
    """Width in pixels of text drawn at the given scale."""
    return len(text) * 4 * scale - scale


def draw_glyph(canvas, x, y, glyph, scale, color):
    """Draw one 3x5 glyph with its top-left corner at (x, y)."""
    for row in range(5):
        bits = glyph[row]
        for col in range(3):
            if bits[col] == "#":
                fill_rect(canvas, x + col * scale, y + row * scale,
                          scale, scale, color)


def draw_text(canvas, x, y, text, scale, color):
    """Draw text left-aligned; returns the x just past the last glyph."""
    cursor = x
    for ch in text:
        glyph = FONT.get(ch.upper(), FONT[" "])
        draw_glyph(canvas, cursor, y, glyph, scale, color)
        cursor += 4 * scale
    return cursor


def draw_text_centered(canvas, cx, y, text, scale, color):
    """Draw text centred on cx; returns the left edge used."""
    left = cx - text_width(text, scale) // 2
    draw_text(canvas, left, y, text, scale, color)
    return left


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_paragraph(canvas, x, y, text, scale, color, max_width,
                   line_gap=4):
    """Draw a wrapped paragraph; returns the y just past the last line."""
    line_height = 5 * scale + line_gap
    for line in wrap_text(text, scale, max_width):
        draw_text(canvas, x, y, line, scale, color)
        y += line_height
    return y


class Canvas:
    """An RGB pixel buffer with simple drawing primitives."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background) * (width * height)

    def put(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]


def fill_rect(canvas, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(canvas.width, x + w)
    y1 = min(canvas.height, y + h)
    for yy in range(y0, y1):
        base = (yy * canvas.width + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            canvas.pixels[i] = color[0]
            canvas.pixels[i + 1] = color[1]
            canvas.pixels[i + 2] = color[2]


def rect_outline(canvas, x, y, w, h, color, thickness=1):
    fill_rect(canvas, x, y, w, thickness, color)
    fill_rect(canvas, x, y + h - thickness, w, thickness, color)
    fill_rect(canvas, x, y, thickness, h, color)
    fill_rect(canvas, x + w - thickness, y, thickness, h, color)


def draw_line(canvas, x0, y0, x1, y1, color):
    """Bresenham line between two points."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        canvas.put(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        step = 2 * err
        if step >= dy:
            err += dy
            x0 += sx
        if step <= dx:
            err += dx
            y0 += sy


def fill_circle(canvas, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                canvas.put(xx, yy, color)


def circle_outline(canvas, cx, cy, r, color, thickness=2):
    for angle in range(360):
        rad = angle * 3.141592653589793 / 180.0
        for t in range(thickness):
            rr = r - t
            x = int(cx + rr * _cos(rad) + 0.5)
            y = int(cy + rr * _sin(rad) + 0.5)
            canvas.put(x, y, color)


def _cos(a):
    return _cos_table[int(a * 57.29577951308232) % 360]


def _sin(a):
    return _cos(a - 1.5707963267948966)


def _build_cos_table():
    table = []
    for deg in range(360):
        rad = deg * 3.141592653589793 / 180.0
        value = 1.0
        term = 1.0
        for n in range(1, 7):
            term *= -rad * rad / ((2 * n - 1) * (2 * n))
            value += term
        table.append(value)
    return table


_cos_table = _build_cos_table()


def _chunk(kind, data):
    """One PNG chunk: length, type, data, CRC32."""
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Encode the canvas as a deterministic PNG (filter 0 rows)."""
    width = canvas.width
    height = canvas.height
    raw = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw.append(0)
        start = y * row_bytes
        raw += canvas.pixels[start:start + row_bytes]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def draw_rule(canvas, x, y, w, color, thickness=3):
    fill_rect(canvas, x, y, w, thickness, color)


def draw_flag_stripes(canvas, x, y, w, h, colors):
    """Horizontal stripes, one per color, across a rectangle."""
    band = h // len(colors)
    for i, color in enumerate(colors):
        fill_rect(canvas, x, y + i * band, w, band, color)


def pic_lead(canvas, x, y, w, h):
    """Lead pictogram: a burst over two flag stripes, arcs above it."""
    fill_rect(canvas, x, y, w, h, NAVY)
    draw_flag_stripes(canvas, x, y + h - 26, w, 26,
                      [(0, 87, 184), (255, 213, 0)])
    fill_rect(canvas, x, y + h - 13, w, 13, (255, 255, 255))
    fill_rect(canvas, x, y + h - 6, w, 6, (220, 20, 60))
    cx = x + w // 2
    cy = y + h // 2 - 8
    for k in range(12):
        ang = k * 30 * 3.141592653589793 / 180.0
        length = 52 if k % 2 == 0 else 30
        x2 = int(cx + length * _cos(ang) + 0.5)
        y2 = int(cy + length * _sin(ang) + 0.5)
        draw_line(canvas, cx, cy, x2, y2, GOLD)
    fill_circle(canvas, cx, cy, 20, RED)
    fill_circle(canvas, cx, cy, 12, (255, 200, 60))
    draw_line(canvas, cx - 78, cy - 52, cx - 30, cy - 18, SKY)
    draw_line(canvas, cx + 80, cy - 56, cx + 32, cy - 20, SKY)


def pic_cartel(canvas, x, y, w, h):
    """Cartel pictogram: a gold star badge over a dark panel."""
    fill_rect(canvas, x, y, w, h, (44, 44, 52))
    cx = x + w // 2
    cy = y + h // 2
    points = []
    for k in range(10):
        ang = -90 + k * 36
        rad = ang * 3.141592653589793 / 180.0
        r = 46 if k % 2 == 0 else 20
        points.append((int(cx + r * _cos(rad) + 0.5),
                       int(cy + r * _sin(rad) + 0.5)))
    for a in range(len(points)):
        b = points[(a + 1) % len(points)]
        draw_line(canvas, points[a][0], points[a][1], b[0], b[1], GOLD)
    fill_circle(canvas, cx, cy, 16, GOLD)
    draw_text(canvas, cx - 7, cy - 12, "$", 5, INK)
    fill_rect(canvas, x + 14, y + h - 18, w - 28, 5, RED)


def pic_fbi(canvas, x, y, w, h):
    """FBI pictogram: server rack with a warning triangle."""
    fill_rect(canvas, x, y, w, h, (30, 46, 66))
    rack_x = x + 18
    rack_y = y + 16
    rack_w = 64
    rack_h = h - 32
    rect_outline(canvas, rack_x, rack_y, rack_w, rack_h, SKY, 3)
    for slot in range(4):
        sy = rack_y + 8 + slot * 14
        fill_rect(canvas, rack_x + 8, sy, rack_w - 16, 10, TEAL)
        fill_circle(canvas, rack_x + rack_w - 14, sy + 5, 3, (120, 255, 120))
    tx = x + w - 62
    ty = y + h // 2 - 30
    draw_line(canvas, tx, ty, tx + 44, ty, GOLD)
    draw_line(canvas, tx + 44, ty, tx + 22, ty + 44, GOLD)
    draw_line(canvas, tx + 22, ty + 44, tx, ty, GOLD)
    draw_text(canvas, tx + 17, ty + 14, "!", 5, INK)


def pic_parliament(canvas, x, y, w, h):
    """Parliament pictogram: columns and a dome on a stone base."""
    fill_rect(canvas, x, y, w, h, LIGHT)
    bx = x + 16
    by = y + h - 22
    fill_rect(canvas, bx, by, w - 32, 8, NAVY)
    cx = x + w // 2
    fill_circle(canvas, cx, y + 26, 22, NAVY)
    fill_rect(canvas, cx - 24, y + 26, 48, 8, NAVY)
    for i in range(4):
        col_x = bx + 8 + i * ((w - 48) // 3)
        fill_rect(canvas, col_x, y + 34, 12, h - 56, NAVY)


def pic_storm(canvas, x, y, w, h):
    """Storm pictogram: rain over rising waves."""
    fill_rect(canvas, x, y, w, h, (52, 84, 112))
    for i in range(7):
        rx = x + 12 + i * 16
        draw_line(canvas, rx, y + 10, rx - 6, y + 26, SKY)
        draw_line(canvas, rx + 6, y + 30, rx, y + 46, SKY)
    for row in range(3):
        wy = y + h - 34 + row * 12
        for xx in range(x + 6, x + w - 6, 24):
            draw_line(canvas, xx, wy, xx + 12, wy, WHITE)
            draw_line(canvas, xx + 12, wy, xx + 18, wy - 6, WHITE)


def pic_crowd(canvas, x, y, w, h):
    """Protest pictogram: a crowd of heads under placards."""
    fill_rect(canvas, x, y, w, h, (96, 32, 40))
    for i in range(5):
        hx = x + 14 + i * 22
        hy = y + h - 34
        fill_circle(canvas, hx, hy, 9, (250, 220, 180))
        fill_rect(canvas, hx - 10, hy + 9, 20, h - (hy + 9 - y), INK)
    fill_rect(canvas, x + 10, y + 10, 44, 22, WHITE)
    fill_rect(canvas, x + w - 54, y + 16, 44, 22, GOLD)
    draw_text(canvas, x + 16, y + 15, "NON", 3, RED)


def story_box(canvas, x, y, w, h, kicker, headline, body, accent,
              picture, body_scale=3):
    """One news box: accent rule, kicker, headline, body, pictogram."""
    fill_rect(canvas, x, y, w, h, WHITE)
    rect_outline(canvas, x, y, w, h, INK, 2)
    fill_rect(canvas, x, y, w, 6, accent)
    px = x + 12
    py = y + 16
    pw = w - 24
    ph = 92
    picture(canvas, px, py, pw, ph)
    cy = py + ph + 10
    draw_text(canvas, x + 12, cy, kicker, 3, accent)
    cy += 22
    cy = draw_paragraph(canvas, x + 12, cy, headline, 4, INK, w - 24,
                        line_gap=3)
    cy += 6
    draw_paragraph(canvas, x + 12, cy, body, body_scale, INK, w - 24,
                   line_gap=4)


def build_page():
    """Compose the whole front page and return the canvas."""
    page = Canvas(WIDTH, HEIGHT, PAPER)
    margin = 36
    inner = WIDTH - 2 * margin

    draw_rule(page, margin, 22, inner, INK, 4)
    draw_text_centered(page, WIDTH // 2, 34, "THE DAILY SUM", 9, INK)
    draw_rule(page, margin, 108, inner, INK, 2)
    draw_text_centered(page, WIDTH // 2, 116,
                       "SUNDAY 22 NOVEMBER 2026", 4, RED)
    draw_text_centered(page, WIDTH // 2, 144,
                       "THE WORLD'S NEWS IN ONE PAGE", 3, GREY)

    # Lead story: full width.
    lx = margin
    ly = 168
    lw = inner
    lh = 244
    fill_rect(page, lx, ly, lw, lh, WHITE)
    rect_outline(page, lx, ly, lw, lh, INK, 3)
    fill_rect(page, lx, ly, lw, 8, RED)
    pic_lead(page, lx + 14, ly + 20, 300, lh - 34)
    tx = lx + 330
    tw = lw - 344
    draw_text(page, tx, ly + 24, "UKRAINE WAR", 3, RED)
    y = draw_paragraph(page, tx, ly + 48,
                       "MISSILES LAND IN POLAND", 6, INK, tw, line_gap=4)
    y += 8
    draw_paragraph(page, tx, y,
                   "A huge Russian barrage on Ukraine spilled over the "
                   "border, with two missiles and a drone landing in "
                   "Polish fields. President Trump called it a mistake "
                   "as NATO vowed to defend every inch of allied land.",
                   3, INK, tw, line_gap=5)

    # Middle row: three stories side by side.
    row_y = 428
    row_h = 272
    col_w = (inner - 24) // 3
    story_box(page, margin, row_y, col_w, row_h,
              "MEXICO", "EL CHAPO ISIDRO CAUGHT",
              "Troops captured cartel boss El Chapo Isidro in a "
              "shoot-out; 11 dead.", TEAL, pic_cartel)
    story_box(page, margin + col_w + 12, row_y, col_w, row_h,
              "UNITED STATES", "FBI PROBES DATA BREACH",
              "The FBI is probing a suspected breach of its national "
              "crime database.", NAVY, pic_fbi)
    story_box(page, margin + 2 * (col_w + 12), row_y, col_w, row_h,
              "ISRAEL", "EISENKOT TO FORM GOVERNMENT",
              "Herzog asked Eisenkot to form a government, bypassing "
              "Netanyahu.", GOLD, pic_parliament)

    # Lower row: two stories side by side.
    low_y = 712
    low_h = 180
    half_w = (inner - 12) // 2
    fill_rect(page, margin, low_y, half_w, low_h, WHITE)
    rect_outline(page, margin, low_y, half_w, low_h, INK, 2)
    fill_rect(page, margin, low_y, half_w, 6, TEAL)
    pic_storm(page, margin + 12, low_y + 16, 120, low_h - 28)
    sx = margin + 144
    draw_text(page, sx, low_y + 18, "GAZA", 3, TEAL)
    draw_paragraph(page, sx, low_y + 42, "STORMS FLOOD GAZA SHELTERS",
                   4, INK, half_w - 156, line_gap=3)
    draw_paragraph(page, sx, low_y + 96,
                   "Winter rain swamped tents of a million displaced "
                   "people as four nations demanded aid access.",
                   3, INK, half_w - 156, line_gap=4)

    fill_rect(page, margin + half_w + 12, low_y, half_w, low_h, WHITE)
    rect_outline(page, margin + half_w + 12, low_y, half_w, low_h, INK, 2)
    fill_rect(page, margin + half_w + 12, low_y, half_w, 6, RED)
    pic_crowd(page, margin + half_w + 24, low_y + 16, 120, low_h - 28)
    fx = margin + half_w + 156
    draw_text(page, fx, low_y + 18, "FRANCE", 3, RED)
    draw_paragraph(page, fx, low_y + 42, "FRANCE MARCHES AGAIN",
                   4, INK, half_w - 168, line_gap=3)
    draw_paragraph(page, fx, low_y + 96,
                   "A fourth weekend of protests against the rising "
                   "cost of living filled French streets.",
                   3, INK, half_w - 168, line_gap=4)

    # Ticker of briefs.
    tick_y = 904
    draw_rule(page, margin, tick_y, inner, INK, 2)
    draw_text(page, margin, tick_y + 10, "ALSO TODAY", 3, RED)
    draw_paragraph(page, margin, tick_y + 32,
                   "US envoys head to Moscow after Abu Dhabi talks  |  "
                   "Trump open to nuclear talks with Putin and Xi  |  "
                   "Iran shortens Hormuz reopening plan to two days",
                   3, INK, inner, line_gap=4)

    draw_rule(page, margin, 980, inner, INK, 2)
    draw_text_centered(page, WIDTH // 2, 988,
                       "DRAWN PROCEDURALLY FROM REPORTS FIRST PUBLISHED "
                       "22 NOVEMBER 2026", 2, GREY)
    return page


def main():
    """Write entry.png into MAKEFUN_OUTPUT_DIR, nothing else."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    page = build_page()
    data = encode_png(page)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
