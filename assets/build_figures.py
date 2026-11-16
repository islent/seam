#!/usr/bin/env python3
"""Generate every figure in ``assets/figures/``.

Run:  python assets/build_figures.py

Two rules hold for every string in these files:

1. **Plain words first.** The labels say what a thing *does* ("改不动了" / "能读到"), not what
   the specification calls it. The formal name appears, if at all, as a small monospace tag.
   A reader who never opens SPEC.md should still be able to follow every figure.
2. **Technical drafting, not illustration.** Flat fills, hairline rules, monospace for
   identifiers, no gradients, no glow, no shadows, no stock-metaphor icons.

A generator rather than eight SVG files, because eight figures sharing one visual grammar
drift apart within a week. Type scale, rule weight, palette and arrowheads are single
definitions here.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from figure_text import EN  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "figures"
LANG = "zh"


def t(s: str) -> str:
    """The same figure, in the other language. Layout is written once; words are data."""
    return EN.get(s, s) if LANG == "en" else s

# ---------------------------------------------------------------------------
# palette — six colours, each with a job. None is decorative.
# ---------------------------------------------------------------------------
PAPER = "#FBFAF6"   # the page
INK = "#17171A"     # primary text
INK2 = "#3D3D3A"    # secondary text
MUTE = "#6E6E68"    # annotations
FAINT = "#9C9C94"   # furniture
RULE = "#D3D0C5"    # hairline
HAIR = "#EFEDE5"    # tinted strips

BLUE = "#1F4E79"    # the boundary, things you can read
BLUE_T = "#EDF2F7"
GREEN = "#2A6A4A"   # worked / allowed
GREEN_T = "#EAF1EC"
BRICK = "#9A3A2C"   # refused / locked
BRICK_T = "#F7E8E4"
OCHRE = "#82601A"   # how we know
OCHRE_T = "#F5EEDE"

SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', "
        "'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif")
MONO = ("'SF Mono', 'JetBrains Mono', ui-monospace, Menlo, Consolas, "
        "'Liberation Mono', monospace")

W = 1200            # one column width, for every figure
M = 64              # left/right margin


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(s: str, size: float) -> float:
    """Approximate advance width: CJK ~1.0 em, Latin ~0.53 em.

    Used for centring and for keeping labels inside boxes. An estimate is enough, but it
    must err wide — the failure mode of erring narrow is a label quietly overhanging.
    """
    w = 0.0
    for ch in t(s):
        o = ord(ch)
        if o > 0x2E80:
            w += 1.0
        elif ch in "iljI.,:;'|![]()":
            w += 0.31
        elif ch in "MW@%":
            w += 0.86
        elif ch.isupper():
            w += 0.63
        else:
            w += 0.53
    return w * size


def T(x, y, s, size=13, fill=INK, weight=None, font=SANS, anchor="start", ls=None,
      rot=None, opacity=None) -> str:
    s = t(s)
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    w = f' font-weight="{weight}"' if weight else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    r = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    o = f' opacity="{opacity}"' if opacity else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" '
            f'fill="{fill}"{w}{a}{l}{r}{o}>{esc(s)}</text>')


def R(x, y, w, h, fill="none", stroke=None, sw=1, rx=0, dash=None, opacity=None) -> str:
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    r = f' rx="{rx}"' if rx else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{opacity}"' if opacity else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="{fill}"{s}{r}{d}{o}/>')


def L(x1, y1, x2, y2, stroke=RULE, sw=1, dash=None, cap="butt") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"{d}/>')


def P(d, stroke=INK, sw=1, fill="none", dash=None, marker=None) -> str:
    a = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round"{a}{m}/>')


def C(cx, cy, r, fill=INK, stroke=None, sw=1) -> str:
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"{s}/>'


def pill(cx, cy, w, h, label, size=9.5, fill=PAPER, stroke=RULE, color=INK2,
         font=SANS) -> str:
    """A label sitting *on* a line, with a punched-out background so the line reads as broken."""
    return (R(cx - w / 2, cy - h / 2, w, h, fill=fill, stroke=stroke, rx=h / 2)
            + T(cx, cy + size * 0.36, label, size, color, font=font, anchor="middle"))


def rot_label(x, y, s, size=8.8, color=BLUE, bg=PAPER) -> str:
    """A vertical edge label. Rotated text needs its own background, or the link it names
    shows through the glyphs."""
    w = tw(s, size)
    return (f'<g transform="rotate(-90 {x} {y})">'
            + R(x - w / 2 - 4, y - size * 0.9 - 3, w + 8, size * 1.5 + 6, fill=bg)
            + T(x, y + size * 0.36, s, size, color, anchor="middle")
            + "</g>")


def cross(x, y, r=8, color=BRICK, sw=2.2) -> str:
    return (L(x - r, y - r, x + r, y + r, color, sw, cap="round")
            + L(x + r, y - r, x - r, y + r, color, sw, cap="round"))


def check(x, y, r=7, color=GREEN, sw=2.0) -> str:
    return P(f"M {x-r} {y} L {x-r*0.25} {y+r*0.7} L {x+r} {y-r*0.8}", color, sw)


# ---------------------------------------------------------------------------
# page furniture
# ---------------------------------------------------------------------------
def defs() -> str:
    marks = []
    for name, col in (("ink", INK), ("blue", BLUE), ("brick", BRICK),
                      ("green", GREEN), ("mute", FAINT), ("ochre", OCHRE)):
        marks.append(
            f'<marker id="a-{name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>')
    return (
        "<defs>"
        + "".join(marks)
        + '<pattern id="hatch-brick" width="7" height="7" patternUnits="userSpaceOnUse" '
          'patternTransform="rotate(45)">'
          f'<rect width="7" height="7" fill="{BRICK_T}"/>'
          '<line x1="0" y1="0" x2="0" y2="7" stroke="#D8B6AC" stroke-width="1.4"/>'
          "</pattern>"
        + "</defs>")


def head(num: int, title: str, sub: str, total: int = 4) -> str:
    return (
        T(M, 42, f"FIG. {num} / {total}", 10.5, OCHRE, font=MONO, ls="1.8")
        + T(M, 79, title, 23, INK, weight="700")
        + T(M, 104, sub, 12.8, MUTE)
        + L(M, 122, W - M, 122, RULE, 1)
    )


def foot(height: int) -> str:
    y = height - 34
    return (L(M, y, W - M, y, HAIR, 1)
            + T(M, y + 18, "seam · v0.1-draft", 9.5, FAINT, font=MONO, ls="0.6")
            + T(W - M, y + 18, "看得见的界线", 9.5, FAINT, font=MONO, anchor="end"))


def wrap(body: str, height: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
            f'width="{W}" height="{height}" role="img">'
            + defs() + R(0, 0, W, height, fill=PAPER) + body + "</svg>")


# ---------------------------------------------------------------------------
# FIG 1 — one handover vs a seam
# ---------------------------------------------------------------------------
def fig1():
    H = 626
    b = head(1, "只交一次，还是每一步都在",
             "现在的工具只把一个结果递给你。中间发生了什么，你看不到，也插不上手。")

    # ---- the way it usually works
    b += T(M, 178, "现在的做法", 18, INK, weight="700")
    b += T(M, 196, "提交 → 等 → 结果", 10, FAINT, font=MONO)
    b += T(M, 228, "一次交付", 10.5, MUTE)

    ax1, ax2 = 250, 1112
    b += L(ax1, 236, ax2 - 20, 236, FAINT, 1.2)
    b += C(268, 236, 4.5, INK)
    b += T(268, 218, "提交", 10.5, MUTE, anchor="middle")

    b += R(300, 214, 700, 44, fill="#26262A", rx=2)
    b += T(650, 242, "中间看不见：没有进度，没有中间结果，也改不了任何东西", 13, "#F2F1EC",
           anchor="middle")

    b += P(f"M 906 236 L {ax2-6} 236", INK, 1.2, marker="a-ink")
    b += C(1040, 236, 4.5, INK)
    b += T(1054, 232, "结果", 10.5, MUTE)
    b += T(650, 286, "跑了两个小时才知道参数填错了。", 10.5, FAINT, anchor="middle")

    # ---- what this project asks for
    b += L(M, 322, W - M, 322, HAIR, 1)
    b += T(M, 360, "这个项目要求的做法", 18, INK, weight="700")
    b += T(M, 378, "每一步都能看，能改", 10, FAINT)
    b += T(M, 410, "一直在场", 10.5, MUTE)

    ay = 420
    b += R(300, 406, 700, 28, fill=BLUE_T)
    b += L(ax1, ay, ax2 - 20, ay, FAINT, 1.2)
    b += C(268, ay, 4.5, INK)
    b += T(268, 402, "开始", 10.5, MUTE, anchor="middle")

    ticks = [(330, "up", "第 120 步"), (412, "dn", "改成 480"), (494, "up", ""),
             (576, "dn", ""), (658, "up", "场强"), (740, "dn", ""),
             (822, "up", ""), (904, "dn", "改分辨率 ✕"), (986, "up", "时间")]
    for x, d, label in ticks:
        col = BLUE if d == "up" else BRICK
        b += L(x, ay - 11, x, ay + 11, col, 1.6)
        b += C(x, ay, 3.4, col)
        if label:
            if d == "up":
                b += T(x, ay - 20, label, 10, BLUE, anchor="middle")
            else:
                b += T(x, ay + 30, label, 10, BRICK, anchor="middle")

    b += T(1108, 384, "↑ 能读到", 9.5, BLUE, font=MONO, anchor="end")
    b += T(1108, 462, "↓ 能改的", 9.5, BRICK, font=MONO, anchor="end")

    # the record, tick for tick with the entries above it
    b += T(M, 476, "操作记录", 10.5, INK2)
    b += T(M, 492, "存在一个 trace.jsonl 里", 9.5, FAINT, font=MONO)
    b += R(250, 466, 862, 46, fill=HAIR, stroke=RULE, rx=2)
    b += T(262, 494, "第几条", 9, FAINT)
    for i, (x, d, _l) in enumerate(ticks):
        col = BLUE if d == "up" else BRICK
        b += R(x - 17, 474, 34, 30, fill=PAPER, stroke=col, sw=0.9, rx=2)
        b += T(x, 494, str(i + 1), 10, col, font=MONO, anchor="middle")

    b += T(M, 548, "差别在于你能不能中途问一句、改一下。", 11.5, INK2)
    b += T(M, 570, "上面那 9 条，每一条都能翻回去看：第几步、谁改的、改成了多少。", 11, FAINT)

    return wrap(b + foot(H), H), H, "fig-1-tunnel-vs-seam"


# ---------------------------------------------------------------------------
# FIG 2 — what one read and one write actually look like
# ---------------------------------------------------------------------------
def fig2():
    H = 676
    b = head(2, "一次读、一次写，长什么样",
             "程序把数递出来，界面把数改回去。同一根线，两个方向，规矩不一样。")

    LX0, LX1 = 84, 430
    SX, SW_ = 470, 220
    RX0, RX1 = 730, 1136
    MID = SX + SW_ / 2

    b += R(SX, 150, SW_, 370, fill=BLUE_T)
    b += L(SX, 150, SX, 520, BLUE, 1)
    b += L(SX + SW_, 150, SX + SW_, 520, BLUE, 1)
    b += T(MID, 172, "界线", 9.5, BLUE, anchor="middle", ls="3")

    b += T(M, 142, "程序内部", 10, FAINT, ls="1.2")
    b += T(W - M, 142, "你看到的界面", 10, FAINT, anchor="end", ls="1.2")

    # ---- band 1: something read out, left to right
    y0, h0 = 190, 88
    cy0 = y0 + h0 / 2
    b += R(LX0, y0, LX1 - LX0, h0, fill=PAPER, stroke=RULE, rx=3)
    b += R(LX0, y0, 3, h0, fill=BLUE)
    b += T(LX0 + 16, y0 + 26, "epoch3d.dat", 12.5, INK, font=MONO)
    b += T(LX0 + 16, y0 + 47, "每写一次快照，往后加一行", 10.5, MUTE)
    b += T(LX0 + 16, y0 + 70, "纯文本，不用装额外的库", 9.5, BLUE)

    b += R(RX0, y0, RX1 - RX0, h0, fill=PAPER, stroke=RULE, rx=3)
    b += R(RX0, y0, 3, h0, fill=BLUE)
    b += T(RX0 + 16, y0 + 26, "一张场的缩略图", 12.5, INK)
    b += T(RX0 + 16, y0 + 47, "120 像素宽，每走一步换一张", 10.5, MUTE)
    b += T(RX0 + 16, y0 + 70, "画成图片 / 字符画都行", 9.5, BLUE)

    b += P(f"M {LX1} {cy0} L {RX0 - 4} {cy0}", BLUE, 1.5, marker="a-blue")
    b += pill(MID, cy0, 198, 24, "多久一次 · 多大 · 凭什么知道", 9.2, PAPER, RULE, BLUE)
    b += T(RX1, 174, "读出来", 9, BLUE, anchor="end")

    # ---- band 2: a change that works, right to left
    y1, h1 = 306, 88
    cy1 = y1 + h1 / 2
    b += R(LX0, y1, LX1 - LX0, h1, fill=PAPER, stroke=RULE, rx=3)
    b += R(LX0, y1, 3, h1, fill=GREEN)
    b += T(LX0 + 16, y1 + 26, "until = 480", 12.5, INK, font=MONO)
    b += T(LX0 + 16, y1 + 47, "程序每走一步瞧一眼，下一步生效", 10.5, MUTE)
    b += T(LX0 + 16, y1 + 68, "改成功了", 9.5, GREEN)
    b += check(LX0 + 16 + tw("改成功了", 9.5) + 10, y1 + 64, 5, GREEN, 1.8)

    b += R(RX0, y1, RX1 - RX0, h1, fill=PAPER, stroke=RULE, rx=3)
    b += R(RX0, y1, 3, h1, fill=GREEN)
    b += T(RX0 + 16, y1 + 26, "一个滑杆，拖到 900", 12.5, INK)
    b += T(RX0 + 16, y1 + 47, "松手才提交，拖着的过程不算数", 10.5, MUTE)
    b += T(RX0 + 16, y1 + 70, "范围 5 – 2000，跑着也能改", 9.5, GREEN)

    b += P(f"M {RX0} {cy1} L {LX1 + 4} {cy1}", GREEN, 1.5, marker="a-green")
    b += pill(MID, cy1, 178, 24, "滑杆 · 5–2000 · 随时能改", 9.2, PAPER, RULE, GREEN)
    b += T(RX1, 292, "写回去", 9, GREEN, anchor="end")

    # ---- band 3: a change that is refused at the boundary
    y2, h2 = 422, 88
    cy2 = y2 + h2 / 2
    b += R(LX0, y2, LX1 - LX0, h2, fill=BRICK_T, stroke="#E4C8C0", rx=3)
    b += R(LX0, y2, 3, h2, fill=BRICK)
    b += T(LX0 + 16, y2 + 26, "改不动", 12.5, BRICK, weight="700")
    b += T(LX0 + 16, y2 + 49, "这个请求根本没送进去：", 10.5, INK2)
    b += T(LX0 + 16, y2 + 67, "在门口就被挡住了。", 10.5, INK2)

    b += R(RX0, y2, RX1 - RX0, h2, fill=PAPER, stroke=RULE, rx=3)
    b += R(RX0, y2, 3, h2, fill=BRICK)
    b += T(RX0 + 16, y2 + 26, "一个滑杆，拖到 60", 12.5, INK)
    b += T(RX0 + 16, y2 + 47, "它和上面那个长得一模一样。", 10.5, MUTE)
    b += T(RX0 + 16, y2 + 70, "这个参数在启动时就定死了", 9.5, BRICK)

    b += P(f"M {RX0} {cy2} L {SX + SW_ + 12} {cy2}", BRICK, 1.5, marker="a-brick")
    b += cross(SX + SW_ - 2, cy2, 9, BRICK, 2.4)
    b += pill(MID, cy2, 116, 24, "启动后不能改", 9.2, PAPER, RULE, BRICK)
    b += T(RX1, 408, "被挡下", 9, BRICK, anchor="end")

    # ---- why this matters
    b += L(M, 546, W - M, 546, HAIR, 1)
    b += T(M, 572, "能改的和不能改的，长得一模一样", 12.5, INK, weight="700")
    b += T(M, 592, "所以「能不能改」必须写在界面上，不能只埋在后台。"
                   "后台知道、你不不知道，结果就是你以为在调，其实什么也没发生。", 10.8, MUTE)
    b += T(M, 622, "还有一条容易漏的：被拒绝也是一次操作，也要记下来 —— "
                   "「没试过」和「试了被挡」是两件事。", 11, BRICK)

    return wrap(b + foot(H), H), H, "fig-2-anatomy"


# ---------------------------------------------------------------------------
# FIG 3 — three questions, four controls
# ---------------------------------------------------------------------------
def fig3():
    H = 748
    b = head(3, "问三个问题，只剩四种控件",
             "做个界面不难，难的是不瞎猜。三个问题问完，答案只有四种 —— 这是穷举的结果。")

    facts = [
        ("① 能不能改？", "有没有东西把它读回去",
         [("只读，没人读它", "→ 只能看"),
          ("能改，程序会读回去", "→ 问第二个"),
          ("说不清", "→ 留空")]),
        ("② 能填什么？", "它的取值长什么样",
         [("没有值，只是一个动作", "→ 按钮"),
          ("几个选项里挑一个", "→ 下拉"),
          ("一段范围里的连续值", "→ 滑杆"),
          ("一段话 / 一个文件 / 没范围", "→ 留空")]),
        ("③ 什么时候能改？", "启动前，还是跑着也能改",
         [("启动前定死", "→ 灰掉"),
          ("跑着随时能改", "→ 能拖"),
          ("停在两步之间才能改", "→ 能拖")]),
    ]
    y = 158
    mids = []
    for title, sub, rows in facts:
        h = 34 + 22 * len(rows) + 12
        b += R(M, y, 372, h, fill=PAPER, stroke=RULE, rx=3)
        b += T(M + 16, y + 25, title, 13, INK, weight="700")
        b += T(M + 16 + tw(title, 13) + 14, y + 25, sub, 8.8, FAINT)
        for i, (left, right) in enumerate(rows):
            yy = y + 50 + 22 * i
            b += T(M + 16, yy, left, 10.5, INK2)
            b += T(M + 356, yy, right, 10, BLUE, anchor="end")
        mids.append(y + h / 2)
        y += h + 14

    nx, nw, ny, nh = 486, 208, 250, 132
    for t in mids:
        b += P(f"M 438 {t} C 464 {t} 468 {ny + nh/2} {nx - 3} {ny + nh/2}", "#BCB9AE", 1.2,
               marker="a-mute")
    b += R(nx, ny, nw, nh, fill="#1D1D21", rx=3)
    b += T(nx + nw / 2, ny + 34, "三个答案", 11, "#8FA6BC", anchor="middle", ls="2")
    b += T(nx + nw / 2, ny + 68, "定下控件", 17, "#FFFFFF", anchor="middle", weight="700")
    b += T(nx + nw / 2, ny + 94, "不用猜", 13, "#D8D6CF", anchor="middle")
    b += T(nx + nw / 2, ny + 116, "只有这四种", 9.2, "#8FA6BC", anchor="middle")

    cards = [
        ("按钮", "一个动作，没有值要填", "stop · dump_slice", BRICK),
        ("滑杆", "一段范围里连续调", "until · resolution", BLUE),
        ("下拉", "几个选项里挑一个", "bc_x_min · dimensions", GREEN),
        ("读数", "只能看，不能改", "数字、曲线、图", FAINT),
    ]
    cx, cw = 752, W - M - 752
    cy = 150
    for cn, rule, ex, col in cards:
        b += P(f"M {nx + nw + 3} {ny + nh/2} L {cx - 8} {cy + 48}", "#BCB9AE", 1.1,
               marker="a-mute")
        b += R(cx, cy, cw, 96, fill=PAPER, stroke=RULE, rx=3)
        b += R(cx, cy, 4, 96, fill=col)
        b += T(cx + 20, cy + 32, cn, 16, INK, weight="700")
        b += T(cx + 20, cy + 56, rule, 11, MUTE)
        b += T(cx + 20, cy + 80, ex, 9.5, col, font=MONO)
        cy += 110

    y4 = 596
    b += R(M, y4, W - 2 * M, 64, fill=BRICK_T, stroke="#E4C8C0", rx=3)
    b += T(M + 18, y4 + 27, "三个问题有一个答不上来 → 留空，并且写在界面上", 13, BRICK,
           weight="700")
    b += T(M + 18, y4 + 48, "猜出来的滑杆比没有滑杆更糟：它让人以为自己能控制。", 11, INK2)

    b += T(M, 690, "想要第五种控件，得先举出一个前三个问题都装不下的例子 —— "
                   "那正是这个项目最想收到的批评。", 11.2, FAINT)

    return wrap(b + foot(H), H), H, "fig-3-derivation"


# ---------------------------------------------------------------------------
# FIG 4 — when can it change
# ---------------------------------------------------------------------------
def fig4():
    H = 566
    b = head(4, "什么时候能改",
             "同一个参数，三种情况。看起来一模一样，用起来完全不同。")

    X0, X1 = 226, 1112
    ph = [(X0, 372, "提交前"), (372, 462, "刚启动"), (462, 1010, "跑着"), (1010, X1, "结束")]
    for a, c, label in ph:
        b += T((a + c) / 2, 156, label, 11.5, MUTE, anchor="middle")
        b += L(c, 168, c, 362, RULE, 1, dash="3 4")

    lanes = [
        ("启动时定死", "sealed", [GREEN, GREEN, None, None],
         {0: "能改", 1: "能改", 2: "改不动了：分辨率在启动时就定了"}),
        ("随时能改", "midrun", [GREEN, GREEN, GREEN, None],
         {2: "随时能改"}),
        ("两步之间才能改", "perstep", [None, None, GREEN, None],
         {0: "没地方插", 2: "只在两步之间那一下", 3: "没有下一步了"}),
    ]
    ly = 172
    for cn, tag, fills, notes in lanes:
        b += T(X0 - 14, ly + 24, cn, 11, INK, weight="700", anchor="end")
        b += T(X0 - 14, ly + 41, tag, 8.5, FAINT, font=MONO, anchor="end")
        for i, (a, c, _l) in enumerate(ph):
            f = fills[i]
            if f == GREEN:
                b += R(a + 2, ly, c - a - 4, 54, fill=GREEN_T, stroke="#BCD4C4", rx=2)
            else:
                b += R(a + 2, ly, c - a - 4, 54, fill="url(#hatch-brick)",
                       stroke="#E4C8C0", rx=2)
            if i in notes:
                b += T((a + c) / 2, ly + 32, notes[i], 10,
                       INK2 if f == GREEN else BRICK, anchor="middle")
        ly += 66

    b += L(X0, 372, X1, 372, FAINT, 1.2)

    b += R(X0, 400, 26, 14, fill=GREEN_T, stroke="#BCD4C4", rx=2)
    b += T(X0 + 34, 412, "能改", 10.5, MUTE)
    b += R(X0 + 92, 400, 26, 14, fill="url(#hatch-brick)", stroke="#E4C8C0", rx=2)
    b += T(X0 + 126, 412, "改不动 —— 但会留一条记录，说明你试过", 10.5, MUTE)

    b += T(M, 454, "能改的和不能改的，外观没有区别。", 11.5, INK2)
    b += T(M, 476, "把「能不能改」只告诉后台、不告诉操作者，等于把一次静默失败"
                   "包装成一次成功。", 11, FAINT)

    return wrap(b + foot(H), H), H, "fig-4-liveness"


# ---------------------------------------------------------------------------
def main(lang: str = "zh") -> int:
    global LANG
    LANG = lang
    dest = OUT / lang
    dest.mkdir(parents=True, exist_ok=True)
    bad = 0
    for fn in (fig1, fig2, fig3, fig4):
        svg, h, name = fn()
        (dest / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"{name+'.svg':30s} {len(svg):6d} bytes  {W}x{h}")
        if lang == "en":
            # a new Chinese label with no translation would ship silently; fail instead
            for m in re.finditer(r"<text[^>]*>([^<]*[\u4e00-\u9fff][^<]*)</text>", svg):
                print(f"   !! untranslated: {m.group(1)[:40]}")
                bad += 1
        for m in re.finditer(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>(.*?)</text>', svg):
            x, y = float(m.group(1)), float(m.group(2))
            if not (0 <= x <= W) or not (0 <= y <= h):
                print(f"   !! outside canvas ({x}, {y}): {m.group(3)[:40]}")
                bad += 1
    for p in sorted(dest.glob("*.svg")):
        s = p.read_text(encoding="utf-8")
        h = int(re.search(r'height="(\d+)"', s).group(1))
        for m in re.finditer(r'<text x="[\d.]+" y="([\d.]+)"[^>]*>([^<]{6,})</text>', s):
            y = float(m.group(1))
            if h - 34 - 8 < y < h - 34:
                print(f"   !! {p.name}: caption at y={y} collides with the footer rule")
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    langs = sys.argv[1:] or ["zh", "en"]
    code = 0
    for lg in langs:
        code |= main(lg)
    raise SystemExit(code)
