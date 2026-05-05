# Presentation Cognitive Engineering

## Design Philosophy

Office Suite treats presentation design as **cognitive engineering** -- the deliberate structuring of visual information to optimize human perception, comprehension, and memory formation. Every design decision must answer: does this reduce the audience's cognitive cost of extracting the intended message?

### Core Principles

1. **Pre-attentive dominance**: The human visual system processes color, size, orientation, and motion in under 200ms before conscious thought. Presentation design must exploit pre-attentive features to establish visual hierarchy before the audience reads a single word.

2. **Dual-channel encoding**: Verbal and visual information are processed through separate cognitive channels (Paivio, 1986). Slides that pair concise text with semantically aligned visuals achieve significantly higher retention than text-only or visual-only approaches.

3. **Working memory budget**: Miller's Law constrains working memory to 7+/-2 chunks. Each slide must present information in cognitively manageable units. A "chunk" is not a bullet point -- it is a meaningful information unit that the audience can process as a single concept.

4. **Progressive disclosure**: Information should be revealed in layers of increasing detail. The slide title carries the conclusion. The visual carries the pattern. The text carries the evidence. The audience self-selects their depth of engagement.

5. **Spatial contiguity**: Related information must be spatially proximate (Mayer, 2001). Labels must be adjacent to their referents. Legends must be embedded in charts, not placed in distant corners. Card containers enforce spatial contiguity by definition.

---

## System Architecture

```
User Intent
  |
  v
Phase 1: Cognitive Context Analysis
  |-- Audience cognitive profile
  |-- Information density target
  |-- Visual-verbal ratio target
  |
  v
Phase 2: Information Architecture
  |-- Content mode selection (architectural / distilled / foraged)
  |-- structure contract (outline.md)
  |
  v
Phase 3: Visual System Design
  |-- Design mode selection (zero-based / analogical / container)
  |-- style contract (design.md)
  |
  v
Phase 4: Materialization
  |-- deck.yml (theme + styles + page manifest)
  |-- pages/*.yml (one per slide)
  |
  v
Phase 5: Verification
  |-- Structural validation (YAML, bounds, references)
  |-- Cognitive validation (hierarchy, density, contiguity)
  |-- Render validation (PPTX output)
```

---

## Phase 1: Cognitive Context Analysis

Before generating any content, build a cognitive profile of the presentation context.

### 1.1 Audience Cognitive Profile

| Factor | Low Expertise | Medium Expertise | High Expertise |
|--------|--------------|-----------------|----------------|
| Concept density per slide | 1-2 | 2-3 | 3-5 |
| Jargon tolerance | Minimal | Moderate | Full domain vocabulary |
| Visual metaphor need | High (analogies essential) | Moderate | Low (direct representation) |
| Data complexity tolerance | Simple aggregates | Trends and comparisons | Multivariate analysis |
| Attention span modeling | 20-30 min | 30-45 min | 45-60 min |

### 1.2 Information Density Target

Information density is the ratio of semantic content to available canvas area. It is NOT the ratio of text to whitespace -- a data-dense slide with a large chart and minimal text has high information density.

| Density Level | Fill Rate | Use Case |
|---------------|-----------|----------|
| Sparse (40-55%) | One core idea with generous breathing room | Brand storytelling, keynote moments, emotional pivots |
| Balanced (55-70%) | One topic with supporting evidence | General business, education, standard content |
| Dense (70-85%) | One topic with multiple evidence streams | Data analysis, research, technical comparison |
| Saturated (85%+) | Maximum information per canvas unit | Reference slides, financial appendix, data dashboards |

### 1.3 Content Mode Selection

Based on the user's input type, select an information architecture strategy:

| Input Type | Mode | Architecture Strategy |
|-----------|------|----------------------|
| Pre-structured outline | Architectural | Parse and map existing structure to slide system |
| Long document | Distilled | Extract information scent trails, rebuild hierarchy |
| Topic only | Foraged | Research, cluster, and synthesize from scratch |

Read the corresponding guideline:
- Architectural: `guideline/content/outline_mode.md`
- Distilled: `guideline/content/summary_mode.md`
- Foraged: `guideline/content/search_mode.md`

### 1.4 Design Mode Selection

Based on visual references provided, select a visual system strategy:

| Reference Type | Mode | Strategy |
|---------------|------|----------|
| No reference | Zero-based | Derive visual system from cognitive context |
| Images/website | Analogical | Extract visual principles, map to Office Suite tokens |
| Template PPTX | Container | Extract structural framework, fill with new content |

Read the corresponding guideline:
- Zero-based: `guideline/design/creative_mode.md`
- Analogical: `guideline/design/reference_mode.md`
- Container: `guideline/design/template_mode.md`

---

## Phase 2: Information Architecture

Content mode determines how information is structured. See the content mode files for detailed workflows.

### Output: structure contract (outline.md)

Every outline.md must include:

1. **Cognitive context**: Audience profile, density target, content mode
2. **Narrative arc**: The emotional and logical progression across the deck
3. **Per-slide specification**:
   - Slide type (cover / toc / chapter / content / closing)
   - Key message (one sentence -- the single thing the audience should remember)
   - Chunk inventory (list of information chunks to present)
   - Saliency target (which chunk should dominate pre-attentive processing)
   - Layout pattern (from the pattern library)
   - Evidence type (chart / table / diagram / image / text)

---

## Phase 3: Visual System Design

### 3.1 Color System as Semantic Coding

Office Suite enforces a strict 6-color token system. Colors are not decorative -- they are **semantic carriers** that encode meaning through consistent association.

| Token | Semantic Role | Pre-attentive Function |
|-------|--------------|----------------------|
| `bg_primary` | Page ground | Figure-ground separation |
| `bg_surface` | Card ground | Content grouping (Gestalt proximity) |
| `border` | Boundary signal | Spatial containment |
| `accent` | Attention attractor | Saliency beacon (highest contrast) |
| `text_primary` | Primary meaning | Semantic content |
| `text_muted` | Secondary context | Metadata, labels, navigation |

### 3.2 Typography as Information Hierarchy

The 4-level type scale is not a style preference -- it is a **hierarchy encoding system**. Each level creates a distinct visual weight that the eye processes in priority order.

| Level | Size | Weight | Cognitive Role |
|-------|------|--------|---------------|
| H1 | 32-36pt | 700 | **Salience anchor** -- the first thing the eye targets |
| H2 | 14-16pt | 700 | **Category label** -- groups content into semantic blocks |
| Body | 12-13pt | 400 | **Evidence carrier** -- supports the key message |
| Caption | 9-10pt | 400 | **Metadata layer** -- sources, dates, navigation |

**Constraint**: Maximum 6 distinct font sizes per slide. Exceeding this fragments the hierarchy and increases search time for the audience. Rich typographic compositions (data posters, magazine layouts) may use up to 6 levels.

### 3.3 Card System as Cognitive Container

Cards are not decoration. They are **cognitive containers** that exploit Gestalt proximity principle: elements enclosed in a shared boundary are perceived as belonging together.

```
Card = rounded_rectangle(bg_surface) + border(border_color)
  |
  +-- H2 title (category label)
  +-- Divider line (visual separator)
  +-- Body content (evidence)
  +-- Caption (optional metadata)
```

Rules:
- One card = one information chunk
- No card nesting (destroys the containment signal)
- Recommended radius: 3mm (varies 0-8mm for stylistic effect; keep consistent within a slide)

### 3.4 Composition Families as Attention Scaffolds

Each composition defines an **attention routing path** -- the sequence of eye fixations the audience will follow. Built-in templates are examples of renderer-safe structures, not mandatory layouts.

| Composition | Attention Path | Best For |
|-------------|---------------|----------|
| `editorial_opener` | Image/visual field -> title -> metadata | First/last impressions |
| `annotated_artifact` | Artifact -> labels -> conclusion | Explaining objects, screenshots, images, diagrams |
| `data_poster` | Oversized number -> claim -> proof notes | One decisive metric |
| `narrative_timeline` | Path/ribbon/shelf progression | Origin, process, journey |
| `comparison_axis` | Pole A -> tension -> Pole B | Tradeoffs, before/after, old/new |
| `quote_wall` | Dominant quote -> author -> supporting fragments | Reflection, culture, voices |
| `process_field` | Central method -> steps -> outcome | Frameworks and methods |
| `magazine_spread` | Headline -> image/figure -> margin note | Editorial explanation |
| `map_or_hub` | Center concept -> satellite details | Ecosystems, factors, stakeholders |
| `card_grid` | Z-pattern across equal containers | True inventories or parallel items only |

### 3.5 Spacing Rhythm

Spatial rhythm uses consistent intervals to create predictability, reducing the audience's spatial search cost:

```text
Page margins:   20mm L/R, 16mm top, 12mm bottom (recommended)
Title band:     y 16-32mm
Body region:    y 40-116mm
Footer:         y 124-132mm
Card gap:       4mm recommended (2-8mm depending on density intent)
Group gap:      8mm (semantic boundary)
Card padding:   4mm internal (adjust 2-6mm for density control)
```

---

## Phase 3.5: Visual Asset Acquisition

Visual assets are **mandatory, not optional**. Every deck must evaluate and acquire image material before writing YAML.

### Decision Framework

| Slide Type | Image Requirement | Default Action |
|-----------|-------------------|----------------|
| Cover | **Must have** | AI-generate a custom background via MiniMax |
| Closing | **Must have** | Reuse cover image with different filter |
| Chapter divider | **Strongly recommended** | AI-generate or Unsplash |
| Content (metaphor needed) | **Recommended** | AI-generate abstract/scene image |
| Content (chart/table heavy) | Optional | Gradient/texture background only |
| Data dashboard | Skip | Native background presets |

### Dual-Track Acquisition

1. **AI Generation Track** — Use `mcp__minimax-image__text_to_image` for:
   - Custom cover backgrounds tailored to the deck topic
   - Abstract concept illustrations (concepts Unsplash cannot photograph)
   - Brand-consistent scene images
   - Prompts must include: subject + style + color palette + composition

2. **Unsplash Track** — Use `python -m office_suite.tools.unsplash_assets` for:
   - Real-world scene photos (office, nature, people)
   - Texture and pattern backgrounds
   - When API key is unavailable, the tool still generates a search plan (`asset_brief.md`)

### Prompt Quality Standard

Every AI image prompt must answer four questions:
1. **What** is the subject? (specific, not generic)
2. **What style** does it use? (photograph / illustration / 3D render / watercolor)
3. **What colors** dominate? (must align with deck palette)
4. **What composition** does it have? (focal point position, text overlay space)

Example prompt:
```
"abstract network of interconnected knowledge nodes, minimalist digital illustration,
deep navy blue with gold accent highlights, 16:9 composition with large empty
area on left half for text overlay, soft gradient background, no text, no watermark"
```

### Fallback Hierarchy

When AI generation is unavailable: Unsplash → background_presets (gradient/geometric) → solid color + decorative shapes.

---

## Phase 4: Materialization

### 4.1 deck.yml Construction

```yaml
version: "4.0"
type: presentation
title: "Presentation Title"
theme: default
styles:
  h1:
    font: { family: "Microsoft YaHei UI", size: 36, weight: 700, color: "#C9A84C" }
  h2:
    font: { family: "Microsoft YaHei UI", size: 16, weight: 700, color: "#E8E4DC" }
  body:
    font: { family: "Microsoft YaHei UI", size: 13, weight: 400, color: "#E8E4DC" }
  caption:
    font: { family: "Microsoft YaHei UI", size: 10, weight: 400, color: "#6B7280" }
pages:
  - pages/001_cover.yml
  - pages/002_content.yml
```

### 4.2 Generate-All-First Strategy

All YAML files (deck.yml + every page file) must be written before any rendering or validation. This prevents partial-deck inconsistencies and enables batch verification.

### 4.3 Sub-Agent Delegation

When the deck exceeds 20 pages, delegate page generation to sub-agents:

1. Main agent completes: outline.md, design.md, deck.yml
2. Sub-agents generate individual page YAML files
3. Sub-agents must read: `format/dsl.md`, design.md, deck.yml, outline.md

**Invariant**: For any file on disk, pass the file path. Never summarize or compress content before passing to sub-agents -- information loss during handoff degrades output quality.

### 4.4 Motion Design: Transitions and Animations

Motion is a scarce attention resource, not decoration. Every animated element competes with every other for the audience's gaze. The AI must decide autonomously whether and how to animate — the user never specifies animation details.

**Decision Process (three steps, applied per slide):**

**Step 1 — Should this slide have element animations?**

| Slide role | Animate? | Cognitive reason |
|-----------|----------|-----------------|
| `opener` / cover | YES | First impression establishes pacing rhythm |
| `context` / section_opener | YES | Section transition needs visual signal |
| `proof` / data_peak | YES | Key data deserves emphasis moment |
| `contrast` / comparison | NO | Static side-by-side enables direct comparison |
| `method` / process | PARTIAL | Only first step — rest appear instantly |
| `pause` / summary | NO | Review slides should be scannable, not theatrical |
| `close` / ending | YES | Closing rhythm mirrors opener |

Budget: **max 1-3 animated elements per slide**. More than 3 = noise.

**Step 2 — Which elements to animate? (priority ranking, select top 1-3)**

| Priority | Element semantic | Condition |
|----------|-----------------|-----------|
| P0 | Main title (中文大字) | Every animated slide — mandatory |
| P1 | Hero number / statistic | Font size ≥ 36pt |
| P2 | English label / section subtitle | Pairs with title as narrative beat |
| P3 | Divider line / accent bar | Has visual guidance function |
| P4 | First info card only | Highest/leftmost card in a grid |

Never select: body paragraphs, labels, tables, background shapes, small captions, non-first cards.

**Step 3 — Match effect to element semantic role:**

| Element role | Effect | Duration | Trigger |
|-------------|--------|----------|---------|
| Main title (中文) | `fade` | 0.6s | `after_previous`, delay 0.3 |
| English label (ALL CAPS) | `fade` | 0.4s | `with_previous` |
| Section subtitle | `slide_left` | 0.5s | `after_previous`, delay 0.2 |
| Hero number (≥36pt) | `zoom_in` | 0.5s | `with_previous` |
| Divider line | `wipe_right` | 0.4s | `with_previous` |
| Info card (first only) | `zoom_in` | 0.4s | `with_previous` |
| Result bar (bottom) | `wipe_up` | 0.5s | `after_previous`, delay 0.2 |
| Process step (first only) | `fade` | 0.4s | `after_previous`, delay 0.2 |
| Conclusion item (first only) | `fade` | 0.5s | `after_previous`, delay 0.3 |

**Slide transition selection:**

Use `fade` for most slides. Use `push` or `wipe` for section transitions. Use at most 2-3 transition types per deck. Consistency beats variety.

| Slide role | Transition |
|-----------|-----------|
| cover / closing | `fade`, `med` |
| section_opener | `push` or `wipe`, `med` |
| data / content | `fade`, `med` |

**Hard prohibitions:**

1. Never animate every element on a slide.
2. Never animate body text, paragraphs, or captions.
3. Never animate all cards in a card grid — only the first.
4. Never use `on_click` on body text.
5. Never mix entry + exit on the same element.
6. Never set delay > 1.0s or duration > 1.0s.
7. Never animate decorative background shapes.

**DSL generation (AI outputs this automatically):**

```yaml
- layout: blank
  transition: { type: fade, speed: med }
  elements:
    - type: text
      content: "标题"
      style: title
      animation: { effect: fade, duration: 0.6, delay: 0.3, trigger: after_previous }
    - type: text
      content: "正文不加 animation 字段"
      style: body
```

---

## Phase 5: Verification

### 5.1 Structural Validation

```bash
python -m office_suite.tools.check output/<deck-name>/deck.yml --render pptx --output-dir output/<deck-name>/check
```

### 5.2 Error Classification

| Severity | Category | Description |
|----------|----------|-------------|
| Block | Syntax | YAML parse errors, missing files, invalid references |
| Block | Bounds | Elements exceed canvas (x+w > 254mm or y+h > 142.875mm) |
| Block | Render | IR compilation failure, PPTX generation failure |
| Fix | Overflow | Text content exceeds allocated space |
| Fix | Occlusion | Text hidden behind other elements |
| Fix | Drift | Text box misaligned with its container |
| Review | Density | Font hierarchy violations (>4 sizes), color count (>6) |
| Review | Spacing | Inconsistent margins or gaps |

### 5.3 Fix Protocol

1. Fix all Block-severity issues first
2. Fix all text overflow/occlusion (these produce visible defects in the final PPTX)
3. Review density and spacing warnings
4. Re-run check after fixes, review complete output (no grep filtering)

**Overflow fix priority**: Condense text -> Reduce font size -> Expand container. Never reduce font size below 12pt.

**Alignment invariant**: When adjusting any element, verify that spatially related elements (its card, its divider, its decorative line) are adjusted in concert.

---

## Output Directory Structure

```
output/<deck-name>/
  outline.md          # Structure contract (Phase 2 output)
  design.md           # Style contract (Phase 3 output)
  deck.yml            # Theme + page manifest
  pages/
    001_cover.yml
    002_content.yml
    ...
  <deck-name>.pptx    # Rendered output
  check/              # Verification artifacts
```
