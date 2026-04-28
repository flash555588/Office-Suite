"""商业计划书模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="business_plan",
    display_name="商业计划书",
    category="business",
    doc_type="presentation",
    description="适用于创业项目、商业计划、融资路演，包含市场分析、商业模式、财务预测。",
    variables={
        "title": "商业计划书",
        "company": "公司/项目名称",
        "primary_color": "#0F172A",
        "problem": "市场痛点：\n\n目标用户在 XX 场景下，面临 YY 问题，现有解决方案存在 ZZ 不足。",
        "solution": "我们的解决方案：\n\n通过 XX 技术/模式，为用户提供 YY 价值，相比竞品具有 ZZ 优势。",
        "market": "市场规模：\n\nTAM：XX 亿\nSAM：XX 亿\nSOM：XX 亿\n\n年增长率：XX%",
        "business_model": "商业模式：\n\n收入来源：SaaS 订阅 + 增值服务\n客单价：¥XX/月\n目标客户：XX 类型企业",
        "team_intro": "核心团队：\n\nCEO：XX 背景\nCTO：XX 背景\nCMO：XX 背景",
        "financial": "财务预测（3年）：\n\nYear 1：营收 XX 万，亏损 XX 万\nYear 2：营收 XX 万，盈亏平衡\nYear 3：营收 XX 万，利润 XX 万",
        "ask": "融资需求：\n\n本轮融资：XX 万元\n出让股权：XX%\n资金用途：产品研发 60% / 市场推广 30% / 运营 10%",
    },
    tags=["商业", "计划书", "融资"],
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
        shape_type: rectangle
        style: { fill: { color: "{{primary_color}}" } }
        position: { x: 0mm, y: 0mm, width: 254mm, height: 142.875mm }
      - type: text
        content: "{{title}}"
        style: title
        position: { x: 30mm, y: 50mm, width: 194mm, height: 20mm }
      - type: text
        content: "{{company}}"
        style: { font: { size: 18, color: "#94A3B8" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "市场痛点"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{problem}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "解决方案"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{solution}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "市场规模"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{market}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "商业模式"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{business_model}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "核心团队"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{team_intro}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "财务预测"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{financial}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "融资需求"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{ask}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
