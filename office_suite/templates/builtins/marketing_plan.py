"""营销方案模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="marketing_plan",
    display_name="营销方案",
    category="business",
    doc_type="presentation",
    description="适用于市场营销策划、推广方案，包含目标、策略、渠道、预算。",
    variables={
        "title": "营销方案",
        "campaign": "活动名称",
        "primary_color": "#E11D48",
        "objective": "营销目标：\n\n1. 品牌曝光：XX 万次\n2. 新增用户：XX 万\n3. 转化率：XX%\n4. ROI：XX",
        "audience": "目标受众：\n\n- 年龄：25-35 岁\n- 职业：XX 行业从业者\n- 痛点：XX\n- 触达渠道：XX",
        "strategy": "营销策略：\n\n1. 内容营销：高质量内容输出\n2. 社交媒体：XX 平台运营\n3. KOL 合作：XX 位达人\n4. 活动策划：XX 主题活动",
        "table_rows": "4",
        "channels": '[["渠道", "预算", "预期效果"], ["微信公众号", "¥5,000", "阅读量10万+"], ["抖音", "¥20,000", "播放量50万+"], ["小红书", "¥10,000", "笔记曝光30万+"]]',
        "timeline": "执行时间线：\n\n第1周：预热期 - 悬念海报\n第2周：爆发期 - KOL 集中发布\n第3周：持续期 - 用户 UGC\n第4周：收尾期 - 数据复盘",
        "budget": "预算分配：\n\n内容制作：30%\n广告投放：40%\nKOL 合作：20%\n应急储备：10%\n\n总预算：¥XX 万",
    },
    tags=["营销", "推广", "方案"],
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
        content: "{{campaign}}"
        style: { font: { size: 18, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "营销目标"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{objective}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "目标受众"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{audience}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "营销策略"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{strategy}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "渠道规划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{table_rows}}
        cols: 3
        data: {{channels}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 80mm }

  - layout: blank
    elements:
      - type: text
        content: "执行计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{timeline}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 70mm }
      - type: text
        content: "预算"
        style: heading
        position: { x: 20mm, y: 110mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{budget}}"
        style: body
        position: { x: 20mm, y: 125mm, width: 214mm, height: 60mm }
''',
))
