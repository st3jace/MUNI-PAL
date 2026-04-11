# Muni-Pal Brand Guidelines

**Version:** 1.0
**Date:** 2026-03-31
**Owner:** CBO, Launch Shop

---

## 1. Brand Architecture

Muni-Pal is an **Endorsed Brand** under the Launch Shop / Innovation Factory parent. It has its own domain, identity, and voice — with a light parent endorsement.

- **Product domain:** muni-pal.io
- **Parent relationship:** "A Launch Shop product" (footer endorsement)
- **Corporate domain:** muni-pal.io (product domain; parent company: Innovation Factory)

Muni-Pal is the first Tier 1 product — customer-facing, trust-critical, independently branded.

---

## 2. Positioning

### Identity Statement

**Muni-Pal is AI-powered municipal bond intelligence for healthcare operators.**

It turns evidence from real EMMA transactions into actionable bond structuring decisions — replacing advisor opacity with data transparency.

### Who It's For

- Healthcare CFOs and finance directors planning bond issuances
- Hospital systems and healthcare operators (deals $10M+)
- Finance teams that want data before they hire advisors

### Who It's NOT For

- Sub-$10M deals
- Non-healthcare issuers (future expansion, not now)
- General financial advice seekers
- Investors (that's Deal House)

### Positioning Statement

> For healthcare operators planning bond issuances, Muni-Pal is the evidence-first intelligence platform that benchmarks your deal against real EMMA transactions — so you walk into the room knowing what good looks like, what it costs, and where deals fall apart.

### Competitive Frame

Muni-Pal does not compete with financial advisors. It makes the issuer smarter before, during, and after advisor engagement. The frame is: **"Your advisors won't tell you this for free. We will."**

---

## 3. Color Palette

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Muni Navy** | `#1B3A5C` | Primary background, headers, sidebar, navigation, cards |
| **Muni Teal** | `#2DAEAC` | Accent text, icons, badges, highlights, monogram |
| **Muni Orange** | `#E8913A` | CTAs, action buttons, conversion elements |

### Secondary Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Muni Gold** | `#f59e0b` | Sparse secondary accent, warnings |
| **White** | `#ffffff` | Body text on dark backgrounds, page backgrounds |
| **Gray 300** | Tailwind `gray-300` | Secondary text on dark backgrounds |

### Tailwind Config Reference

```js
muni: {
  navy: '#1B3A5C',
  teal: '#2DAEAC',
  orange: '#E8913A',
  gold: '#f59e0b',
}
```

### Color Rules

- **Navy** is the dominant brand color. It signals authority and seriousness.
- **Teal** is the differentiator. It breaks the navy monotone and signals intelligence/data.
- **Orange** is reserved for actions. Every orange element should drive a behavior (click, sign up, start).
- Never use orange for decoration. Never use teal for CTAs.
- Dark backgrounds (navy-to-indigo gradients) for hero sections and emphasis areas.
- White backgrounds for content-heavy sections and readability.

---

## 4. Typography

### Font Stack

System sans-serif (no custom fonts):

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Hierarchy

| Element | Weight | Size | Notes |
|---------|--------|------|-------|
| H1 (Hero) | Bold | 2xl–4xl (responsive) | Used in hero sections, landing pages |
| H2 (Section) | Bold | xl–2xl | Section headers |
| H3 (Card) | Semibold | lg | Card titles, subsections |
| Body | Normal | base–lg | Primary content |
| Label | Semibold | sm | Uppercase tracking-wide, teal color for category labels |
| Caption | Normal | sm | Gray text, supplementary information |

### Typography Rules

- Headlines: direct, outcome-focused, no jargon
- Body: clear, evidence-based tone — not marketing fluff
- Labels: uppercase, tracking-wide, teal — used sparingly for category identifiers
- No italics for emphasis (use bold or teal color instead)

---

## 5. Logo & Favicon

### Monogram (Primary Mark)

Navy rounded rectangle with teal "M":
- Background: `#1B3A5C`, border-radius 15%
- Letter: `#2DAEAC`, bold, centered

Used as favicon, app icon, and compact brand mark.

### Full Logo

`Muni-Pal_Logo.jpg` — 2048x2048px, 300 DPI. Use for documents, presentations, and full-size placements.

### Logo Rules

- Monogram is the default in UI (sidebar, favicon, tab icon)
- Full logo for external materials, documents, and larger placements
- Minimum clear space: equal to the height of the "M" on all sides
- Never stretch, rotate, recolor, or add effects to the logo
- On dark backgrounds: use monogram as-is (navy bg + teal M)
- On white backgrounds: monogram as-is, or navy wordmark "Muni-Pal"

---

## 6. Voice & Tone

### Brand Voice

| Attribute | What it means | What it doesn't mean |
|-----------|---------------|----------------------|
| **Direct** | Lead with the point. No preamble. | Blunt or rude |
| **Evidence-based** | Claims backed by data (EMMA corpus, DSCR benchmarks) | Academic or dry |
| **Outcome-driven** | Every message connects to a result the reader wants | Salesy or hyperbolic |
| **Professional** | Serious instrument for serious decisions | Stuffy or corporate |

### Tone by Context

| Context | Tone | Example |
|---------|------|---------|
| Landing page hero | Confident, slightly provocative | "Your advisors won't tell you this for free." |
| Product UI | Clean, functional, helpful | "3 gaps identified. View recommendations." |
| Engagement path / pricing | Transparent, structured | "Free → $15K–$25K → $45K–$75K" |
| Error states | Calm, actionable | "Report generation failed. Try again or contact support." |

### Copy Anti-Patterns

- No "revolutionary," "cutting-edge," or "game-changing"
- No vague promises ("transform your bond process")
- No exclamation marks in product copy
- No startup slang ("disrupt," "pivot," "hack")
- No first-person plural without specificity ("We help you" → "Muni-Pal benchmarks your deal against 866 transactions")

---

## 7. Meta Tags & OG Properties

### Main Application (muni-pal.io)

```html
<title>Muni-Pal BFMS</title>
<meta name="description" content="Muni-Pal — Bond Finance Management System for municipal bond issuers.">
<meta property="og:title" content="Muni-Pal BFMS">
<meta property="og:description" content="Bond Finance Management System for municipal bond issuers.">
<meta property="og:url" content="https://muni-pal.io">
<meta property="og:image" content="https://muni-pal.io/favicon.svg">
<meta property="og:type" content="website">
<meta name="theme-color" content="#1B3A5C">
```

### Healthcare Landing Page (muni-pal.io/healthcare)

```html
<title>Healthcare Bond Readiness — Muni-Pal</title>
<meta name="description" content="Healthcare bond market intelligence — benchmarks from 866 EMMA transactions. Know what good looks like, what it costs, and where deals fall apart.">
<meta property="og:title" content="Healthcare Bond Readiness — Muni-Pal">
<meta property="og:description" content="Healthcare bond market intelligence — benchmarks from 866 EMMA transactions.">
<meta property="og:url" content="https://muni-pal.io/healthcare">
<meta property="og:image" content="https://muni-pal.io/favicon.svg">
<meta property="og:type" content="website">
```

### Web Manifest

```json
{
  "name": "Muni-Pal",
  "short_name": "Muni-Pal",
  "description": "Bond Finance Management System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1B3A5C"
}
```

---

## 8. UI Components

### Buttons

| Type | Background | Text | Usage |
|------|-----------|------|-------|
| Primary CTA | `#E8913A` (hover: `#d47e2e`) | White | Sign up, start, submit — one per section max |
| Secondary | Transparent, white border | White | Alternative actions alongside primary CTA |
| Tertiary | Transparent | Teal or white with arrow | "Learn more" style links |

### Cards

- White background with subtle shadow (`shadow-md`)
- Navy or teal icon containers (rounded, 48px)
- Heading in dark text, body in gray-600

### Badges

- Teal background for positive states (approved, active)
- Orange for pending/attention states
- Navy for neutral/informational
- Red for rejected/error states

### Navigation

- Navy sidebar (`#1B3A5C`) with white text
- Teal monogram at top-left
- Active state: lighter navy or teal accent

---

## 9. Footer Endorsement

Every page served from muni-pal.io must include the endorsed brand footer:

```
Muni-Pal — A Launch Shop product
© 2026 Launch Shop. All rights reserved.
```

The endorsement is subtle — small text, gray color, below the main footer content. It connects back to the parent brand without competing with the product identity.

---

## 10. Content Architecture

### Landing Page Hierarchy

1. **Category label** — Uppercase, teal, tracking-wide (e.g., "Healthcare Bond Intelligence")
2. **Hero headline** — Bold, outcome-driven, slightly provocative
3. **Supporting paragraph** — Evidence-backed, specific numbers
4. **Primary CTA** — Orange button, clear action
5. **Value props** — 3 cards with icon + headline + copy
6. **Social proof** — Real numbers (866 transactions, 3.20x DSCR, 5 risk categories)
7. **Engagement path** — Clear pricing ladder (Free → Paid)
8. **Footer** — Endorsed brand tagline

### Key Statistics (Current Corpus)

Use these in marketing materials — they are drawn from real EMMA data:

| Stat | Value | Context |
|------|-------|---------|
| EMMA transactions analyzed | 866 | Healthcare sector corpus |
| Median healthcare DSCR | 3.20x | Benchmark figure |
| Risk categories scored | 5 | Issuer risk framework |
| Financial reports in corpus | 1,318 | Supporting data depth |

---

## 11. Domain & URL Structure

| URL | Purpose |
|-----|---------|
| `muni-pal.io` | Product home / tools index |
| `muni-pal.io/healthcare` | Healthcare sector landing page |
| `muni-pal.io/tools/*` | Sensing tools (MIR, Readiness Assessment, Benchmarking, Credit Spread) |
| `muni-pal.io/api/*` | Backend API |

### Sector Landing Page Convention

Each sector gets its own landing page at the root level: `/healthcare`, `/education`, `/housing`, `/waste`, `/industrial`. This creates a scalable, sector-specific entry point architecture. Tools remain shared at `/tools/*`.

### Redirect Plan

| From | To | Type |
|------|----|------|
| `readiness.elaunchshop.com` (deprecated) | `muni-pal.io/healthcare` | 301 — completed |

---

## 12. Brand Governance

### What Can Change Without CBO Review

- Bug fixes to existing brand elements
- New pages following established patterns
- Internal tool styling (Tier 3 platforms)

### What Requires CBO Review

- Any new customer-facing page or landing page
- Changes to the color palette or typography
- New positioning statements or taglines
- Any external-facing content (Tier 3 decision per AGENTS.md)
- Modifications to the logo or monogram

### What Requires CEO + Board Approval

- New Tier 1 domain purchases (Deal House, Champion Social)
- Changes to the brand architecture model
- Pricing/offer messaging that implies commitments
