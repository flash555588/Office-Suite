"""季度复盘模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="quarterly_review",
    display_name="季度复盘",
    category="business",
    doc_type="presentation",
    description="适用于季度业务复盘，包含目标回顾、数据分析、经验总结、改进计划。",
    variables={
        "title": "Q1 季度复盘",
        "team": "团队名称",
        "primary_color": "#0078D4",
        "target_review": "目标回顾：\n\n目标A：完成度 120%\n目标B：完成度 95%\n目标C：完成度 80%",
        "data_analysis": "数据分析：\n\n核心指标：\n- DAU：XX 万 (环比 +XX%)\n- 留存率：XX% (环比 +XX%)\n- 收入：¥XX 万 (环比 +XX%)",
        "what_went_well": "做得好的：\n\n1. XX 策略效果超预期\n2. 团队协作效率提升\n3. 技术架构优化成功",
        "what_to_improve": "待改进的：\n\n1. 需求变更管理不够规范\n2. 测试覆盖率不足\n3. 文档更新滞后",
        "action_items": "改进计划：\n\n1. 建立需求变更审批流程\n2. 自动化测试覆盖率提升至 80%\n3. 每周文档同步检查",
    },
    tags=["复盘", "季度", "总结"],
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
        content: "{{team}}"
        style: { font: { size: 16, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "目标回顾"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{target_review}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "数据分析"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{data_analysis}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "做得好的"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{what_went_well}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "待改进的"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{what_to_improve}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "改进计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{action_items}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
