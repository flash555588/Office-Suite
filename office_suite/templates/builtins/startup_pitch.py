"""创业路演模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="startup_pitch",
    display_name="创业路演",
    category="creative",
    doc_type="presentation",
    description="适用于创业大赛、融资路演、Demo Day，精简有力地展示项目价值。",
    variables={
        "title": "项目名称",
        "tagline": "一句话价值主张",
        "primary_color": "#7C3AED",
        "problem": "痛点：\n\nXX 人群在 XX 场景下，每天浪费 XX 小时在 XX 上。\n现有方案：贵 / 慢 / 难用。",
        "solution_detail": "解决方案：\n\n用 XX 技术，让用户 YY。\n一句话：我们是 XX 领域的 YY。",
        "traction": "数据验证：\n\n- 内测用户：XX 人\n- 日活：XX\n- NPS：XX\n- 月增长：XX%",
        "market_size": "市场规模：\n\n¥XX 亿市场，年增长 XX%\n我们先切 XX 细分赛道",
        "business_model_detail": "商业模式：\n\n- SaaS 订阅：¥XX/月\n- 交易抽成：XX%\n- 增值服务：XX",
        "team_brief": "团队：\n\nCEO - XX 公司前 XX\nCTO - XX 公司前 XX\nCMO - XX 公司前 XX",
        "ask_detail": "本轮融资：\n\n- 金额：¥XX 万\n- 出让：XX%\n- 用途：产品 50% / 增长 30% / 团队 20%",
    },
    tags=["路演", "创业", "融资"],
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
        content: "痛点"
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
        content: "{{solution_detail}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "数据验证"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{traction}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "市场规模"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{market_size}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "商业模式"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{business_model_detail}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "团队"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{team_brief}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "融资需求"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{ask_detail}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
