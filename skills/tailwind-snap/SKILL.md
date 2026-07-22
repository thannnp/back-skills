---
name: tailwind-snap
description: Snap px values from a design onto the nearest Tailwind token instead of arbitrary values like text-[13px] or p-[15px]. Use when implementing a Figma design in code, when writing Tailwind classes from design specs or CSS, and when auditing existing markup for arbitrary values.
---

# Snap to the scale

A design tool emits exact px. Code that keeps them — `text-[13px]`, `p-[15px]`, `rounded-[7px]` — has no scale left: nothing lines up, nothing is reusable, and the theme stops being the source of truth. Every value **snaps** onto the nearest token on its scale, and a 1–2px drift from the mockup is the accepted trade.

Snapping applies to every value you take from a design — font size, line height, padding, margin, gap, width, height, radius, border, shadow, tracking, opacity — not just the ones that look off.

Open your reply with the line `▸ /tailwind-snap` before anything else, so the user can see the skill is driving this turn.

## 1. Read the theme first

Project tokens beat framework defaults. A project that defines `--spacing: 0.5rem` or its own `--text-body` changes every answer below.

```
grep -rln "@theme" --include=*.css .
```

Read each `@theme` block and note what it overrides and what it adds. If there is no `@theme` block, the defaults in [`reference/tokens.md`](reference/tokens.md) apply as-is.

**Done when** you can state the project's spacing base and name its font-size, radius, and color tokens — or you have confirmed the project ships no `@theme` block.

## 2. Snap every value

Three kinds of scale; which one a utility belongs to decides how it snaps.

### Multiplier scales — round to the nearest step

Value = `n × --spacing` (4px by default). `n` can be a half step (`p-1.5`), any integer with no upper bound (`p-13`), so **any even px snaps exactly and any odd px is at most 1px off**.

Utilities: `p*` `m*` `gap*` `space-*` `w` `h` `size` `min-*` `max-*` `basis` `inset*` `top/right/bottom/left` `translate*` `leading` `scroll-*` `indent`.

Snap: `n = px / 4`, rounded to the nearest 0.5. Ties go to the whole step — 15px → `p-4`, not `p-3.5`.

### Named scales — round to the nearest entry, ties go down

These have no numeric form, so the nearest entry is the only option.

| Scale | Entries (px) |
|---|---|
| `text-*` | xs 12 · sm 14 · base 16 · lg 18 · xl 20 · 2xl 24 · 3xl 30 · 4xl 36 · 5xl 48 · 6xl 60 · 7xl 72 · 8xl 96 · 9xl 128 |
| `rounded-*` | none 0 · xs 2 · sm 4 · md 6 · lg 8 · xl 12 · 2xl 16 · 3xl 24 · 4xl 32 · full 9999 |
| `blur-*` | xs 4 · sm 8 · md 12 · lg 16 · xl 24 · 2xl 40 · 3xl 64 |
| `shadow-*` | 2xs · xs · sm · md · lg · xl · 2xl — match by intent (spread and darkness), not by a number |
| `tracking-*` | tighter −0.05em · tight −0.025em · normal 0 · wide 0.025em · wider 0.05em · widest 0.1em |
| `font-*` (weight) | thin 100 … medium 500 · semibold 600 · bold 700 … black 900 — designs land on these exactly |

13px font → `text-xs`. 47px → `text-5xl`. 7px radius → `rounded-md`.

### Literal scales — write the number, never a bracket

The number *is* the value: `border-3` (3px), `z-30`, `opacity-65`, `duration-350`, `order-2`. There is nothing to snap; an arbitrary value here is pure noise.

### Font size with line height

Figma hands you both. One utility carries them: `text-<size>/<leading>`, where the leading half is a multiplier step. 13px/18px → `text-xs/4.5`. Reach for the modifier whenever the design's line height differs from the token's built-in one.

### Colors

Snap a hex to a **theme token whose value it matches**. When nothing in the theme matches, keep the hex as an arbitrary value and flag it in the report as a missing token — a guessed shade (`bg-blue-500` for `#3B82F6`) is worse than an honest arbitrary value, because it looks tokenized while being wrong.

### The one escape hatch

Keep an arbitrary value only when the property has no scale at all, when the number must match an external constraint exactly (an asset's intrinsic size, a third-party widget's height), or when it is a sub-2px hairline like `w-[1px]` for a divider, where the nearest step is either 0 or double. Every survivor goes in the report.

## 3. Report the drift

Close the work with a table of what moved:

| Design | Class | Token value | Drift |
|---|---|---|---|
| font 13px | `text-xs` | 12px | −1px |
| padding 15px | `p-4` | 16px | +1px |
| `#2F6FEB` | `bg-[#2F6FEB]` | — | no theme token |

**Done when** every px value from the design appears in the code as a token or in this table as a row. Rows with zero drift are noise — leave them out.

## Auditing existing code

`scripts/snap.py --audit <paths>` walks files and lists every arbitrary utility with its suggested replacement and drift. Use it to scope the work, apply the replacements yourself, and finish with the same drift table. `scripts/snap.py 13 15 7` answers a one-off "what does this px become".

Both are conveniences — the rules above are the authority, and the script does not know the project's `@theme` overrides.
