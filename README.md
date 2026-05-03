# Office Suite 4.0

**声明式 YAML DSL 文本处理引擎** — 用 YAML 描述设计意图，编译为 PPTX / DOCX / XLSX / PDF / HTML。

```
YAML DSL  ──→  Parser  ──→  IR Document  ──→  Renderer  ──→  .pptx / .docx / .xlsx / .pdf / .html
              (意图解析)    (统一中间表示)     (五格式后端)
```

> 架构类比 LLVM：声明式前端 → 中间表示 → 多目标后端渲染。

424 测试全部通过 | 5 种输出格式 | 13 个内置模板 | 5 种图表引擎 | 7 种布局系统 | 12 种入场/退出动画

---

## 快速开始

### 安装

```bash
git clone https://github.com/flash555588/Office-Suite.git
cd Office-Suite

# 核心（仅 DSL/IR，无可选后端）
pip install -e .

# 全部功能（PPTX + DOCX + XLSX + PDF + HTML）
pip install -e ".[full]"

# 开发（含 pytest + 覆盖率）
pip install -e ".[full,dev]"
```

可选后端可单独安装：

```bash
pip install -e ".[pptx]"   # 仅 PowerPoint
pip install -e ".[docx]"   # 仅 Word
pip install -e ".[xlsx]"   # 仅 Excel
pip install -e ".[pdf]"    # 仅 PDF
```

### 三行代码生成 PPT

```python
from office_suite.dsl.parser import parse_yaml
from office_suite.ir.compiler import compile_document
from office_suite.renderer.pptx.deck import PPTXRenderer

doc = parse_yaml("presentation.yml")
ir_doc = compile_document(doc)
PPTXRenderer().render(ir_doc, "output.pptx")
```

### CLI 命令

```bash
# 渲染 DSL 文件
office-suite build deck.yml -o output/deck.pptx

# 从内置模板生成
office-suite generate work_report -o output/work.pptx

# 质量检查（解析 → 编译 → 校验 → Lint → 渲染）
office-suite check deck.yml --render pptx

# 格式转换
office-suite convert input.yml output.docx docx
```

---

## DSL 示例

### 最小演示文稿

```yaml
version: "4.0"
type: presentation

slides:
  - layout: blank
    elements:
      - type: text
        content: "Hello World"
        position: { x: 50mm, y: 80mm, width: 150mm, height: 20mm }
        style:
          font: { family: "Arial", size: 44, weight: 700, color: "#1E293B" }
```

### 带动画、图表、背景的完整幻灯片

```yaml
slides:
  - layout: blank
    background_board:
      background: { type: color, color: "#0B1226" }
      illustration: { source: "cover.jpg", filter: blur(8px) }
      scrim: { opacity: 0.6 }
    elements:
      - type: text
        content: "数据分析报告"
        position: { x: 20mm, y: 40mm, width: 160mm, height: 30mm }
        animation: { type: fade_in, duration: 0.8 }
        style:
          font: { size: 48, weight: 700, color: "#FFFFFF" }

      - type: chart
        chart_type: bar
        data:
          labels: ["Q1", "Q2", "Q3", "Q4"]
          values: [120, 180, 210, 260]
        position: { x: 20mm, y: 80mm, width: 160mm, height: 80mm }
        animation: { type: slide_up, duration: 0.5, delay: 0.3 }
```

### 多文件管理

```yaml
# deck.yml（主文件）
version: "4.0"
type: presentation
pages:
  - pages/01_cover.yml
  - pages/02_content.yml
  - pages/03_chart.yml
  - pages/04_conclusion.yml
```

---

## 支持格式

| 格式 | 用途 | 渲染器 |
|:-----|:-----|:-------|
| `.pptx` | PowerPoint 演示文稿 | `renderer/pptx/deck.py` |
| `.docx` | Word 文档 | `renderer/docx/document.py` |
| `.xlsx` | Excel 表格 | `renderer/xlsx/workbook.py` |
| `.pdf` | PDF 文档 | `renderer/pdf/canvas.py` |
| `.html` | 网页 | `renderer/html/dom.py` |

格式之间可互转：

```python
from office_suite.tools.convert import convert_dsl_file

convert_dsl_file("input.yml", "output.docx", "docx")
convert_dsl_file("input.yml", "output.pdf",  "pdf")
```

---

## 核心功能

### 动画引擎

slide 级分组交错 — 同一触发组内的动画按 delay 自动链式播放：

```yaml
animation: { type: fade_in, duration: 0.8 }              # 点击时立即播放
animation: { type: slide_up, duration: 0.5, delay: 0.3 } # 上一个结束后等 300ms
animation: { type: zoom_in, duration: 0.5, delay: 0.5 }  # 再等 500ms
```

支持 12 种动画效果：

| 入场 | 退出 | 强调 |
|:-----|:-----|:-----|
| `fade_in` | `fade_out` | `pulse` |
| `slide_up/down/left/right` | `slide_out_up/down/left/right` | `grow` / `shrink` |
| `zoom_in` / `zoom_out` | `zoom_out_exit` | `spin_emphasis` |
| `fly_in` / `wipe_*` | | |

7 种缓动函数：`linear` / `ease_in` / `ease_out` / `ease_in_out` / `spring` / `bounce` / `orbit`

### 布局系统

7 种布局模式，可自由组合：

| 模式 | 说明 |
|:-----|:-----|
| `grid` | CSS Grid，支持 `template` / `gap` / `areas` |
| `flex` | Flexbox，支持 `direction` / `justify` / `align` / `gap` |
| `constraint` | 绝对约束（x/y/width/height） |
| `stack` | 垂直/水平堆叠，支持间距 |
| `sidebar` | 侧边栏 + 主区域 |
| `holy-grail` | 经典三栏布局 |
| `dashboard` | 仪表盘网格 |

### 图表渲染

5 种图表引擎，192 DPI 高清输出，自动检测 CJK 字体：

| 引擎 | 适用场景 |
|:-----|:---------|
| `matplotlib` | 通用统计图表（默认） |
| `plotly` | 交互式图表 |
| `vegalite` | 声明式可视化 |
| `ggplot2` | R 风格统计图 |
| `pgfplots` | LaTeX 出版级图表 |

```yaml
- type: chart
  chart_type: bar        # bar / column / line / pie / scatter / area / radar
  engine: matplotlib     # 可选：plotly / vegalite / ggplot2 / pgfplots
  data:
    labels: ["A", "B", "C"]
    values: [10, 20, 30]
```

### 主题系统

4 个预设主题，一键切换全局风格：

| 主题 | 风格 |
|:-----|:-----|
| `fluent` | Microsoft Fluent Design |
| `material3` | Google Material 3 |
| `apple_hig` | Apple Human Interface Guidelines |
| `universal` | 通用简约风格 |

```yaml
version: "4.0"
theme: fluent   # 切换主题只需改这一个字段
```

### 内置模板

13 个开箱即用的高质量模板：

| 模板 | 说明 |
|:-----|:-----|
| `work_report` | 工作汇报 |
| `project_proposal` | 项目方案 |
| `annual_report` | 年度报告 |
| `quarterly_review` | 季度复盘 |
| `product_launch` | 产品发布 |
| `business_plan` | 商业计划书 |
| `startup_pitch` | 创业路演 |
| `marketing_plan` | 营销方案 |
| `academic_defense` | 学术答辩 |
| `resume` | 简历 |
| `weekly_meeting` | 周会 |
| `training_course` | 培训课程 |
| `cover_styles` | 封面样式集 |

```bash
office-suite generate annual_report -o report.pptx
```

### AI 驱动

| 模块 | 功能 |
|:-----|:-----|
| `ai/intent.py` | 自然语言意图解析 → DSL 生成 |
| `ai/suggest.py` | 设计建议（布局、配色、排版） |
| `ai/critique.py` | 质量评审（一致性、可读性、专业度） |
| `ai/dsl_generator_prompt.py` | LLM 提示词模板（含图片生成决策流程） |

---

## 项目结构

```
office_suite/
├── dsl/                    # YAML 解析器 + Schema 验证 + 路径解析
├── ir/                     # 中间表示：编译器、样式级联、优化器
├── renderer/               # 五格式渲染器
│   ├── pptx/               #   PowerPoint（含动画引擎）
│   ├── docx/               #   Word
│   ├── xlsx/               #   Excel
│   ├── pdf/                #   PDF
│   └── html/               #   HTML
├── engine/                 # 引擎层
│   ├── layout/             #   7 种布局（grid / flex / constraint / ...）
│   ├── chart/              #   5 种图表引擎（matplotlib / plotly / ...）
│   ├── style/              #   颜色、渐变、阴影、透明度
│   ├── text/               #   富文本、艺术字、文本塑形
│   └── media/              #   图像处理、SVG
├── ai/                     # AI 模块：意图、建议、评审、提示词
├── pipeline/               # 计算图工作流：节点、调度、历史存储
├── components/             # 组件库（图表卡片、统计卡片、时间线、信息图）
├── templates/              # 13 个内置模板
├── hub/                    # 资源中枢：注册表、解析器、缓存、多 Provider
└── tools/                  # CLI 工具：build / check / convert / linter / batch
```

---

## 测试

```bash
pytest tests/ -v --cov       # 全量测试 + 覆盖率
pytest tests/ -q             # 快速运行
```

424 passed / 1 xfailed — 全绿。

| 阶段 | 覆盖范围 | 测试数 |
|:-----|:---------|-------:|
| Phase 1 | DSL 解析 + IR 编译 | 65 |
| Phase 2 | PPTX 渲染 | 60 |
| Phase 3 | Hub 资源管理 | 50 |
| Phase 4 | DOCX + XLSX | 24 |
| Phase 5 | AI 模块 | 42 |
| Phase 6 | 主题 + 组件 | 57 |
| Phase 7 | PDF + HTML | 30 |
| Phase 8 | 动画 + 艺术字 | 58 |
| Phase 9 | 模板系统 | 64 |
| Pipeline | 计算图工作流 | 39 |
| 其他 | 设计增强、样式、语义布局 | 61 |

---

## CLI 工具一览

| 命令 | 说明 |
|:-----|:-----|
| `office-suite build <file> -o <out>` | 渲染 DSL 文件 |
| `office-suite generate <name> -o <out>` | 从内置模板生成 |
| `office-suite check <file> --render <fmt>` | 统一质量门 |
| `office-suite convert <in> <out> <fmt>` | 格式转换 |
| `office-suite linter <file>` | DSL 规范检查 |
| `office-suite batch <glob>` | 批量处理 |
| `office-suite preview <file>` | 本地预览 |

---

## 路线图

| 优先级 | 特性 | 状态 |
|:-------|:-----|:-----|
| P0 | 文本、图片、形状、表格、坐标系统、样式级联 | 已完成 |
| P1 | 约束布局、Flexbox、动画、艺术字、图表 | 已完成 |
| P2 | 视频/音频、滤镜、路径文字、实时预览 | 规划中 |
| P3 | 3D 模型、地图 | 规划中 |

---

## 贡献

欢迎提交 Issue 和 Pull Request。

```bash
# 开发环境
pip install -e ".[full,dev]"
pytest tests/ -q

# 提交前检查
office-suite check your_deck.yml --render pptx
```

## 许可证

MIT License
