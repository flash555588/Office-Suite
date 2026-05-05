# Office Suite 4.0 — Presentation & Document Generation

## Scope

Generate professional presentations and documents from YAML DSL. Runtime path:

```text
YAML DSL -> Parser -> IR Document -> Renderer -> .pptx / .docx / .xlsx / .pdf / .html
```

## Core Workflow: Generate-All-First, Check-Once

For every generation task, adopt a **generate-all-first, then check-once** strategy:

1. Complete ALL files (outline, design, deck.yml, every page) before any rendering or validation.
2. Never render, check, or deliver one page at a time.
3. Only after the complete deck is written, run the unified quality gate.
4. Fix issues in batch, then re-render.

## Agent Orchestration

| Role | Scope | Prohibited |
|------|-------|-----------|
| **Main Agent** | Visual design, structure contract, style contract, `deck.yml` construction, quality gate, final delivery | Delegating design decisions to sub-agents before `deck.yml` exists |
| **Sub-Agent** | Generating individual `.page` / `.yml` slide files under `pages/` only | Making visual design choices, changing color/font rules, modifying `deck.yml` or `design.md` |

Before the `deck.yml` and `design.md` are finalized, **strictly prohibited** from assigning page-generation tasks to sub-agents.

## PPT Generation Workflow

### Step 0: Read Guidelines

Before generating any PPT content, read `office_suite/guidelines/ppt_layout_system.md`. Do not proceed without reading it.
Also read `office_suite/guideline/design/art_direction.md` for baseline visual quality standards.
Also read `office_suite/guideline/design/premium_presentation.md` whenever the user asks for PPTs that are creative, polished, refined, premium, paid-grade, non-template, impressive, high-end, or presentation-ready. In normal PPT generation, still treat it as the default standard unless the user explicitly asks for a plain internal draft.
When visual mode is `creative`, also read `office_suite/guideline/design/creative_mode.md` and the closest matching profile under `office_suite/guideline/design/profiles/`.
Before writing `outline.md`, read the matching content guideline:
- `office_suite/guideline/content/search_mode.md` when the user provides only a topic or asks for current facts, data, examples, recommendations, or enrichment.
- `office_suite/guideline/content/summary_mode.md` when the user provides a long document to distill.
- `office_suite/guideline/content/outline_mode.md` when the user provides a structured outline.
Before the asset stage, read `minimax-multimodal-toolkit/SKILL.md`. Every deck must evaluate MiniMax image generation as an asset path alongside Unsplash, and `design.md` must record whether generated images are used, skipped, or kept as prompt briefs.

### Step 1: Understand Inputs

- Read all user-provided source files.
- Identify language, audience, page count, required data, tone, visual constraints.
- Decide the **content mode**:
  - `outline`: user supplied a page plan, chapter tree, or structured outline.
  - `summary`: user supplied a long document and wants it distilled into slides.
  - `research`: user supplied only a topic or sparse requirements.
- Decide the **visual mode**:
  - `creative`: no visual reference; create from scenario, audience, topic.
  - `reference`: user supplied screenshots, website, images, or style sample.
  - `template`: user explicitly asked to follow a provided template.

Record these decisions in `outline.md` and `design.md`.

### Step 1a: Information Gathering Before Outline

Do not write slide content from memory when the topic can benefit from external facts, examples, sources, statistics, dates, names, standards, or current context.

Before `outline.md`, create an information inventory:
- Known inputs: what the user provided directly.
- Unknowns: facts, examples, data, definitions, timelines, or audience-specific context needed to make the deck credible.
- Search plan: 3-8 targeted queries or source lookups, adjusted to the audience and topic.
- Source priority: primary/official sources first, then reputable research or established media, then secondary explainers only for background.
- Evidence target: for research/enrichment decks, aim for at least 3 credible sources and 5-10 source-backed facts before drafting the slide outline.
- Currentness check: if any claim may have changed recently, verify it before using it.

**Web search is mandatory when:**
- content mode is `research`
- the user asks for "latest", "current", "today", trends, market data, policies, standards, product specs, prices, schedules, or recommendations
- the topic is niche, technical, legal, medical, financial, or otherwise high-stakes
- the deck includes statistics, rankings, named case studies, or claims about modern organizations/people

**Search tool:** Use `mcp__MiniMax__web_search` for all web searches. Do not fabricate URLs or data.

**Search strategy by content type:**

| Content type | Query pattern | Example |
|-------------|--------------|---------|
| 行业数据 | `"<行业> <指标> <年份>"` | `"中国新能源汽车销量 2025"` |
| 技术原理 | `"<技术> 原理 工作机制"` | `"锂电池 原理 工作机制"` |
| 对比分析 | `"<A> vs <B> 优缺点"` | `"React vs Vue 优缺点 2025"` |
| 案例事实 | `"<公司/人物> <事件> <年份>"` | `"OpenAI GPT-5 发布时间"` |
| 政策标准 | `"<领域> <国家/机构> 标准 规范"` | `"医疗器械 FDA 认证流程"` |
| 趋势预测 | `"<领域> 趋势 预测 <年份>"` | `"AI 教育 趋势 预测 2026"` |

**Search execution rules:**
1. Run 2-4 searches per deck, each targeting a different angle (数据/事实/案例/趋势).
2. Extract concrete numbers, dates, names, and URLs from results.
3. Cross-verify claims that appear in only one source.
4. Record all source URLs in `outline.md` under "Information Inventory".
5. If a search returns no useful results, rephrase the query with different keywords before giving up.

**When NOT to search:**
- User provided complete source documents (summary mode).
- User provided a structured outline (outline mode).
- Topic is purely fictional/creative (fiction, storytelling).
- All content is from user's own data/experience.

If network access is unavailable, record that limitation in `outline.md`, proceed with conservative claims only, and avoid unsupported statistics.

### Step 2: Write Structure Contract (`outline.md`)

Persist a page-level outline before writing YAML. Include:

- Deck title and target audience
- Content mode and expansion policy
- Information inventory: sources consulted, queries used, facts retained, and facts rejected or left unverified
- Slide count and slide-by-slide story flow
- For each slide: title, key message (one single message per slide), content bullets, custom composition, visual treatment notes
- For each slide: define one visual hook (`photo`, `semantic_icon`, `diagram`, `big_number`, `quote`, `timeline`, or `contrast_panel`) that makes the page visually distinct
- For creative/premium decks: include a "why this slide does not feel templated" note for every content slide.
- Explicit notes for charts, tables, diagrams, images, callouts

**Expansion policy:**
- If the user asks to follow provided content exactly, preserve structure and wording.
- If the user asks for enrichment, add supporting examples and data, marking what was supplemented.
- If the user is silent, stay conservative: clarify structure and only add obvious missing structural pages.

Recommended outline shape:

```markdown
# Presentation Outline

## Context
- Audience:
- Content mode:
- Expansion policy:
- Page count:
- Sources consulted:
- Search queries:
- Evidence retained:
- Unverified or excluded claims:

## Page 1 [cover] — Layout: cover_split
- Title:
- Key message:
- Content:
- Evidence/source:
- Visual:

## Page 2 [content] — Composition: annotated_artifact
- Title:
- Key message:
- Content:
- Evidence/source:
- Visual:
- Anti-template note:
```

### Step 3: Write Style Contract (`design.md`)

Persist the visual design system before writing YAML. Must include:

#### 3.1 Canvas
- 16:9, `254mm x 142.875mm`
- Background color, margin system

#### 3.1a Art Direction (MANDATORY)
Before choosing slide coordinates, define a concise art direction in `design.md`:
- Creative concept: a concrete metaphor or visual language derived from the topic, not a generic "clean modern" phrase.
- Creative premise: one sentence that could not apply to an unrelated deck.
- Slide choreography: label each slide's role in the audience experience (`opener`, `context`, `proof`, `contrast`, `data_peak`, `method`, `pause`, `close`, etc.).
- Composition strategy: choose the dominant flow per slide family (`rule_of_thirds`, `linear`, `center_out`, `asymmetric_balance`, or `editorial_grid`).
- Visual rhythm: label each slide density as `sparse`, `balanced`, or `dense`; covers and closings should normally be sparse.
- Signature motif: one repeatable, topic-relevant visual element used across the deck (for example: book margins, circuit traces, map pins, product frames, quote marks).
- Contrast moment: identify 1-2 slides where layout, scale, or background intentionally breaks the rhythm for emphasis.
- Anti-template strategy: explicitly name which slides avoid card grids and what custom composition they use instead.

Creativity must come from semantic choices, composition, scale, pacing, and strong assets. Do not rely on random decorative shapes, large shadows, emoji, clip art, or unrelated ornaments.
Templates are references for canvas, syntax, and fit. They are not mandatory layouts and must not constrain the final composition when a stronger custom slide is appropriate.

#### 3.2 Theme Selection (MANDATORY — do this before picking any colors)

**First**, read `office_suite/design/tokens.py` and review all 10 built-in presets. Evaluate which preset best matches the deck's domain, audience, and emotional tone:

| Preset | Background | Accent | Suits |
|--------|-----------|--------|-------|
| `warm` | cream #FFFBEB | amber #D97706 | Education, reading, lifestyle, nonprofit |
| `elegant` | white #FFFFFF | gold #D4AF37 | Formal events, luxury, literature, arts |
| `editorial` | white #FFFFFF | blue #2563EB | Reports, journalism, clean communication |
| `corporate` | white #FFFFFF | blue #1E40AF | Business, finance, enterprise |
| `minimal` | white #FFFFFF | blue #2563EB | Startups, modern tech, design-focused |
| `tech` | dark #0B0F19 | cyan #06B6D4 | Developer tools, AI, deep tech |
| `creative` | dark #18181B | rose #E11D48 | Brand launches, creative portfolios, bold pitches |
| `flat` | light #F0F9FF | sky #0EA5E9 | Healthcare, wellness, accessibility |
| `chinese` | deep red #7F1D1D | gold #D4AF37 | Chinese festivals, traditional culture, celebration |
| `forest` | — | — | (gradient only: green-teal) |

**Second**, set `style_preset` in `deck.yml` to the chosen preset name. The compiler will auto-derive base styles from the preset.

**Third**, if the preset needs tuning (e.g., a lighter card surface, a warmer accent), override individual tokens in `design.md` palette. Never invent a palette from scratch without first consulting the preset list and documenting why no preset fits.

#### 3.3 Color Palette (strict limit)
Define exactly 5-6 colors using the preset as baseline:
```text
style_preset: warm     # ← selected from tokens.py preset list
# Overrides (if any):
bg_primary:    #FFFBEB   (from preset)
bg_surface:    #FEF3C7   (from preset)
border:        #FDE68A   (from preset)
accent:        #D97706   (from preset)
text_primary:  #1C1917   (from preset)
text_muted:    #78716C   (from preset)
```
All emphasis must use opacity/brightness variations of these colors. Do not add new hues. If the preset provides exactly what's needed, use it as-is.

#### 3.3 Typography Scale (strict 4-level)

| Level | Size | Weight | Use |
|-------|------|--------|-----|
| H1 | 32-36pt | 700 | Page titles |
| H2 | 14-16pt | 700 | Card titles, section headers |
| Body | 12-13pt | 400 | Descriptions, bullet text |
| Caption | 9-10pt | 400 | Labels, tags, page markers |

Never use more than 4 distinct font sizes on a single slide.

#### 3.4 Composition System (Templates Are Reference Only)

Do not force every slide into a fixed layout pattern. Use templates only to understand renderer-safe syntax, spacing, and coordinate ranges. For each slide, design a composition that serves the message.

Preferred composition families:

| Composition | Use Case | Structure |
|-------------|----------|-----------|
| `editorial_opener` | Cover/chapter | Full-bleed crop or large visual field + asymmetric title block |
| `annotated_artifact` | Explain an object, concept, screenshot, book, product, map | One large artifact/image/diagram with labels and connector lines |
| `data_poster` | One decisive statistic | Oversized number/claim + small proof notes |
| `narrative_timeline` | Origin, evolution, process | Path/ribbon/shelf/margin sequence, not default equal circles |
| `comparison_axis` | Tradeoff, before/after, old/new | Two poles, center tension, selective evidence |
| `quote_wall` | Reflection, culture, voices | One dominant quote + secondary quote fragments or attribution treatment |
| `process_field` | Methods, steps, framework | Steps embedded in a meaningful diagram or scene |
| `magazine_spread` | Editorial explanation | Strong headline, short deck, image/figure, margin notes |
| `map_or_hub` | Ecosystem, stakeholders, factors | Central concept with satellite details |
| `closing_poster` | Closing | Sparse memorable call-to-action |
| `card_grid` | Catalog/list only | Equal cards when comparison really requires equal weight |

Composition rhythm rules:
- Do not use the same content skeleton more than 2 slides in a row.
- In decks with 6+ slides, include at least 5 distinct composition types unless the user explicitly asked for a strict template.
- No more than 2 card-grid slides in a 6+ slide deck unless the deck is a product catalog, curriculum module list, or other inherently repeated inventory.
- Include at least 2 slides where the primary visual is not a card: image crop, diagram, oversized number, quote/poster typography, chart, timeline, or annotated artifact.
- After a dense slide, follow with a simpler or more spacious slide when the story allows.

#### 3.5 Spacing Rhythm
```text
Page margins: 20mm L/R, 16mm top, 12mm bottom
Title band: y 16-32mm (title + divider)
Body region: y 40-116mm
Footer: y 124-132mm
Card gap: 4mm
Group gap: 8mm
Card internal padding: 4mm
```

#### 3.6 Risk Checklist
- [ ] No more than 6 colors total
- [ ] No more than 4 font sizes per slide
- [ ] Body text minimum 12pt
- [ ] All cards use identical radius (3mm)
- [ ] Text that visually belongs to a card/panel stays fully inside that card/panel, with at least 3mm bottom clearance
- [ ] Card/panel internal content groups are optically centered unless the design explicitly uses top-aligned reading flow
- [ ] `design.md` contains art direction, visual rhythm, signature motif, and contrast moment
- [ ] `design.md` contains creative premise, slide choreography, and anti-template strategy
- [ ] Every slide has one visual hook, not only title + bullets
- [ ] Deck uses at least 5 composition types when slide count is 6 or more, unless a strict template constraint is documented
- [ ] No more than 2 card-grid slides in a 6+ slide deck unless the content is an inventory/catalog
- [ ] Page markers: `x: 196mm, y: 126mm, width: 38mm`, align:right

#### 3.7 Asset Decision Gate

Before any page YAML is written, `design.md` must explicitly record the visual asset plan:

- Photo decision: `use`, `skip`, or `brief-only`
- Target slides that need photos, if any
- Search queries or source criteria for each photo
- AI image decision: `use`, `skip`, or `prompt-brief-only`
- Target slides that need generated images, if any
- MiniMax image prompts, aspect ratios, output directory, and fallback plan
- Icon decision: `frontend icon library SVG`, `native semantic_icon`, `external PNG`, or `skip`
- Icon inventory: library/source, exact icon names, target slides, meaning, size class, stroke width, color, and license/source note
- Fallback when network/API access is unavailable

This gate is mandatory even when the final decision is to use no photos. A deck may skip photo search only when `design.md` explains why diagrams, native icons, charts, or text-only layouts are clearer than photographic material.

### Step 4: Acquire Visual Image Assets

**This step is mandatory for every deck.** Do not write `deck.yml` or any page YAML before completing both the Unsplash track and the MiniMax generation track.

#### 4.1 Unsplash Search Track

1. Always run `python -m office_suite.tools.unsplash_assets` with at least 3 search queries tailored to the deck topic.
2. If `UNSPLASH_ACCESS_KEY` is not set, the tool still generates `asset_brief.md` and `manifest.json` — that is the minimum viable output.
3. Only after the tool has run may you decide which photos to actually use. Skipping the run entirely is a process defect.

Read `office_suite/guideline/design/unsplash_assets.md`, then execute:

```bash
python -m office_suite.tools.unsplash_assets \
  --output-dir output/<deck-name>/assets/photos \
  --topic "<deck topic>" \
  --query "<query 1: scene / mood / object relevant to topic>" \
  --query "<query 2: different angle or setting>" \
  --query "<query 3: third variation>" \
  --orientation landscape
```

Rules:
- Craft queries that match the deck's specific topic, not generic filler.
- Prefer 1-3 strong photos in a short deck, not images on every slide.
- Select images with clean negative space and colors compatible with the chosen preset.
- Use local downloaded JPG paths from `manifest.json` in page YAML.
- Preserve attribution metadata in `manifest.json`.
- Apply `blur` + `opacity` filters to full-bleed background images so text remains readable.
- If no suitable image is found, record that result in `design.md` and proceed with native diagram/icon treatment.
- Missing `asset_brief.md`, `manifest.json`, or a documented skip reason blocks the quality gate.

#### 4.2 MiniMax Image Generation Track

Read `minimax-multimodal-toolkit/SKILL.md`, then proactively generate images for the deck. **Default decision is `use`** — only skip when the deck is purely data-driven (dashboards, financial tables) where images would add noise rather than value.

Every deck should have at minimum:
- 1 cover background image (AI-generated, topic-specific)
- 1 closing/conclusion image (can reuse cover with different filter)

Additional images for chapter dividers, metaphor illustrations, and scene backgrounds are strongly encouraged.

Create a MiniMax image plan in `design.md`:
- Generation decision: `use` (default), `skip` (requires documented justification), or `prompt-brief-only`
- Target slide(s)
- Prompt(s)
- Aspect ratio, normally `16:9` for full-slide backgrounds and `1:1` or `4:3` for framed illustrations
- Output directory: `output/<deck-name>/assets/generated`
- Negative guidance: avoid text inside images, watermarks, distorted hands/faces, cluttered backgrounds, and off-palette colors
- Fallback: Unsplash photo, native diagram, or icon-based composition

When generation is used, run:

```bash
mmx image generate \
  --prompt "<deck-specific prompt>" \
  --aspect-ratio 16:9 \
  --n 1 \
  --out-dir output/<deck-name>/assets/generated \
  --out-prefix "<slide-or-purpose>" \
  --output json \
  --quiet
```

**Prompt construction rules:**

Every image prompt must follow this structure: **主体 + 场景 + 风格 + 色调 + 构图**

| 幻灯片角色 | Prompt 模板 | 示例 |
|-----------|-----------|------|
| 封面背景 | `<主题> <场景>, <风格> style, <色调> palette, wide composition, clean negative space` | `"chemistry laboratory glassware on dark table, cinematic photography style, deep blue and teal palette, wide 16:9 composition"` |
| 章节引导 | `<章节概念> metaphor, <风格>, <色调>, centered composition, minimal` | `"data flow metaphor with glowing nodes, flat illustration style, blue and white palette, centered symmetrical"` |
| 数据背景 | `<领域> abstract pattern, <风格>, <色调>, subtle texture, low contrast` | `"molecular structure abstract pattern, geometric art style, navy and cyan palette, subtle low-contrast texture"` |
| 结尾画面 | `<主题> future vision, <风格>, <色调>, inspirational, wide angle` | `"sustainable energy future landscape, digital art style, warm golden and green palette, wide angle inspirational"` |

**Prompt 质量检查：**
- 必须包含 4 个以上描述维度（主体/场景/风格/色调/构图）
- 禁止在 prompt 中要求生成文字/字母/数字（AI 图片中的文字不可读）
- 色调必须与 `design.md` 中选定的调色板一致
- 风格词必须具体（"cinematic photography" > "beautiful"；"flat illustration" > "nice"）

**风格词速查：**
| 风格 | 关键词 |
|------|-------|
| 商务摄影 | `corporate photography style, professional lighting, clean background` |
| 电影感 | `cinematic photography style, dramatic lighting, depth of field` |
| 扁平插画 | `flat illustration style, vector art, clean lines, solid colors` |
| 3D 渲染 | `3D render style, octane render, soft shadows, glossy materials` |
| 科技感 | `futuristic tech style, holographic, neon glow, dark background` |
| 水彩手绘 | `watercolor illustration style, soft brushstrokes, paper texture` |
| 极简主义 | `minimalist style, geometric shapes, lots of white space, single accent color` |

**Rules:**
- **Proactive by default**: Every deck must have a concrete reason to skip image generation, not a reason to use it. The burden of justification is on skipping, not on generating.
- Generated images must be purposeful assets that reinforce the deck's message, not generic filler.
- Each image prompt must include subject + style + color palette + composition to ensure quality and palette consistency.
- Do not place readable text inside generated images; keep all text as PPT elements.
- Record generated image paths and prompts in `design.md` or an asset manifest.
- If `mmx` is unavailable, unauthenticated, quota-limited, or blocked, record `prompt-brief-only` in `design.md` and continue with Unsplash/native visuals.
- Missing MiniMax plan, generated asset paths for used images, or documented skip/fallback reason blocks the quality gate.

**Tool 联动决策矩阵：**

| 场景 | Web search | MiniMax 图片 | Unsplash | 说明 |
|------|-----------|-------------|----------|------|
| 用户给主题，无资料 | 必须搜索 | 必须生成封面+1 | 运行工具 | research 模式全流程 |
| 用户给完整文档 | 跳过 | 生成封面 | 运行工具 | summary 模式，图片补充视觉 |
| 用户给大纲 | 按需补充 | 生成封面 | 运行工具 | outline 模式，搜索填补空白 |
| 纯数据/报表 | 跳过 | 跳过（记录原因） | 运行工具 | 数据页用图表/表格，不用图片 |
| 用户要求"最新数据" | 必须搜索 | 按需 | 运行工具 | 搜索结果直接进幻灯片内容 |

**备选工具矩阵（MiniMax 不可用时）：**

| 功能 | 首选 | 备选 1 | 备选 2 | 降级策略 |
|------|------|--------|--------|----------|
| AI 生图 | `mmx image generate` | `mcp__MiniMax__text_to_image`（MCP） | `generate-image` skill（多引擎） | Unsplash 真实照片 → `background_presets` 渐变/纹理 → 纯色 + `semantic_icon` 装饰 |
| 网页搜索 | `mcp__MiniMax__web_search` | `WebSearch` 内置工具 | `web-access` skill（浏览器自动化） | 直接使用已有知识（标注"未经实时验证"） |
| 图片理解 | `mcp__MiniMax__understand_image` | `WebFetch`（URL 图片分析） | Claude 原生视觉（本地文件直接读取） | 人工描述参考图特征 |
| 视频生成 | `mmx video generate` | 无直接 CLI 备选 | — | 跳过视频，用静态图片 + 动画过渡替代 |
| 语音合成 | `mmx speech synthesize` | 无直接 CLI 备选 | — | 跳过语音，PPT 本身不依赖音频 |
| 音乐生成 | `mmx music generate` | 无直接 CLI 备选 | — | 跳过背景音乐，PPT 演讲不需要配乐 |

**降级触发条件**（按优先级尝试，直到成功）：
1. `mmx` CLI 未安装或 `mmx auth` 失败 → 切换到 MCP 工具
2. MCP 工具 API key 未配置或配额耗尽 → 切换到 skill
3. Skill 也不可用 → 执行降级策略（Unsplash / 纯色背景 / 人工输入）

**每张 `design.md` 必须记录**：
```markdown
## Asset Pipeline
- Image generation: mmx (primary) → mcp__MiniMax__text_to_image (fallback)
- Web search: mcp__MiniMax__web_search (primary) → WebSearch (fallback)
- Fallback reason: <if降级，记录原因>
```

### Step 5: Select Icon Assets, Then Fallback to semantic_icon

**This step is mandatory for every deck.** Do not write any page YAML before it is complete.

Every deck must include at least 1-2 meaningful icons. Prefer mature frontend icon libraries first because they provide better recognizability, consistent geometry, and professional stroke discipline. Use PPT-native `semantic_icon` primitives only as a fallback or when editability inside PowerPoint is more important than icon fidelity.

Preferred icon sources:
- `lucide`: default first choice for clean outline icons, education, SaaS, dashboards, workflows, reading, and general presentations.
- `heroicons`: good for simple product/UI metaphors and business decks.
- `tabler-icons`: broad coverage for dashboards, data, operations, and technical decks.
- `remixicon`: broad mixed style set; use when Lucide/Heroicons do not cover the needed metaphor.
- `material-symbols`: use only when matching a Google/Material visual language.

Do not mix multiple icon libraries in the same deck unless `design.md` documents why the mix is needed. One icon family per deck is the default.

#### Workflow

1. **Map icon metaphors** — Identify 1-3 icons that visually reinforce the deck's message. Examples per domain:
   - Reading/books: open book, bookmark, lamp
   - Business: chart bar, handshake, target
   - Tech: chip, cloud, gear
   - Education: pencil, graduation cap, lightbulb
   - Health: heart, cross, leaf

2. **Try frontend icon libraries first** — Select exact icon names from the preferred library and record them in `design.md`.
   - Use SVG whenever possible, not screenshots.
   - Normalize all icons to one stroke width, normally `1.5` or `2`.
   - Use one deck palette color, normally `accent` or `text_muted`.
   - Keep icons line-based or filled consistently across the deck.
   - Use local asset paths in page YAML after the SVG/PNG is available.

Example inventory entry:

```markdown
- Library: lucide
- Icons:
  - book-open: cover and reading-benefits slides, meaning "reading / knowledge", 24mm, stroke 1.75, color #D97706
  - bookmark: action slide, meaning "save commitment", 14mm, stroke 1.75, color #D97706
- License/source note: use the library's open-source SVG icons; keep attribution/license metadata when assets are copied into output assets.
```

3. **Fallback to native semantic_icon only when needed** — Use primitive recipes when:
   - the required metaphor is unavailable in the chosen icon library
   - network/package access is unavailable and no local icon asset exists
   - the icon must remain fully editable as PPT-native shapes
   - the icon is simple enough to draw cleanly from 5-15 primitives

Each fallback icon lives in a 100×100 coordinate space (viewBox). Use the deck's `accent` color. Example:

```yaml
- type: semantic_icon
  color: "<accent color>"
  stroke_width: 1.6
  position: { x: 117mm, y: 26mm, width: 20mm, height: 14mm }
  primitives:
    - { type: line, x1: 18, y1: 14, x2: 50, y2: 4 }
    - { type: line, x1: 50, y1: 4, x2: 82, y2: 14 }
    - { type: line, x1: 18, y1: 14, x2: 18, y2: 88 }
    - { type: line, x1: 82, y1: 14, x2: 82, y2: 88 }
    - { type: line, x1: 18, y1: 88, x2: 50, y2: 78 }
    - { type: line, x1: 50, y1: 78, x2: 82, y2: 88 }
    - { type: line, x1: 50, y1: 4, x2: 50, y2: 78 }
```

4. **Record the inventory** in `design.md` before writing page YAML:
   - Icon source: frontend library name, local SVG/PNG path, or `native semantic_icon`
   - Icon name, semantic meaning, size, stroke width, color
   - For fallback semantic icons, include primitive count and primitive recipe
   - Which slide(s) each icon appears on

5. **Add to page YAML** — Place library icons as image/SVG assets when supported by the renderer, or place fallback `semantic_icon` elements alongside other elements.

Rules:
- Use a frontend icon library first; fallback to self-authored `semantic_icon` only with a recorded reason.
- Include at least 1 icon on the cover or closing slide when it reinforces the concept.
- Use one color from the deck palette, normally `accent`.
- Keep fallback primitives minimal (5-15 primitives per icon).
- Do not use emoji, clip art, random web images, or screenshots as icons.
- **禁止用几何图元拼接动物轮廓**（如椭圆+三角形拼鸭子）。动物形象辨识度低且视觉粗糙，改用抽象符号（书本、火焰、圆环等）或省略图标。
- Missing icon inventory, missing library/source note, or missing fallback primitive recipes in design.md blocks the quality gate.

### Step 6: Generate YAML Files (Generate-All-First)

Prerequisite: `outline.md`, `design.md`, and the image/icon asset plan are complete. If Unsplash photos are used, page YAML must reference local image paths from `manifest.json`; if MiniMax generated images are used, page YAML must reference local generated image paths from `output/<deck-name>/assets/generated`; if either image path is skipped, `design.md` must contain the skip reason. If icons are used, page YAML must reference the selected local icon assets or include the preplanned fallback `semantic_icon.primitives`.
For research/enrichment decks, `outline.md` must contain the information inventory and source-backed evidence before any YAML is written.

Write files in this order, all in one batch:

1. `deck.yml`
2. `pages/001_*.yml` through `pages/NNN_*.yml` (can use parallel sub-agents for pages)

Main file:
```yaml
version: "4.0"
type: presentation
title: "Presentation Title"
theme: default
style_preset: warm   # ← REQUIRED: one of the 10 presets from design/tokens.py
styles:
  h1:
    font: { family: "Microsoft YaHei UI", size: 36, weight: 700, color: "#D97706" }
  h2:
    font: { family: "Microsoft YaHei UI", size: 16, weight: 700, color: "#1C1917" }
  body:
    font: { family: "Microsoft YaHei UI", size: 13, weight: 400, color: "#1C1917" }
  caption:
    font: { family: "Microsoft YaHei UI", size: 10, weight: 400, color: "#78716C" }
pages:
  - pages/001_cover.yml
  - pages/002_content.yml
```
The `style_preset` auto-generates base styles; the `styles:` section can override individual tokens. Page YAML inline styles override both.

Page file rules:
- Every slide must implement the custom composition and visual hook promised in `outline.md`; a slide with only a title and bullet list is incomplete unless the source explicitly requires a plain text slide.
- Treat templates as syntax references only. Do not copy a template skeleton when a custom composition would be clearer or more memorable.
- Cards are optional information containers, not the default page architecture. Use cards only for genuinely parallel items.
- Related elements may share a panel/card container when containment improves comprehension; otherwise use editorial placement, annotation, diagram structure, image crop, axis, timeline, or typographic hierarchy.
- Card internal layout when cards are used: title (H2) → divider → body (Body) → optional caption (Caption).
- For each card/panel, verify child geometry before rendering: `child.y + child.height <= container.y + container.height - 3mm`, `child.x >= container.x + 4mm`, and `child.x + child.width <= container.x + container.width - 4mm`.
- If a card/panel content stack does not fit, first shorten wording, then enlarge the container, then change the layout. Never leave text visually spilling outside its parent container.
- For compact cards, compute the content group as one unit before placing children:
  - group top = first child `y`
  - group bottom = last child `y + height`
  - group center = `(group top + group bottom) / 2`
  - container visual center = `container.y + container.height / 2`
  - require `abs(group center - container visual center) <= 4mm` for centered cards
  - if the card contains a large number/date plus smaller labels, bias the group 1-3mm above geometric center so the visual weight feels centered
  - if the card is intentionally top-aligned, record that in `design.md` or the slide's visual notes
- Use `align: center`, `vertical_align: middle`, `margin: 0` for centered content inside cards.
- Never hand-tune coordinates to simulate centering.

#### Slide Transitions and Element Animations (Optional)

Both are optional. Use sparingly — a silent slide is better than a noisy one.

**Slide transition** — the visual effect when moving between slides. Set once per slide at the top level:

```yaml
slides:
  - layout: blank
    transition: { type: fade, speed: med }
```

Supported types: `fade`, `push`, `wipe`, `dissolve`, `split`, `blinds`, `cover`, `uncover`, `cut`, `diamond`, `fly`, `wheel`, `circle`. Speed: `slow`, `med`, `fast`.

**Element animation** — entrance/exit/emphasis effects on individual elements. Set per element:

```yaml
- type: text
  content: "标题"
  animation: { type: entry, effect: fade, duration: 0.6, delay: 0.2, trigger: after_previous }
```

Fields:
- `type`: `entry` / `exit` / `emphasis` / `motion_path` (default: `entry`, auto-inferred from effect name)
- `effect`: see effect tables below
- `duration`: seconds (default: 0.5)
- `delay`: seconds before this animation starts (default: 0)
- `trigger`: `on_click` / `with_previous` / `after_previous` (default: `on_click`)
- `easing`: `linear` / `ease_in` / `ease_out` / `ease_in_out` (default: `ease_out`)

**Entry effects (40+):**

| Group | Effects |
|-------|---------|
| Fade | `fade` |
| Wipe | `wipe_up`, `wipe_down`, `wipe_left`, `wipe_right` |
| Slide | `slide_up`, `slide_down`, `slide_left`, `slide_right` |
| Fly | `fly_in` |
| Zoom | `zoom_in`, `zoom_out_in` |
| Blinds | `blinds_h`, `blinds_v` |
| Checkerboard | `checkerboard`, `checkerboard_v` |
| Box | `box_in`, `box_out` |
| Shape | `diamond`, `plus`, `circle`, `shape_diamond`, `shape_plus` |
| Wheel | `wheel`, `wheel_1`, `wheel_2`, `wheel_3`, `wheel_4`, `wheel_8` |
| Random bars | `random_bars_h`, `random_bars_v` |
| Strips | `strips_upleft`, `strips_upright`, `strips_downleft`, `strips_downright` |

**Exit effects (mirror entry):** `fade_out`, `wipe_out_up/down/left/right`, `slide_out_up/down/left/right`, `fly_out`, `zoom_out`, `zoom_out_exit`, `blinds_out_h/v`, `checkerboard_out`, `box_out_exit`, `diamond_out`, `circle_out`, `random_bars_out_h/v`, `strips_out_*`

**Emphasis effects:**

| Group | Effects |
|-------|---------|
| Scale | `pulse` (110%), `grow` (150%), `shrink` (75%), `grow_s` (120%), `shrink_s` (90%) |
| Rotate | `spin_cw` (360deg), `spin_ccw` (-360deg), `spin_half_cw` (180deg), `spin_half_ccw` (-180deg) |
| Color | `color_pulse` (blue), `color_grow` (green), `color_warn` (yellow), `color_flash` (red) |

**Motion path effects:**

| Group | Effects |
|-------|---------|
| Linear | `path_right`, `path_left`, `path_up`, `path_down`, `path_up_right`, `path_down_right`, `path_up_left`, `path_down_left` |
| Arc | `path_arc_right`, `path_arc_left`, `path_loop` |
| Preset | `path_diamond`, `path_triangle`, `path_hexagon`, `path_figure_8` |

**Animation Decision Framework — AI 自主判断规则**

生成 PPT 时，AI 必须按以下三步决策，自主决定每个幻灯片的动画方案。不需要用户手动指定。

**第一步：判断幻灯片是否需要动画**

| 幻灯片角色 | 是否加动画 | 原因 |
|-----------|-----------|------|
| cover（封面） | 是 | 第一印象，标题入场建立节奏 |
| section_opener（章节引导） | 是 | 章节转折需要视觉信号 |
| data_peak（数据高潮） | 是 | 关键数字值得强调 |
| comparison（对比） | 否 | 静态并列更利于比较 |
| process（流程/步骤） | 部分 | 仅第一步动画，其余静态 |
| timeline（时间线） | 部分 | 仅起点动画 |
| summary（总结/回顾） | 否 | 回顾页应快速扫过 |
| closing（结尾） | 是 | 收尾节奏与封面呼应 |
| 普通内容页 | 否 | 信息密度高，动画干扰阅读 |

每张幻灯片的动画预算：**最多 1-3 个元素**。超过 3 个 = 噪音。

**第二步：选择动画元素**

在需要动画的幻灯片上，按以下优先级选择要动画的元素（从高到低，最多选 3 个）：

| 优先级 | 元素语义 | 选中条件 |
|--------|---------|---------|
| P0 | 主标题 | 每张动画幻灯片必选 |
| P1 | 关键数字 / 统计值 | 页面有大字号数字 (≥36pt) |
| P2 | 章节副标题 / 英文标签 | 与主标题构成叙事对 |
| P3 | 分隔线 / 装饰条 | 具有视觉引导功能的线条 |
| P4 | 信息卡片（仅第一张） | 卡片网格中位置最高/最左的那张 |

不选：正文段落、标签文字、数据表格、背景形状、小字号说明、卡片网格中的其余卡片。

**第三步：匹配效果**

按元素语义角色自动选择效果，不需要人工判断：

| 元素语义 | 效果 | 时长 | 触发 |
|---------|------|------|------|
| 主标题（中文大字） | `fade` | 0.6s | `after_previous`, delay 0.3 |
| 英文标签（全大写小字） | `fade` | 0.4s | `with_previous` |
| 章节副标题 | `slide_left` | 0.5s | `after_previous`, delay 0.2 |
| 关键数字（≥36pt） | `zoom_in` | 0.5s | `with_previous` |
| 分隔线 / 装饰条 | `wipe_right` | 0.4s | `with_previous` |
| 信息卡片（第一张） | `zoom_in` | 0.4s | `with_previous` |
| 底部结果条 | `wipe_up` | 0.5s | `after_previous`, delay 0.2 |
| 流程步骤（仅第一步） | `fade` | 0.4s | `after_previous`, delay 0.2 |
| 结论条目（第一条） | `fade` | 0.5s | `after_previous`, delay 0.3 |

**幻灯片过渡选择规则：**

| 幻灯片角色 | 过渡类型 | 速度 |
|-----------|---------|------|
| cover | `fade` | `med` |
| section_opener | `push` 或 `wipe` | `med` |
| data_peak | `fade` | `med` |
| comparison | `dissolve` | `med` |
| process / timeline | `wipe` | `med` |
| closing | `fade` | `med` |
| 普通内容 | `fade` | `med` |

同一份 PPT 的过渡类型应保持一致（最多用 2-3 种），避免"动画展"。

**禁止模式（硬规则）：**

1. 每个元素都加动画 → 禁止。这是噪音，不是专业感。
2. 正文/段落文字加动画 → 禁止。读者按自己节奏阅读。
3. 卡片网格中所有卡片都加动画 → 禁止。只动第一张。
4. `on_click` 用于正文 → 禁止。观众不应等待逐字出现。
5. 同一元素同时有入场 + 退出 → 禁止。
6. delay > 1.0s → 禁止。超过 1 秒的等待 = 死时间。
7. duration > 1.0s → 禁止。动画慢于 1 秒 = 拖沓。
8. 装饰性背景形状加动画 → 禁止。背景应即时出现。

**DSL 生成示例（AI 应自动生成此格式）：**

```yaml
# 封面页 — 标题动画 + 过渡
- layout: blank
  transition: { type: fade, speed: med }
  elements:
    - type: shape
      shape: rect
      position: { x: 35%, y: 18%, width: 30%, height: 0.4% }
      style: { fill: { color: "#38BDF8" } }
      # 装饰线 → with_previous，无 delay
      animation: { effect: wipe_right, duration: 0.4, trigger: with_previous }

    - type: text
      content: "标题文字"
      style: title
      position: { x: 10%, y: 24%, width: 80%, height: 30% }
      extra: { align: center }
      # 主标题 → fade，after_previous，delay 0.3
      animation: { effect: fade, duration: 0.6, delay: 0.3, trigger: after_previous }

    - type: text
      content: "正文不动画"
      style: body
      position: { x: 10%, y: 60%, width: 80%, height: 20% }
      # 正文 → 无 animation 字段

# 数据页 — 关键数字强调
- layout: blank
  transition: { type: fade, speed: med }
  elements:
    - type: text
      content: "0.1002"
      style:
        font: { size: 56, weight: 700 }
      animation: { effect: zoom_in, duration: 0.5, trigger: with_previous }
```

### Step 7: Unified Quality Gate

After ALL files are written, run:

```bash
python -m office_suite.tools.check output/<deck-name>/deck.yml --render pptx --output-dir output/<deck-name>/check
```

Blocking issues (must fix):
- YAML parse errors, missing page files
- IR validation errors, failed render
- Missing information inventory for research/enrichment decks
- Modern factual claims, statistics, rankings, dates, policies, product/company/person claims, or recommendations without recorded sources
- Missing MiniMax generated-image plan or documented skip/fallback reason in `design.md`
- Generated images used in page YAML without recorded prompts and local asset paths
- Out-of-bounds content
- Text, labels, or captions that visually belong to a card/panel but extend outside that card/panel
- Visibly unbalanced card/panel content where a centered card's internal group is top-heavy or bottom-heavy without a documented top-aligned design reason
- Confirmed text overlap or truncation
- Missing art direction, visual rhythm, signature motif, or per-slide visual hooks
- Missing creative premise, slide choreography, or anti-template strategy for creative/premium decks
- A 6+ slide deck using fewer than 5 distinct composition types without a documented strict-template constraint
- More than 2 card-grid slides in a 6+ slide deck without an inventory/catalog rationale
- Three or more slides sharing the same title-divider-card skeleton

Review items (consciously accept or fix):
- Font hierarchy warnings (>4 sizes)
- Color count warnings (>6 colors)
- Spacing warnings (intentional compact layout is acceptable)
- Decorative overlap

Fix order:
1. Syntax and missing-file errors
2. Out-of-bounds content
3. Text overflow and unreadable font sizes
4. Text occlusion
5. Misalignment and inconsistent spacing

## Layout System (Normative)

### Canvas
- 16:9, width: 254mm, height: 142.875mm
- Origin: top-left
- Constraints: `x + width <= 254mm`, `y + height <= 142.875mm`

### Page Regions
```text
Title band:     y 16-32mm
Body region:    y 40-116mm
Footer:         y 124-132mm
```

### Text Layout Fields
| Field | Values | Meaning |
|-------|--------|---------|
| `align` | left, center, right | Horizontal paragraph alignment |
| `vertical_align` | top, middle, bottom | Text frame vertical anchoring |
| `margin` | mm | Uniform internal margin |

For centered badges/labels inside shapes: set text box equal to shape bounds + `align: center` + `vertical_align: middle` + `margin: 0`.

### Card System
- Cards are containers, not decoration.
- Fill: `bg_surface`, radius: 3mm, border: 1pt `border` color.
- Do not use cards inside cards.
- Card text left-aligned for sentences; center-aligned for compact tiles.

### Repeated Elements
Repeated cards must be generated as a system:
- Same object type, width, height, internal alignment.
- Consistent gaps (4mm).
- Complete sequences. If the outline says 6 modules, render exactly 6.

## Visual Quality Rules

- **One message per slide**: Every content slide must have one dominant message. Move secondary detail to another slide.
- **Evidence before polish**: Factual slides must be grounded in gathered sources before visual design. Do not invent statistics, dates, rankings, quotes, named examples, or institutional claims for layout convenience.
- **Density limit**: Body text max 40-50 Chinese characters or ~80 English words per slide.
- **Data prominence**: In data slides, make the conclusion visually dominant; chart/table is supporting evidence.
- **Palette control**: Exactly 1 primary, 1 accent, neutrals, optional semantic colors. Never exceed 6 colors.
- **Typography control**: Max 4 font sizes per slide. Minimum body 12pt.
- **Alignment**: Use explicit layout fields for internal positioning; use coordinates only for container placement.
- **Composition**: Content pages should normally place the salience target near a rule-of-thirds point or use clear asymmetric balance; reserve dead-center composition for cover, chapter, quote, and closing pages.
- **Creative hook**: Each slide needs a visual reason to exist: one meaningful icon, diagram, image crop, oversized number, quote treatment, timeline, comparison axis, or structured panel.
- **Motif continuity**: Repeat one subtle topic-relevant motif across the deck so slides feel designed as a system, not as isolated pages.
- **Rhythm**: Alternate sparse, balanced, and dense slides intentionally. Avoid a deck where every page is the same card grid density or the same title-divider-card skeleton.
- **Decoration discipline**: Decorative elements must carry meaning or structure. Do not add unrelated blobs, random circles, heavy shadows, emoji, clip art, or ornamental borders to appear creative.
- **Card optical balance**: Treat each card's title, metric, icon, body, and caption as one content group. Center the group optically inside the container; do not let small captions drift toward the bottom or make the card feel visually lopsided.
- **Template discipline**: Templates are examples of valid DSL and spacing, not a design brief. Start from the deck's metaphor, audience, evidence, and slide role; only borrow template mechanics after the composition is decided.

## Build and Convert

```python
from office_suite.dsl.parser import parse_yaml
from office_suite.ir.compiler import compile_document
from office_suite.renderer.pptx.deck import PPTXRenderer

doc = parse_yaml("output/my_deck/deck.yml")
ir_doc = compile_document(doc)
PPTXRenderer().render(ir_doc, "output/my_deck/my_deck.pptx")
```

CLI:
```bash
python -m office_suite build output/my_deck/deck.yml -o output/my_deck/my_deck.pptx
```

For non-PPT formats:
```python
from office_suite.tools.convert import convert_dsl_file
convert_dsl_file("input.yml", "output.docx", "docx")
convert_dsl_file("input.yml", "output.xlsx", "xlsx")
convert_dsl_file("input.yml", "output.pdf", "pdf")
convert_dsl_file("input.yml", "output.html", "html")
```

## Non-PPT Formats

### DOCX
- Single YAML file, `type: document`
- Clear heading hierarchy, concise paragraphs, tables for comparisons.
- Verify: `python -m office_suite.tools.check document.yml --render docx`

### XLSX
- Single YAML file, `type: spreadsheet`
- Model data as tables; use charts only for trends/comparisons.
- Preserve numeric types, dates, percentages.

### PDF
- Fixed layout, print-safe margins, explicit block sizing.
- High-resolution images; avoid blurry screenshots.

### HTML
- `type: presentation` for slide-like sections, `type: document` for document-like pages.
- Semantic structure, responsive readability.

## Project Directory Structure

```text
output/<deck-name>/
  outline.md          # Structure contract
  design.md           # Style contract (palette, typography, layout patterns, spacing)
  deck.yml            # Main entry
  pages/
    001_cover.yml
    002_content.yml
    ...
  <deck-name>.pptx    # Rendered output
  check/              # Quality gate outputs
```
