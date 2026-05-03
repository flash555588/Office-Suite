# Art Direction

This file defines the visual quality standards that apply to **every** presentation regardless of domain profile. Domain profiles (academic, business_insight, etc.) define WHAT to show. This file defines HOW it should look.

---

## 1. Visual Composition

### 1.1 Spatial Weight Distribution

Every slide has a **visual center of gravity** -- the point where the eye naturally rests. This is NOT necessarily the geometric center.

| Composition Type | Center of Gravity | Use When |
|-----------------|------------------|----------|
| Symmetric | Geometric center | Formal authority (cover, chapter pages) |
| Rule of thirds | Intersection points at 1/3 and 2/3 | Dynamic content (image-heavy, editorial) |
| Golden ratio | ~61.8% from left edge | Premium feel (brand, luxury, cultural) |
| Diagonal tension | Opposing corners | Energy and movement (comparison, contrast) |

Office Suite canvas: 254mm x 142.875mm. The four rule-of-thirds intersection points are:
- (84.7mm, 47.6mm), (169.3mm, 47.6mm)
- (84.7mm, 95.3mm), (169.3mm, 95.3mm)

Place the **salience target** (the element that should attract the eye first) at or near one of these points. Never place the salience target at dead center on content pages -- center placement signals "this is a title page."

### 1.2 Visual Balance

Balance is not symmetry. It is the equilibrium of visual weight across the slide.

**Visual weight factors** (heavier = more weight):
- Dark colors > light colors
- Large elements > small elements
- High contrast > low contrast
- Dense texture > flat fill
- Sharp edges > soft edges

**Balance strategies**:
- **Symmetric balance**: Mirror elements across the vertical axis. Use for: covers, formal chapter pages. Risk: static, predictable.
- **Asymmetric balance**: A large element on one side balanced by multiple smaller elements on the other. Use for: content pages, editorial layouts. Creates dynamic interest.
- **Radial balance**: Elements radiate from a center point. Use for: hub-and-spoke diagrams, cycle graphics.

**Anti-pattern**: A slide with all visual weight concentrated in one quadrant, leaving the opposite quadrant completely empty. This is not "whitespace" -- it is imbalance.

### 1.3 Visual Flow

The eye follows a predictable path determined by element arrangement:

| Flow Pattern | Element Arrangement | Best For |
|-------------|-------------------|----------|
| Z-pattern | Top-left -> Top-right -> Bottom-left -> Bottom-right | Information-dense pages with scanning behavior |
| F-pattern | Top horizontal scan -> Left vertical scan -> Secondary horizontal | Text-heavy pages |
| Center-out | Central element -> surrounding details | Hero moments, single-focus pages |
| Linear | Left-to-right or top-to-bottom sequence | Timeline, process, narrative progression |
| Layered | Foreground -> midground -> background | Depth and sophistication |

The page title, being the highest-contrast text element, anchors the flow start point. From there, the layout pattern determines the continuation path.

---

## 2. Color Harmony

### 2.1 Harmony Models

The 6-token palette must achieve internal harmony. Given that Office Suite uses a fixed palette per deck, harmony is established once in design.md and maintained across all pages.

| Model | Relationship | Character |
|-------|-------------|-----------|
| Monochromatic | Single hue, varied saturation/brightness | Refined, cohesive, sophisticated |
| Analogous | Adjacent hues on the color wheel | Harmonious, natural, comfortable |
| Complementary | Opposite hues | High contrast, vibrant, attention-grabbing |
| Triadic | Three equidistant hues | Balanced variety, energetic |

For Office Suite's 6-token system, the accent color and bg_primary establish the primary hue relationship. text_primary and text_muted are neutrals (achromatic or near-achromatic) that do not participate in hue harmony.

### 2.2 Contrast Standards

| Pair | Minimum Contrast Ratio | Purpose |
|------|----------------------|---------|
| text_primary on bg_primary | 7:1 (WCAG AAA) | Body text readability |
| text_muted on bg_primary | 4.5:1 (WCAG AA) | Caption readability |
| accent on bg_primary | 4.5:1 | Emphasis visibility |
| H1 text on bg_primary | 4.5:1 | Title visibility |
| text on bg_surface | 4.5:1 | Card content readability |

When selecting accent colors, verify contrast against BOTH bg_primary and bg_surface (cards).

### 2.3 Color Temperature Continuity

Maintain consistent temperature across the deck. A cool palette on slides 1-4 followed by a warm palette on slides 5-7 creates jarring discontinuity.

Exceptions for intentional punctuation:
- A warm accent on an otherwise cool deck creates a "spotlight" effect on key slides
- Dark-background slides in a light-background deck create dramatic emphasis

These temperature breaks should be **rare** (1-2 per deck) and **purposeful** (only on climactic slides).

---

## 3. Typography as Visual Art

### 3.1 Letterform Aesthetics

Typography is not just hierarchy encoding (covered in generate_slides.md). It is also **visual texture**.

| Quality | Parameter | Effect |
|---------|----------|--------|
| **Weight rhythm** | Alternating bold and regular within a slide | Creates breathing rhythm in text blocks |
| **Size drama** | Extreme size contrast (H1 at 36pt next to Caption at 10pt) | Creates visual tension and premium feel |
| **Letter spacing** | Wide spacing on titles (1-2pt) | Evokes luxury, ceremony, formality |
| **Line height** | 1.3x for body, 1.1x for titles | Controls density and breathability |
| **Vertical rhythm** | Baseline alignment across card columns | Creates grid coherence |

### 3.2 Typographic Composition Rules

- **Maximum 3 font families per slide** (e.g., display + body + accent). Single family is simplest.
- **Contrast through weight and size**, not through multiple families.
- **Maximum 6 distinct font sizes on a single slide** for rich typographic hierarchy (data posters, magazine layouts may need more levels).
- **Title text should be short enough to fit on one line.** If the title wraps, it is too long -- shorten the title, do not shrink the font.
- **Body text alignment**: Left-aligned for sentences (default). Center-aligned only for short labels, badges, and tile content. Never center-align paragraphs.

---

## 4. Image Art Direction

### 4.1 Style Consistency

All images within a single deck must share a consistent visual treatment:

| Treatment | Description | When to Use |
|-----------|-------------|-------------|
| Original | No modification beyond sizing | Product photos, screenshots, data visualizations |
| Desaturated | Reduced saturation (30-60%) | Background images, atmospheric photos |
| Duotone | Two-color mapping (accent + bg_primary) | Hero images on cover/chapter pages |
| Masked | Semi-transparent color overlay | Images that need text readability on top |
| Cropped | Aggressive crop to focus on subject | Character photos, product details |

**Rule**: Within one deck, all non-data images use the same treatment. Mixing treatment styles (e.g., one photo in full color, another in duotone) creates visual incoherence.

### 4.2 Image-Text Coexistence

When text overlays an image:
- Apply a semi-transparent overlay (50-70% opacity of bg_primary) between the image and text
- Ensure text contrast ratio meets 4.5:1 against the overlaid result
- Text should be placed over the least visually busy region of the image
- Prefer bottom-placed text on landscape images (sky/top tends to be visually lighter)

### 4.3 Image Sourcing Standards

| Criterion | Minimum Standard |
|-----------|-----------------|
| Resolution | >= 1200px on the long edge |
| Aspect ratio | Match the target container; crop rather than stretch |
| Watermarks | None |
| Relevance | Directly supports the slide's key message |
| Quality | Publication-grade (no phone screenshots, no low-res internet grabs) |

---

## 5. Visual Rhythm Across the Deck

### 5.1 Density Pacing

A deck should have **rhythmic variation** in visual density, not uniform density throughout:

```
Slide 1 [cover]:     SPARSE (high impact, minimal content)
Slide 2 [content]:   BALANCED (standard density)
Slide 3 [content]:   DENSE (information-heavy)
Slide 4 [content]:   BALANCED (recovery)
Slide 5 [content]:   DENSE (data-heavy)
Slide 6 [content]:   BALANCED (decompression)
Slide 7 [closing]:   SPARSE (high impact, minimal content)
```

The pattern: sparse open -> build density -> decompress -> peak density -> sparse close. This creates a narrative rhythm that sustains attention.

### 5.2 Composition Rhythm

Consecutive slides should NOT use the same composition skeleton. The rule of non-repetition:

- Maximum 2 consecutive slides with the same skeleton
- After a dense composition (large grid, complex chart, or multi-label diagram), follow with a simpler or more spacious composition
- Chapter/transition pages break the content layout sequence, but should still express the deck's motif

### 5.3 Color Rhythm

Accent color usage should have rhythm:
- Use accent on 60-80% of content slides (for titles at minimum)
- Reserve slides without accent for dramatic contrast (a fully monochrome page followed by accent reintroduction)
- Accent color is typically emphasis-level (~30% of visual area), but promotional and brand slides may use it more aggressively when the design concept calls for it

---

## 6. Card Visual Quality

### 6.1 Card Aesthetics

Cards in Office Suite follow these visual standards:

| Parameter | Recommended Default | Rationale |
|-----------|-------------------|-----------|
| Corner radius | 3mm (recommended; vary 0-8mm for stylistic effect) | Consistency by default, variation for intentional design |
| Border | 1pt, border token color | Subtle containment signal |
| Fill | bg_surface token | Distinct from page background |
| Internal padding | 4mm on all sides (adjust 2-6mm for density control) | Content breathing room |
| Shadow | Optional -- use for depth hierarchy when the design concept calls for it | Adds visual layering when intentional |

### 6.2 Card Grid Alignment

Cards in a grid must be:
- **Same width**: All cards in a row share identical width
- **Same height**: All cards in a group share identical height
- **Even spacing**: 4mm gap between cards (recommended; 2-8mm depending on density intent)
- **Aligned to grid**: Left edges aligned, top edges aligned

### 6.3 Card Content Density

| Card Width | Max Title Length | Max Body Length |
|-----------|-----------------|----------------|
| 32mm | 6 characters | 20 characters |
| 50mm | 10 characters | 40 characters |
| 68mm | 14 characters | 60 characters |
| 103mm | 20 characters | 100 characters |

If content exceeds these limits, either shorten the text or increase the card width.

---

## 7. Decoration Philosophy

### 7.1 Decoration = Information

Every visual element on a slide must carry information. "Decoration" in Office Suite means functional visual elements:

| Element | Information Carried |
|---------|-------------------|
| Divider line | "Below is a new section" |
| Card border | "These elements belong together" |
| Accent color on title | "This is the most important text" |
| Diamond shape (closing) | "This is the end" |
| Page marker | "You are here in the deck" |

### 7.2 Decorative Patterns -- Use with Intent

The following patterns are **not prohibited**, but must serve a clear design purpose. If removing the element does not reduce the slide's communicative power, remove it.

| Pattern | When It Works | When It Fails |
|---------|--------------|---------------|
| Drop shadows | Layered depth on dark backgrounds; floating card aesthetics | Every element having shadows = visual noise |
| Gradient fills on cards | Premium feel; brand-aligned atmospheric depth; hero cards | Data-dense slides where clarity > aesthetics |
| Decorative borders (dashed, ornamental) | Playful/creative contexts; placeholder regions | Formal business contexts without thematic reason |
| Background textures | Brand storytelling; immersive cover/closing pages | Content pages where text readability suffers |
| Animated GIFs or emoji | Casual/educational contexts | Formal business presentations |
| Stock watermarks | Never acceptable | Always destroys credibility |
| Decorative shapes unrelated to content | Brand identity reinforcement; atmospheric context | Consuming spatial budget without meaning |

### 7.3 Decorative Elements

These are common decorative choices. The list is non-exhaustive -- AI is free to invent new decorative treatments that serve the design concept.

| Element | Typical Use |
|---------|------------|
| Thin horizontal lines | Section separation, accent punctuation |
| Diamond/rhombus shapes | Closing pages, visual punctuation |
| Gradient overlays on images | Text readability, atmospheric depth |
| Rounded rectangles | Card containers, buttons, badges |
| Background geometric shapes | Brand identity, atmospheric context (circles, blobs, abstract forms) |
| Textured fills | Brand storytelling, immersive backgrounds |
| Decorative borders | Creative/artisanal contexts, placeholder regions |

---

## 8. Visual Quality Checklist

Apply this checklist to every slide before rendering:

```markdown
## Per-Slide Visual Audit

### Composition
- [ ] Salience target is at or near a rule-of-thirds intersection point
- [ ] Visual weight is balanced (not concentrated in one quadrant)
- [ ] Eye flow follows the intended pattern (Z/F/linear/center-out)

### Color
- [ ] All text meets contrast ratio requirements (7:1 body, 4.5:1 captions)
- [ ] Accent color covers <30% of visual area
- [ ] Temperature is consistent with adjacent slides

### Typography
- [ ] <= 6 distinct font sizes
- [ ] <= 3 font families
- [ ] Title fits on one line (or intentionally wraps for effect)
- [ ] Body text is left-aligned (or center only for short labels)

### Cards
- [ ] Same-size cards in each grid row
- [ ] Consistent gaps between cards (recommended 4mm; 2-8mm depending on density)
- [ ] Content within density limits per card width
- [ ] No card nesting (unless intentional containment hierarchy)

### Decoration
- [ ] Every decorative element has a purpose (brand, atmosphere, hierarchy)
- [ ] Shadows, gradients, and ornamental elements are intentional, not default
- [ ] Consistent image treatment across deck
```

---

## 9. Domain-Specific Art Overrides

Some domain profiles override specific art direction rules:

| Domain | Override |
|--------|---------|
| promotion | Center placement IS allowed on content pages (slogan pages) |
| promotion | Large whitespace IS intentional (not imbalance) |
| business_insight | Accent color may be used for >30% of a chart's visual area |
| education | Up to 4 semantic colors ARE permitted (beyond the 6-token limit) for knowledge category coding |

When a domain profile conflicts with this file, the domain profile takes precedence. This file is the baseline; profiles are the exceptions.
