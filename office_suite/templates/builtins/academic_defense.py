"""学术答辩模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="academic_defense",
    display_name="学术答辩",
    category="academic",
    doc_type="presentation",
    description="适用于毕业答辩、课题汇报、学术报告，包含研究背景、方法、实验、结论。",
    variables={
        "title": "论文标题",
        "author": "答辩人",
        "advisor": "导师：XX 教授",
        "institution": "XX 大学 XX 学院",
        "primary_color": "#1E40AF",
        "background": "研究背景：\n\n1. 研究领域现状\n2. 存在的问题\n3. 研究意义与价值",
        "method": "研究方法：\n\n1. 方法论选择与依据\n2. 技术路线\n3. 实验设计",
        "experiment": "实验结果：\n\n实验一：XX 数据集上准确率达到 XX%\n实验二：相比 baseline 提升 XX%\n消融实验：验证各模块贡献",
        "conclusion": "结论与展望：\n\n1. 主要贡献总结\n2. 创新点\n3. 局限性与未来工作",
        "table_rows": "4",
        "results": '[["方法", "指标A", "指标B"], ["Baseline", "85.2%", "78.3%"], ["方法1", "89.1%", "82.5%"], ["本文方法", "92.3%", "87.6%"]]',
        "publications": "发表论文：\n\n1. XX 期刊 (SCI 一区)\n2. XX 会议 (CCF-A)",
    },
    tags=["答辩", "学术", "论文"],
    content='''version: "4.0"
type: presentation
theme: fluent

styles:
  title:
    font: { size: 32, weight: 700, color: "#FFFFFF" }
    fill: { color: "{{primary_color}}" }
  heading:
    font: { size: 28, weight: 700, color: "#0F172A" }
  body:
    font: { size: 14, color: "#334155" }

slides:
  - layout: blank
    elements:
      - type: shape
        shape_type: rectangle
        style: { fill: { color: "{{primary_color}}" } }
        position: { x: 0mm, y: 0mm, width: 254mm, height: 142.875mm }
      - type: text
        content: "{{title}}"
        style: title
        position: { x: 30mm, y: 40mm, width: 194mm, height: 25mm }
      - type: text
        content: "{{author}}"
        style: { font: { size: 18, color: "#FFFFFF" } }
        position: { x: 30mm, y: 70mm, width: 194mm, height: 10mm }
      - type: text
        content: "{{advisor}}"
        style: { font: { size: 16, color: "#94A3B8" } }
        position: { x: 30mm, y: 85mm, width: 194mm, height: 10mm }
      - type: text
        content: "{{institution}}"
        style: { font: { size: 14, color: "#94A3B8" } }
        position: { x: 30mm, y: 100mm, width: 194mm, height: 10mm }

  - layout: blank
    elements:
      - type: text
        content: "研究背景"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{background}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "研究方法"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{method}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "实验结果"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{table_rows}}
        cols: 3
        data: {{results}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 60mm }
      - type: text
        content: "{{experiment}}"
        style: body
        position: { x: 20mm, y: 100mm, width: 214mm, height: 80mm }

  - layout: blank
    elements:
      - type: text
        content: "结论与展望"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{conclusion}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 80mm }
      - type: text
        content: "{{publications}}"
        style: body
        position: { x: 20mm, y: 120mm, width: 214mm, height: 60mm }
''',
))
