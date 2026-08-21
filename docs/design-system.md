# Ring design system — "Warm Paper"

Ring is a place where groups write letters to each other. The interface should
feel like good stationery: warm, calm, editorial, and quiet. This document is
the source of truth for the visual language. Every frontend change must follow
it.

Inspirations: Notion (calm neutrals, compact radii, restrained hover states),
Shopify Polaris (token discipline, focus rings, depth scale), Airbnb DLS
(typographic hierarchy), Spotify Encore (one accent, used sparingly).

---

## 1. Framework evaluation (decision record)

We evaluated whether to keep the current stack (Tailwind CSS v4 + Radix
primitives + shadcn-style owned components) or move to a packaged component
library.

| Option | Verdict | Notes |
|--------|---------|-------|
| **Keep Tailwind v4 + Radix + shadcn-owned components** | **Chosen** | Components live in our repo (`react/src/components/ui/`), so we can restyle every pixel without fighting library opinions. Radix supplies a11y/behavior. Tailwind v4's CSS-first `@theme` gives us a real token system. Zero migration risk. This is the same architectural shape Notion-quality products use. |
| Mantine / Chakra UI | Rejected | Runtime CSS-in-JS (Chakra) or its own style-props system (Mantine) conflicts with Tailwind v4 already in the codebase; wholesale component migration of ~60 feature components for no capability gain. |
| HeroUI / DaisyUI | Rejected | Strong default aesthetics that are hard to de-brand; we would be trading one recognizable template look for another. |
| MUI | Rejected | Material design language is the opposite of the warm editorial direction; heavy theme layer. |
| Park UI / Ark UI | Viable but not worth it | Equivalent capability to Radix; migration churn with no visual payoff. |

**Conclusion:** the framework was never the problem — the missing piece was a
designed token layer and consistent usage. We keep the stack and invest in
tokens + owned primitives.

---

## 2. Principles

1. **Warm paper, quiet ink.** Backgrounds are warm off-whites (light) or warm
   near-blacks (dark). Text is warm charcoal, never pure black or pure white.
2. **One accent.** Terracotta (`--color-primary`) is the only brand color. It
   marks the primary action on a screen and small identity moments (focus
   rings, active nav text, links). If everything is terracotta, nothing is.
3. **Borders before shadows.** Structure comes from 1px warm borders and
   background steps. Shadows are reserved for true elevation: menus, dialogs,
   drag states.
4. **Compact, consistent radii.** 6px for controls, 8px for cards, 12px for
   dialogs. Nothing pill-shaped except badges/avatars.
5. **Editorial typography.** UI text is Instrument Sans. Page titles, letter
   titles, and brand moments use Lora (serif) via `font-display`. Serif is a
   seasoning, not the base.
6. **No decoration without information.** No gradients, no glassmorphism, no
   glow. Hover states are background tints, not lifts; transitions are
   `transition-colors` at default duration. (Exception: interactive card grids
   may keep a subtle `hover:shadow-sm`.)
7. **Feedback has its own hues.** Success/warning/info/destructive are warm-
   adjusted and used only for status, never decoration.

---

## 3. Tokens

Defined in `react/src/app.css` under `@theme` (light) and `.dark` (dark).
Use them through Tailwind utilities (`bg-background`, `text-muted-foreground`,
`border-border`, `shadow-md`, `rounded-lg`, `font-display`, …).

### Surfaces & text

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `background` | warm paper `hsl(45 30% 98%)` | warm near-black `hsl(24 10% 10%)` | app canvas |
| `card` | white | `hsl(24 9% 12.5%)` | cards, panels, inputs sit on this |
| `popover` | white | `hsl(24 9% 13%)` | menus, popovers, dialogs |
| `muted` | `hsl(45 22% 94.5%)` | `hsl(24 8% 16.5%)` | wells, skeletons, code chips |
| `foreground` | warm ink `hsl(30 8% 21%)` | warm off-white `hsl(40 18% 89%)` | primary text |
| `muted-foreground` | `hsl(30 6% 43%)` | `hsl(35 9% 61%)` | secondary text, icons |
| `border` / `input` | `hsl(40 16% 88%)` / `85%` | `hsl(26 8% 19.5%)` / `23%` | hairlines / control borders |
| `sidebar*` | warm beige family | darker than canvas | nav shell only |

### Brand & feedback

| Token | Role |
|-------|------|
| `primary` | terracotta; primary buttons, links, active nav, focus rings |
| `secondary` | warm gray fill for secondary buttons |
| `accent` | hover/selected tint for ghost/menu items |
| `destructive` | warm red; delete actions and errors |
| `success` / `warning` / `info` | status badges, callouts (new) |

Tinted chips: `bg-success/10 text-success border-success/20` (same pattern for
warning, info, destructive, primary).

### Depth (shadows)

Warm-tinted, layered. `shadow-2xs`…`shadow-2xl` are overridden globally.

| Level | Use |
|-------|-----|
| `shadow-xs` | resting controls (buttons, inputs) — barely visible |
| `shadow-sm` | interactive card hover |
| `shadow-md` | dropdown menus, tooltips, popovers |
| `shadow-lg` | command palette, sheets |
| `shadow-xl` | dialogs |

### Radii

| Utility | Value | Use |
|---------|-------|-----|
| `rounded-sm` | 4px | kbd chips, tiny tags |
| `rounded-md` | 6px | buttons, inputs, menu items |
| `rounded-lg` | 8px | cards, panels, wells |
| `rounded-xl` | 12px | dialogs, sheets, command palette |
| `rounded-full` | — | badges, avatars, dots |

### Typography

| Utility | Font | Use |
|---------|------|-----|
| `font-sans` (default) | Instrument Sans Variable | all UI text |
| `font-display` | Lora Variable | page titles (`h1`), letter/question titles, auth brand, empty-state headlines |
| `font-mono` | system mono | ids, code, kbd |

Scale (use these, don't invent): page title `font-display text-2xl md:text-3xl
font-semibold tracking-tight`; section heading `text-base font-semibold`;
body `text-sm`; secondary `text-sm text-muted-foreground`; caption/meta
`text-xs text-muted-foreground`.

---

## 4. Recipes

**Page container**
```tsx
<div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
  <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">…</h1>
  <p className="mt-1 text-sm text-muted-foreground">…</p>
```

**Card (static)** — `rounded-lg border bg-card` (Card primitive does this).
**Card (clickable)** — add `transition-shadow hover:shadow-sm` — no translate,
no scale.

**Menus/popovers** — `rounded-lg border bg-popover shadow-md`.
**Dialogs** — `rounded-xl border bg-popover shadow-xl` (overlay
`bg-foreground/25 backdrop-blur-[2px]` light-warm, not pitch black).

**Status badge** — Badge primitive variants: `success`, `warning`, `info`,
`destructive`, `primary` (tinted), `secondary` (neutral), `outline`.

**Empty state**
```tsx
<div className="flex flex-col items-center rounded-lg border border-dashed px-6 py-16 text-center">
  <Icon className="h-8 w-8 text-muted-foreground/60" strokeWidth={1.5} />
  <h3 className="mt-4 font-display text-lg font-medium">Nothing here yet</h3>
  <p className="mt-1 max-w-sm text-sm text-muted-foreground">…</p>
  <Button className="mt-6">…</Button>
</div>
```

**Focus** — never remove; primitives ship
`focus-visible:border-ring focus-visible:ring-ring/30 focus-visible:ring-[3px]`.

**Icons** — lucide only, `h-4 w-4` in controls, `strokeWidth={1.5}` for
decorative/empty-state icons, `text-muted-foreground` unless status-colored.

---

## 5. Hard rules

1. **Never** use raw palette classes in feature code: `bg-white`, `bg-black`,
   `*-gray-*`, `*-slate-*`, `*-zinc-*`, `*-stone-*`, `*-neutral-*`, or hex
   colors. Use semantic tokens. (Lone exception: `text-white` inside
   photo-overlay chrome, e.g. image carousels.)
2. **Never** use color-suffixed utilities for status (`bg-green-100
   text-green-800`…). Use `success`/`warning`/`info`/`destructive` tokens.
3. **No gradients, no glassmorphism** (`backdrop-blur` + translucent white),
   no `hover:-translate-y-*`, no `hover:scale-*` on cards or buttons.
4. **Dark mode is automatic.** Tokens flip; feature code should almost never
   contain `dark:` overrides. If you need one, the token choice is wrong.
5. **Radii/shadow/typography come from the scales above** — no `rounded-2xl`,
   `shadow-2xl` (dialogs cap at `shadow-xl`), or ad-hoc text sizes in feature
   code.
6. New UI goes through primitives in `react/src/components/ui/` first; extend
   variants there instead of inlining one-off styles.

---

## 6. File map

| Concern | File |
|---------|------|
| Tokens (all) | `react/src/app.css` |
| Fonts | `@fontsource-variable/instrument-sans`, `@fontsource-variable/lora` (imported at top of `app.css`) |
| Animations | `tw-animate-css` (imported in `app.css`; powers `animate-in/out` in primitives) |
| Primitives | `react/src/components/ui/*` |
| PWA/browser chrome color | `react/vite.config.ts` manifest `theme_color` + `background_color` |
