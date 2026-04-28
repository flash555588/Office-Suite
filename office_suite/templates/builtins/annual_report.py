"""年度报告模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="annual_report",
    display_name="年度报告",
    category="business",
    doc_type="presentation",
    description="适用于公司/团队年度总结报告，包含业绩回顾、数据分析、战略规划。",
    variables={
        "title": "2025 年度报告",
        "company": "公司名称",
        "primary_color": "#0F172A",
        "revenue": "¥12.8M",
        "growth": "+35%",
        "customers": "500+",
        "achievement_summary": "2025年度核心业绩：\n\n1. 营收同比增长35%\n2. 新增客户200+\n3. 产品迭代12个版本\n4. 团队规模扩大至45人",
        "table_rows": "5",
        "quarterly_data": '[["季度", "营收", "增长率"], ["Q1", "¥2.8M", "+25%"], ["Q2", "¥3.1M", "+30%"], ["Q3", "¥3.4M", "+38%"], ["Q4", "¥3.5M", "+42%"]]',
        "strategy_2026": "2026年战略重点：\n\n1. 产品国际化\n2. AI 能力集成\n3. 企业级客户拓展\n4. 技术基础设施升级",
    },
    tags=["年度", "报告", "总结"],
    content='''version: "4.0"
type: presentation
theme: fluent

styles:
  title:
    font: { size: 40, weight: 700, color: "#FFFFFF" }
    fill: { color: "{{primary_color}}" }
  heading:
    font: { size: 28, weight: 700, color: "#0F172A" }
  body:
    font: { size: 14, color: "#334155" }
  accent:
    font: { size: 48, weight: 700, color: "#0078D4" }

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
        content: "年度亮点"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{revenue}}"
        style: accent
        position: { x: 20mm, y: 35mm, width: 70mm, height: 20mm }
      - type: text
        content: "年度营收"
        style: body
        position: { x: 20mm, y: 55mm, width: 70mm, height: 8mm }
      - type: text
        content: "{{growth}}"
        style: { font: { size: 48, weight: 700, color: "#10B981" } }
        position: { x: 95mm, y: 35mm, width: 70mm, height: 20mm }
      - type: text
        content: "同比增长"
        style: body
        position: { x: 95mm, y: 55mm, width: 70mm, height: 8mm }
      - type: text
        content: "{{customers}}"
        style: accent
        position: { x: 170mm, y: 35mm, width: 60mm, height: 20mm }
      - type: text
        content: "客户数量"
        style: body
        position: { x: 170mm, y: 55mm, width: 60mm, height: 8mm }

  - layout: blank
    elements:
      - type: text
        content: "业绩回顾"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{achievement_summary}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "季度数据"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{table_rows}}
        cols: 3
        data: {{quarterly_data}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 80mm }

  - layout: blank
    elements:
      - type: text
        content: "2026 战略规划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{strategy_2026}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
