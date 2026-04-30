---
version: alpha
name: Stuck LLM
description: Design system for a local-first conversational stock-analysis workspace.
colors:
  primary: "#171717"
  secondary: "#525866"
  background: "#F8FAFC"
  surface: "#FFFFFF"
  surface-muted: "#EEF2F6"
  border: "#D7DEE8"
  accent: "#157A6E"
  on-accent: "#FFFFFF"
  positive: "#0A6B4D"
  negative: "#C2413A"
  warning: "#B7791F"
  chart-price: "#2563EB"
typography:
  h1:
    fontFamily: Inter
    fontSize: 2rem
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: 0em
  h2:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: 0em
  body:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0em
  label:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: 0em
  mono:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: 0em
rounded:
  sm: 4px
  md: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
components:
  app-shell:
    backgroundColor: "{colors.background}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  panel-muted:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 10px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 10px
  evidence-chip-positive:
    backgroundColor: "{colors.positive}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 6px
  evidence-chip-negative:
    backgroundColor: "{colors.negative}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 6px
  evidence-chip-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 6px
  chart-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.chart-price}"
    rounded: "{rounded.md}"
    padding: 12px
  divider:
    backgroundColor: "{colors.border}"
    textColor: "{colors.primary}"
    height: 1px
  code-inline:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.primary}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: 4px
---

## Overview

Stuck LLM should feel like a practical analysis terminal for investment research, not a marketing page. The interface should be calm, dense, and scannable, with enough contrast to separate conversation, evidence, prices, and operational status.

## Colors

Use neutral surfaces for most workspace areas, teal for primary actions, blue for price charts, green for constructive evidence, red for adverse evidence, and amber for warnings. Avoid single-hue palettes and avoid decorative gradients.

## Typography

Use compact, readable type. Reserve large headings for actual workspace titles; panels, chat cards, charts, and evidence tables should use smaller headings and labels. Letter spacing is always zero.

## Layout

Favor a ChatGPT-style workspace: left navigation rail, central conversation, and focused side or panel views for analysis, snapshot, and backtest. Charts must have stable dimensions and responsive constraints so loading, hover, and empty states do not resize the layout.

## Elevation & Depth

Use borders and subtle surface contrast instead of shadows. Do not nest cards inside cards. Use framed panels only for repeated items, modals, and concrete tools such as charts or source lists.

## Shapes

Use 4px radius for controls and 8px radius for larger panels. Avoid pill-shaped controls unless they represent compact tags or segmented state.

## Components

Price charts should be readable in both chat messages and expanded workspace panels. Evidence chips must clearly separate positive, negative, and warning states. Buttons should use icons when the action is common and labels when the command needs precision.

## Do's and Don'ts

Do show source dates, provider status, and stale-data state near analysis output. Do keep price data visually separate from LLM evidence. Do not use future prices as historical evidence. Do not add decorative orbs, oversized hero sections, or explanatory marketing copy inside the app.
