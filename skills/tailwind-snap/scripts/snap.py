#!/usr/bin/env python3
"""Snap px values onto Tailwind v4 tokens.

  snap.py 13 15 7px 1.5rem      -> what each value becomes on every scale
  snap.py --audit src app.tsx   -> every arbitrary utility in those paths, with a suggestion

The scales here are Tailwind v4 defaults. A project @theme block overrides them,
and this script does not read one — treat its output as a starting list, not a verdict.
"""

import argparse
import math
import os
import re
import sys

SPACING = 4.0  # px per step, --spacing: 0.25rem

FONT_SIZE = [("xs", 12), ("sm", 14), ("base", 16), ("lg", 18), ("xl", 20),
             ("2xl", 24), ("3xl", 30), ("4xl", 36), ("5xl", 48), ("6xl", 60),
             ("7xl", 72), ("8xl", 96), ("9xl", 128)]

RADIUS = [("none", 0), ("xs", 2), ("sm", 4), ("md", 6), ("lg", 8), ("xl", 12),
          ("2xl", 16), ("3xl", 24), ("4xl", 32)]

BLUR = [("xs", 4), ("sm", 8), ("md", 12), ("lg", 16), ("xl", 24), ("2xl", 40), ("3xl", 64)]

CONTAINER = [("3xs", 256), ("2xs", 288), ("xs", 320), ("sm", 384), ("md", 448),
             ("lg", 512), ("xl", 576), ("2xl", 672), ("3xl", 768), ("4xl", 896),
             ("5xl", 1024), ("6xl", 1152), ("7xl", 1280)]

# utility prefixes -> scale family
MULTIPLIER = """p px py pt pr pb pl ps pe
m mx my mt mr mb ml me ms
gap gap-x gap-y space-x space-y
w h size min-w min-h max-w max-h basis
inset inset-x inset-y top right bottom left start end
translate translate-x translate-y leading indent
scroll-m scroll-mx scroll-my scroll-mt scroll-mr scroll-mb scroll-ml
scroll-p scroll-px scroll-py scroll-pt scroll-pr scroll-pb scroll-pl""".split()

RADIUS_PREFIXES = ["rounded", "rounded-t", "rounded-r", "rounded-b", "rounded-l",
                   "rounded-s", "rounded-e", "rounded-tl", "rounded-tr",
                   "rounded-bl", "rounded-br", "rounded-ss", "rounded-se",
                   "rounded-es", "rounded-ee"]

LITERAL_PREFIXES = ["border", "border-x", "border-y", "border-t", "border-r",
                    "border-b", "border-l", "divide-x", "divide-y",
                    "z", "opacity", "duration", "delay", "order"]

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte",
        ".astro", ".php", ".blade", ".erb", ".twig", ".mdx", ".svg"}

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "vendor",
             "__pycache__", ".venv", "coverage", ".turbo", "out"}

ARBITRARY = re.compile(r"(?<![\w:./-])(-?)([a-z][a-z0-9-]*)-\[([^\]\s\"']+)\]")


def to_px(raw):
    """Parse a CSS length into px, or None if it is not one."""
    v = raw.strip().replace("_", " ")
    m = re.fullmatch(r"(-?\d*\.?\d+)(px|rem|em)?", v)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2)
    if unit in ("rem", "em"):
        return n * 16
    return n  # px or unitless


def fmt(n):
    return f"{n:g}"


def snap_multiplier(px):
    """Nearest half step; an exact tie goes to the whole step (15px -> p-4)."""
    exact = px / SPACING
    lo = math.floor(exact * 2) / 2
    hi = lo + 0.5
    if abs(exact - lo) < abs(hi - exact):
        steps = lo
    elif abs(hi - exact) < abs(exact - lo):
        steps = hi
    else:  # tie
        steps = lo if lo == int(lo) else hi
    if steps == int(steps):
        steps = int(steps)
    return fmt(steps), steps * SPACING


def snap_named(px, scale):
    # ties go down: the first entry at the minimum distance wins
    name, val = min(scale, key=lambda kv: (abs(kv[1] - px), kv[1]))
    return name, val


def suggest(prefix, raw):
    """-> (replacement class body, resolved px, note) or None."""
    if raw.startswith(("#", "rgb", "hsl", "oklch", "var(")):
        return (None, None, "color: use a theme token, or flag it as missing")
    if prefix.startswith("tracking"):
        return (None, None, "letter spacing: convert to em against the font size, then pick a tracking-* token")
    ms = re.fullmatch(r"(-?\d*\.?\d+)m?s", raw.strip())
    if ms and prefix in ("duration", "delay"):
        n = float(ms.group(1)) * (1000 if raw.strip().endswith("s") and not raw.strip().endswith("ms") else 1)
        return (f"{prefix}-{fmt(n)}", None, "literal scale — no bracket needed")
    if prefix == "opacity":
        v = to_px(raw)
        if v is not None:
            return (f"opacity-{fmt(v * 100 if v <= 1 else v)}", None, "literal scale — no bracket needed")
    px = to_px(raw)
    if px is None:
        return None
    if prefix in MULTIPLIER:
        if 0 < abs(px) < 2:
            return (None, None, "hairline — below the scale, keep it arbitrary")
        n, actual = snap_multiplier(px)
        return (f"{prefix}-{n}", actual, "")
    if prefix == "text":
        name, actual = snap_named(px, FONT_SIZE)
        return (f"text-{name}", actual, "")
    if prefix in RADIUS_PREFIXES:
        if px >= 48:  # past the scale, this is a pill
            return (f"{prefix}-full", None, "")
        name, actual = snap_named(px, RADIUS)
        return (f"{prefix}-{name}", actual, "")
    if prefix == "blur" or prefix.startswith("backdrop-blur"):
        name, actual = snap_named(px, BLUR)
        return (f"{prefix}-{name}", actual, "")
    if prefix in ("max-w", "min-w", "w") and px >= 256:
        n, actual = snap_multiplier(px)
        name, cval = snap_named(px, CONTAINER)
        if abs(cval - px) < abs(actual - px):
            return (f"{prefix}-{name}", cval, "container scale")
        return (f"{prefix}-{n}", actual, "")
    if prefix in LITERAL_PREFIXES:
        if prefix == "border" and px == 1:
            return ("border", None, "1px is the bare utility")
        if prefix.startswith(("border-", "divide-")) and px == 1:
            return (prefix, None, "1px is the bare utility")
        return (f"{prefix}-{fmt(px)}", None, "literal scale — no bracket needed")
    return None


def drift_str(want, got):
    if got is None or want is None:
        return ""
    d = got - want
    return "exact" if abs(d) < 1e-9 else f"{d:+g}px"


def cmd_values(values):
    for raw in values:
        px = to_px(raw)
        if px is None:
            print(f"{raw}: not a length")
            continue
        n, actual = snap_multiplier(px)
        fs, fsv = snap_named(px, FONT_SIZE)
        rd, rdv = snap_named(px, RADIUS)
        print(f"{fmt(px)}px")
        print(f"  spacing   p-{n} / m-{n} / gap-{n} / w-{n} / leading-{n}   = {fmt(actual)}px ({drift_str(px, actual)})")
        print(f"  font-size text-{fs}   = {fsv}px ({drift_str(px, fsv)})")
        print(f"  radius    rounded-{rd}   = {rdv}px ({drift_str(px, rdv)})")
        print(f"  literal   border-{fmt(px)} / z-{fmt(px)} / duration-{fmt(px)}")


def walk(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if os.path.splitext(f)[1] in EXTS or f.endswith(".blade.php"):
                    yield os.path.join(root, f)


def cmd_audit(paths):
    rows = []
    for path in walk(paths):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for m in ARBITRARY.finditer(line):
                neg, prefix, raw = m.groups()
                s = suggest(prefix, raw)
                if not s:
                    continue
                repl, actual, note = s
                cur = f"{neg}{prefix}-[{raw}]"
                if repl is None:
                    rows.append((path, i, cur, "—", note))
                    continue
                px = to_px(raw)
                rows.append((path, i, cur, f"{neg}{repl}",
                             " ".join(x for x in (drift_str(px, actual), note) if x)))
    if not rows:
        print("No snappable arbitrary values found.")
        return 0
    w1 = max(len(f"{r[0]}:{r[1]}") for r in rows)
    w2 = max(len(r[2]) for r in rows)
    w3 = max(len(r[3]) for r in rows)
    for path, ln, cur, repl, note in rows:
        print(f"{path}:{ln}".ljust(w1) + "  " + cur.ljust(w2) + "  ->  " + repl.ljust(w3) + "  " + note)
    print(f"\n{len(rows)} arbitrary value(s) across {len(set(r[0] for r in rows))} file(s).")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", action="store_true", help="scan paths for arbitrary utilities")
    ap.add_argument("--spacing", type=float, default=4.0, help="px per spacing step (default 4)")
    ap.add_argument("args", nargs="+", metavar="VALUE|PATH")
    ns = ap.parse_args()
    global SPACING
    SPACING = ns.spacing
    return cmd_audit(ns.args) if ns.audit else cmd_values(ns.args)


if __name__ == "__main__":
    sys.exit(main() or 0)
