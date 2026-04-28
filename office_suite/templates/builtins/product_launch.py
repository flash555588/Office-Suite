"""产品发布模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="product_launch",
    display_name="产品发布",
    category="creative",
    doc_type="presentation",
    description="适用于新产品发布、功能上线，包含产品亮点、特性介绍、定价方案。",
    variables={
        "title": "产品名称",
        "tagline": "一句话描述产品价值",
        "primary_color": "#7C3AED",
        "product_intro": "产品简介：\n\n这是一款面向 XX 场景的创新产品，解决了用户在 YY 方面的核心痛点。",
        "feature_rows": "4",
        "features": '[["特性", "说明", "价值"], ["特性一", "详细描述", "用户收益"], ["特性二", "详细描述", "用户收益"], ["特性三", "详细描述", "用户收益"]]',
        "pricing": "定价方案：\n\n基础版：免费\n专业版：¥99/月\n企业版：联系销售",
        "launch_date": "2026年5月正式发布",
    },
    tags=["产品", "发布", "上线"],
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
        content: "{{tagline}}"
        style: { font: { size: 18, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "产品简介"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{product_intro}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "核心特性"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{feature_rows}}
        cols: 3
        data: {{features}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 100mm }

  - layout: blank
    elements:
      - type: text
        content: "定价方案"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{pricing}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "发布计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{launch_date}}"
        style: { font: { size: 24, weight: 700, color: "#7C3AED" } }
        position: { x: 20mm, y: 40mm, width: 214mm, height: 20mm }
''',
))
