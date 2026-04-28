"""培训课件模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="training_course",
    display_name="培训课件",
    category="academic",
    doc_type="presentation",
    description="适用于内部培训、技术分享、课程教学，包含知识要点、示例演示、总结回顾。",
    variables={
        "title": "培训主题",
        "instructor": "讲师姓名",
        "date": "2026年4月",
        "primary_color": "#059669",
        "outline": "课程大纲：\n\n1. 基础概念\n2. 核心原理\n3. 实战演练\n4. 常见问题\n5. 总结回顾",
        "key_concepts": "核心概念：\n\n概念一：详细说明\n概念二：详细说明\n概念三：详细说明",
        "demo_content": "演示示例：\n\n步骤1：操作说明\n步骤2：操作说明\n步骤3：操作说明",
        "summary": "课程总结：\n\n1. 掌握了 XX 基础\n2. 理解了 YY 原理\n3. 能够独立完成 ZZ",
        "qa": "Q&A 环节",
    },
    tags=["培训", "课件", "教学"],
    content='''version: "4.0"
type: presentation
theme: fluent

styles:
  title:
    font: { size: 36, weight: 700, color: "#FFFFFF" }
    fill: { color: "{{primary_color}}" }
  heading:
    font: { size: 28, weight: 700, color: "#0F172A" }
  body:
    font: { size: 14, color: "#334155" }

slides:
  - layout: blank
    elements:
      - type: shape
        shape_type: rounded_rectangle
        style: { fill: { color: "{{primary_color}}" } }
        position: { x: 0mm, y: 0mm, width: 254mm, height: 142.875mm }
      - type: text
        content: "{{title}}"
        style: title
        position: { x: 30mm, y: 50mm, width: 194mm, height: 20mm }
      - type: text
        content: "{{instructor}} / {{date}}"
        style: { font: { size: 16, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "课程大纲"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{outline}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "核心概念"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{key_concepts}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "实战演示"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{demo_content}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "总结"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{summary}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 100mm }
      - type: text
        content: "{{qa}}"
        style: { font: { size: 36, weight: 700, color: "#059669" } }
        position: { x: 20mm, y: 140mm, width: 214mm, height: 20mm }
''',
))
