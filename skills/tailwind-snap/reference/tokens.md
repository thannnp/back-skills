# Tailwind v4 default scale

Values below were read from `tailwindcss@4.3.1/theme.css` and verified by compiling each candidate class. Root font size assumed 16px (`1rem = 16px`).

## Spacing base

```
--spacing: 0.25rem   /* 4px */
```

Every multiplier utility resolves to `calc(var(--spacing) * n)`. Verified generated: `p-0.5` `p-1.5` `p-2.5` `p-3.5` `p-4.5` `p-7` `p-13` `w-13` `h-13` `min-h-13` `basis-13` `inset-3.5` `translate-3.5` `space-y-4.5` `leading-5.5` `size-4.5`. There is no cap and no gap in the scale — `n` is free.

Families on this scale: `p px py pt pr pb pl ps pe`, `m mx my mt mr mb ml ms me`, `gap gap-x gap-y`, `space-x space-y`, `w h size`, `min-w min-h max-w max-h`, `basis`, `inset inset-x inset-y top right bottom left start end`, `translate translate-x translate-y`, `leading`, `scroll-m* scroll-p*`, `indent`.

## Font size

| Token | rem | px | Paired line-height |
|---|---|---|---|
| `text-xs` | 0.75 | 12 | 16px |
| `text-sm` | 0.875 | 14 | 20px |
| `text-base` | 1 | 16 | 24px |
| `text-lg` | 1.125 | 18 | 28px |
| `text-xl` | 1.25 | 20 | 28px |
| `text-2xl` | 1.5 | 24 | 32px |
| `text-3xl` | 1.875 | 30 | 36px |
| `text-4xl` | 2.25 | 36 | 40px |
| `text-5xl` | 3 | 48 | 1 (48px) |
| `text-6xl` | 3.75 | 60 | 1 |
| `text-7xl` | 4.5 | 72 | 1 |
| `text-8xl` | 6 | 96 | 1 |
| `text-9xl` | 8 | 128 | 1 |

`text-<number>` does **not** exist — font size is a named scale only. The `text-sm/6` modifier form is verified: `font-size: var(--text-sm); line-height: calc(var(--spacing) * 6)`.

## Line height

Named: `leading-tight` 1.25 · `leading-snug` 1.375 · `leading-normal` 1.5 · `leading-relaxed` 1.625 · `leading-loose` 2 · `leading-none` 1 (static utility, not a theme variable).

Numeric: `leading-<n>` on the spacing scale — `leading-6` = 24px.

Figma gives line height in px, so the numeric form is usually the match; use a named one when the design specifies a ratio.

## Border radius

| Token | rem | px |
|---|---|---|
| `rounded-none` | 0 | 0 |
| `rounded-xs` | 0.125 | 2 |
| `rounded-sm` | 0.25 | 4 |
| `rounded-md` | 0.375 | 6 |
| `rounded-lg` | 0.5 | 8 |
| `rounded-xl` | 0.75 | 12 |
| `rounded-2xl` | 1 | 16 |
| `rounded-3xl` | 1.5 | 24 |
| `rounded-4xl` | 2 | 32 |
| `rounded-full` | — | 9999 |

`rounded-<number>` does **not** exist (verified). Sides and corners take the same scale: `rounded-t-xl`, `rounded-bl-sm`, `rounded-s-md`.

## Border width

Literal px, dynamic: `border` = 1px, `border-0`, `border-2`, `border-3`, `border-4`, `border-8` — any integer compiles (`border-3` verified → `border-width: 3px`). Same for `border-x-*`, `border-t-*`, and `divide-*`.

## Shadows

| Token | Value |
|---|---|
| `shadow-2xs` | `0 1px rgb(0 0 0 / 0.05)` |
| `shadow-xs` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| `shadow-sm` | `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` |
| `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` |
| `shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` |
| `shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` |
| `shadow-2xl` | `0 25px 50px -12px rgb(0 0 0 / 0.25)` |

Also `inset-shadow-2xs|xs|sm`, `drop-shadow-xs…2xl`, `text-shadow-2xs…lg`.

Match a Figma shadow by its blur radius and opacity together. A design shadow rarely equals a token exactly; a shadow that is deliberately brand-specific (colored, layered) is a theme token worth adding rather than an arbitrary value repeated across files.

## Blur

`blur-xs` 4px · `blur-sm` 8 · `blur-md` 12 · `blur-lg` 16 · `blur-xl` 24 · `blur-2xl` 40 · `blur-3xl` 64.

## Tracking

`tracking-tighter` −0.05em · `tight` −0.025em · `normal` 0 · `wide` 0.025em · `wider` 0.05em · `widest` 0.1em. No numeric form (verified: `tracking-4` does not compile).

Figma reports letter spacing in px or %. Convert to em against the font size: 0.4px on a 16px font = 0.025em = `tracking-wide`.

## Font weight

`thin` 100 · `extralight` 200 · `light` 300 · `normal` 400 · `medium` 500 · `semibold` 600 · `bold` 700 · `extrabold` 800 · `black` 900. Designs land on these exactly; a weight in between means a variable font, which is a theme addition.

## Containers (max-width scale)

`3xs` 16rem/256px · `2xs` 18/288 · `xs` 20/320 · `sm` 24/384 · `md` 28/448 · `lg` 32/512 · `xl` 36/576 · `2xl` 42/672 · `3xl` 48/768 · `4xl` 56/896 · `5xl` 64/1024 · `6xl` 72/1152 · `7xl` 80/1280.

`max-w-*` accepts both this scale and the spacing scale (`max-w-96` = 384px), plus fractions (`w-1/2`).

## Breakpoints

`sm` 40rem/640px · `md` 48/768 · `lg` 64/1024 · `xl` 80/1280 · `2xl` 96/1536. A Figma frame width maps to the breakpoint at or below it, not to an arbitrary `min-[1180px]:`.

## Free numeric utilities

No snapping needed — the number is the value, and any integer compiles: `z-<n>`, `opacity-<n>` (percent), `duration-<n>` (ms), `delay-<n>`, `order-<n>`, `grid-cols-<n>`, `col-span-<n>`, `border-<n>`.

## If the project is on v3

The names moved in v4. Under v3, snap to these instead:

- Radius: `rounded-sm` 2px · `rounded` 4 · `rounded-md` 6 · `rounded-lg` 8 · `rounded-xl` 12 · `rounded-2xl` 16 · `rounded-3xl` 24. There is no `rounded-xs` or `rounded-4xl`.
- Shadow: `shadow-sm` · `shadow` · `shadow-md` … — one step down in naming, and no `shadow-2xs`.
- Blur: `blur-sm` 4px · `blur` 8 · `blur-md` 12 …
- Spacing is a **fixed** scale, not a multiplier: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, then whole steps 4–16, then 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 72, 80, 96. `p-13` and `p-4.5` do not exist — snap to a step that does, or add it to `tailwind.config.js`.
- Tokens live in `tailwind.config.js` (`theme.extend`), not `@theme`.
