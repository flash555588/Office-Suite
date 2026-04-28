# Office Suite 4.0

全媒体融合文档引擎 — 从声明式 DSL 编译到任意文档格式。

## 核心流程

```
YAML DSL → Parser → IR Document → Renderer → .pptx / .docx / .xlsx / .pdf / .html
```

## 快速开始

```python
from office_suite.dsl.parser import parse_yaml
from office_suite.ir.compiler import compile_document
from office_suite.renderer.pptx.deck import PPTXRenderer

# 1. 解析 DSL
doc = parse_yaml("presentation.yml")

# 2. 编译为 IR
ir_doc = compile_document(doc)

# 3. 渲染
renderer = PPTXRenderer()
renderer.render(ir_doc, "output.pptx")
```

## 工具脚本

```bash
# 生成文档（输出到 demo_output/<项目名>/）
py -m office_suite.tools.generate <yaml文件名>

# 示例：生成苹果的好处 PPT 和 PDF
py -m office_suite.tools.generate apple_benefits
```

## DSL 示例

```yaml
version: "4.0"
type: presentation
theme: default

slides:
  - layout: blank
    elements:
      - type: text
        content: "Hello World"
        position: { x: 50mm, y: 80mm, width: 150mm, height: 20mm }
        style:
          font: { family: "Arial", size: 44, weight: 700, color: "#1E293B" }
```

## 支持格式

| 格式 | 状态 |
|------|------|
| `.pptx` | 已支持 |
| `.docx` | 已支持 |
| `.xlsx` | 已支持 |
| `.pdf` | 已支持 |
| `.html` | 已支持 |

## 渲染器能力矩阵

| 特性 | PPTX | DOCX | XLSX | PDF | HTML |
|------|------|------|------|-----|------|
| 文本 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 图片 | ✅ | ✅ | - | ✅ | ✅ |
| 形状 | ✅ | ✅ | - | ✅ | ✅ |
| 表格 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 图表 | ✅ | - | ✅ | ✅ | ✅ |
| 分组 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 分节 (Section) | - | ✅ | ✅ | ✅ | ✅ |
| 绝对坐标 | ✅ | ✅ | - | ✅ | ✅ |
| 相对坐标 | ✅ | ✅ | - | - | ✅ |
| 艺术字 | ✅ | 降级 | - | 降级 | 降级 |
| 动画 | ✅ | - | - | - | - |
| 阴影 | ✅ | ✅ | - | ✅ | ✅ |
| 渐变 | ✅ | 降级 | 降级 | ✅ | ✅ |

**降级策略**: 不支持的特性自动降级为可用替代（如艺术字→纯文本，图表→表格）。

## 项目结构

```
office_suite/
├── dsl/           # DSL 解析器
├── ir/            # 中间表示层
├── renderer/      # 渲染器（pptx/docx/xlsx/pdf/html）
├── engine/        # 布局/样式/文本引擎
├── components/    # 内置组件
├── templates/     # 预设模板
├── themes/        # 主题系统
├── tools/         # 工具脚本
└── hub/           # 资源管理
```

## 特性分级

| 等级 | 特性 |
|------|------|
| P0 | 文本、图片、形状、表格、绝对/相对坐标、样式级联 |
| P1 | 约束布局、Flexbox、动画、艺术字 |
| P2 | 视频/音频、滤镜、路径文字、实时预览 |
| P3 | 3D 模型、地图 |
