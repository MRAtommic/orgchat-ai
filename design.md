# Design — OrgChat Corporate AI Assistant

A locked design system for OrgChat. All UI components, dashboards, and views read and adhere to this system.

## Genre
`modern-minimal` (Technical Slate / Enterprise Studio)

## Macrostructure Family
- App Pages: `Workbench` (Disciplined 12-column grid, 1-level elevation, crisp borders)
- Modals & Overlays: `Clean Studio Dialog` (Centered or drawer, solid slate surface, no colored glow)

## Theme (Technical Slate)
- `--color-paper`: `oklch(0.14 0.01 250)` / `#090d16` (Deep Charcoal Base)
- `--color-paper-2`: `oklch(0.18 0.015 250)` / `#0f172a` (Elevated Technical Slate)
- `--color-paper-3`: `oklch(0.22 0.018 250)` / `#1e293b` (Sub-surface / Control background)
- `--color-ink`: `oklch(0.96 0.005 250)` / `#f8fafc` (Primary High-contrast text)
- `--color-ink-2`: `oklch(0.68 0.01 250)` / `#94a3b8` (Secondary metadata text)
- `--color-rule`: `oklch(0.24 0.012 250)` / `#1e293b` (Crisp 1px border rule)
- `--color-accent`: `oklch(0.68 0.16 160)` / `#10b981` (Technical Emerald)
- `--color-accent-ink`: `#022c22`
- `--color-secondary-accent`: `oklch(0.72 0.13 220)` / `#0ea5e9` (Precision Cyan)
- `--color-focus`: `oklch(0.72 0.13 220)`

## Anti-AI-Slop Directives
1. **No Purple/Indigo Default Swirls**: Abolish arbitrary `bg-gradient-to-br from-brand-600 to-indigo-700` and `via-indigo-950`. Replace with solid Technical Slate backgrounds with subtle linear borders.
2. **No Card-in-Card Glass Nesting**: Eliminate double and triple nested `.glass` containers. Use single-layer cards with clean hairline dividers (`border-t border-surface-200 dark:border-surface-800`).
3. **No Colored Glow Shadows**: Strip `shadow-2xl shadow-brand-600/20` and `shadow-amber-500/20`. Use restrained, neutral ambient shadows (`shadow-sm`, `shadow-md`).
4. **Strict Tabular Numerics**: All statistics, KPI badges, timestamps, currency amounts, and attendance timers must use `font-variant-numeric: tabular-nums`.
5. **Harmonious Radii Scale**: Limit corner radii to a disciplined scale: `rounded-lg` (8px for controls/buttons), `rounded-xl` (12px for list items), and `rounded-2xl` (16px for primary cards). Eliminate inflated `rounded-[2.5rem]`.

## Typography
- Primary Sans: `Prompt`, `Anuphan`, `Inter`, system-ui, sans-serif
- Monospace / Tabular: `ui-monospace`, `SFMono-Regular`, Menlo, Monaco, Consolas, monospace
- Heading tracking: `tracking-tight`

## Spacing & Grid
- Standard grid gap: `gap-4` to `gap-6` (16px - 24px)
- Padding rhythm: `p-4` to `p-6` for dashboard widgets, `p-6` to `p-8` for primary views.

## Component Voice
- Buttons: Solid high-contrast fill (Emerald or Dark Slate) with crisp border and subtle active feedback (`active:scale-[0.98]`).
- Status Badges: Muted background with solid text and dot indicator (e.g. `bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`).
