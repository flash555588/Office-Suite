# Business Intelligence

> Domain: Equity research, industry analysis, market surveys, competitive intelligence, strategic consulting
> Cognitive posture: Decision-accelerating -- the audience needs to reach actionable conclusions in minimum time

## Density Target: Saturated (85%+)

Business audiences evaluate information density as a proxy for analytical rigor. Sparse slides signal shallow analysis.

Each slide must carry at minimum: one conclusion statement (the title), 3-5 quantified data points, and at least one chart or table. A slide that can be fully consumed in under 10 seconds is too sparse.

## Visual-Verbal Ratio

Approximately 60% text and data annotations, 30% charts and tables, 10% source attributions and structural elements. Text is the primary carrier because business insight requires interpretation -- data without commentary is inert.

## Color Derivation

Temperature: cool-authoritative, leaning toward maximum restraint. The palette must not create emotional bias in data interpretation.

| Token | Default | Rationale |
|-------|---------|-----------|
| accent | Deep navy or brand color | Authority signal, not decoration |
| bg_primary | White `#FFFFFF` | Maximum data legibility |

Color usage is information-coded, not decorative:
- The primary data series uses the accent color
- Secondary data series uses neutral grays
- Highlighted metrics use bold weight + larger size, NOT a different color

Maximum 3 non-grayscale colors across the entire deck.

## Typography Posture

Every slide title is an **action title** -- a complete insight sentence that a senior executive can read without looking at the body content.

Wrong: "Market Analysis"
Right: "China SaaS Market at $28B, Penetration at 12%, 5-Year CAGR 24%"

The title carries the "so what." The body carries the "how do we know."

Body text at 13pt. Source annotations at 9-10pt with `<a href="url">` hyperlinks.

## Data Expression Standards

| Element | Standard |
|---------|---------|
| Key metrics | Displayed as bold numbers 2-4pt larger than surrounding text |
| Data sources | Every chart and table annotated: `Source: Institution, Year` |
| Comparisons | Same-unit metrics in tables; different-unit metrics in charts |
| Highlighting | Bold weight only. No colored text, no background fills on text |
| Tables | Header row: accent background, white text. Alternating row shading optional |

Charts must have: title, axis labels, units, data labels, legend. A chart the audience cannot read without verbal explanation has failed.

## Narrative Convention

Each slide answers one business question. The title states the answer. The body proves it.

Content layers: Conclusion -> Evidence -> Implication. Not: Background -> Analysis -> Finding.

Source attributions use `<a href="url">` hyperlinks for traceability.

## Design Guidance

| Pattern | Guidance |
|---------|----------|
| Shadows on any element | Avoid unless the design concept explicitly calls for depth (e.g., floating metric cards on dark backgrounds) |
| Gradient fills | Avoid on data-dense content pages; permitted on cover/closing pages for brand expression |
| Decorative icons | Avoid -- information density budget is too precious for non-data elements |
| Data without sources | Blocker -- destroys credibility in analytical contexts |
| Single large chart filling entire page | Avoid -- wastes spatial budget; pair with interpretation text |
| Vague qualifiers ("significant", "substantial") | Replace with specific numbers |
