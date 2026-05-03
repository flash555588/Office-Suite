# Academic Presentation

> Domain: Thesis defense, research seminars, conference talks, lab group meetings, project reports
> Cognitive posture: High-effort analytical -- the audience actively evaluates evidence quality and logical validity

## Density Target: Dense (70-85%)

Academic audiences expect information-rich slides. Sparse slides signal insufficient preparation. Each slide should carry a complete argumentative unit: claim + evidence + interpretation.

Charts, formulas, and data tables are the primary content carriers. Text serves as connective tissue between visual evidence.

## Visual-Verbal Ratio

Approximately 35% text, 55% charts/figures/tables/formulas, 10% whitespace. Results slides should be chart-dominant with text reduced to annotations and key takeaways.

Original figures from the source paper/report should be reused when available. Original figures preserve data precision, annotation standards, and formatting conventions that redrawing may compromise.

## Color Derivation

Temperature: cool-authoritative. The palette must not compete with data visualization colors.

| Token | Default | Rationale |
|-------|---------|-----------|
| accent | University brand color if specified; otherwise a restrained blue-gray | Low saturation to avoid distracting from data |
| bg_primary | White `#FFFFFF` | Maximum contrast for charts, formulas, and annotations |

Chart colors: prioritize distinguishability over aesthetic harmony. Reference Nature/Science palette conventions for multi-series charts.

## Typography Posture

All figures and tables require standard numbering (Figure 1, Table 2). Chart axes need labels and units. Every data point must be traceable to a source.

The reference list is mandatory. Format follows the user's specified citation style (APA, IEEE, GB/T 7714); default to the convention of the presentation language.

Font formula/code: monospace. LaTeX for mathematical notation.

## Narrative Convention

Follow the research logic chain: Background -> Problem -> Method -> Results -> Conclusion. Each slide maps to one node in this chain.

The title should be a descriptive finding statement ("Transformer Attention Patterns Differ by Layer Depth") not a section label ("Experiments").

## Content Expression

| Evidence Type | Visual Encoding |
|--------------|----------------|
| Quantitative comparison (methods vs metrics) | Bar chart or table with highlighted best values |
| Temporal trends | Line chart with annotated milestones |
| Multi-dimensional evaluation | Radar chart or parallel coordinates |
| System architecture | Shape + arrow + text diagram |
| Mathematical formulation | Centered LaTeX block with variable annotations |
| Process workflow | Flowchart built from shapes and connectors |

## Design Guidance

| Pattern | Guidance |
|---------|----------|
| Decorative backgrounds or textures | Avoid on data pages; permitted on cover/closing for conference branding |
| Charts without complete annotations | Blocker -- undermines scientific rigor |
| Text effects (shadow, glow, bevel) | Avoid on data/content pages; permitted on cover/closing for visual identity |
| Unsupported claims | Blocker -- academic audiences verify assertions |
| Gradient fills on charts | Avoid -- reduces data readability |
