"""工作汇报模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="work_report",
    display_name="工作汇报",
    category="business",
    doc_type="presentation",
    description="适用于日常工作汇报，包含工作总结、关键成果、数据分析、下期计划。",
    variables={
        "title": "2026 Q1 工作汇报",
        "author": "汇报人",
        "date": "2026年4月",
        "primary_color": "#0078D4",
        "work_summary": "本期主要完成了以下工作：\n\n1. 项目 A 核心功能开发\n2. 性能优化，响应时间降低 40%\n3. 完成技术方案评审",
        "table_rows": "4",
        "key_results": '[["指标", "目标", "实际"], ["完成需求", "10", "12"], ["修复 Bug", "20", "25"], ["代码评审", "30", "35"]]',
        "next_plan": "下期重点工作：\n\n1. 项目 B 启动\n2. 技术债务清理\n3. 团队知识分享",
    },
    tags=["汇报", "工作", "季度"],
    content='''version: "4.0"
type: presentation
theme: fluent

styles:
  title:
    font: { size: 36, weight: 700, color: "#FFFFFF" }
    fill: { color: "{{primary_color}}" }
  subtitle:
    font: { size: 16, color: "#64748B" }
  heading:
    font: { size: 28, weight: 700, color: "#0F172A" }
  body:
    font: { size: 14, color: "#334155" }
  accent:
    font: { size: 48, weight: 700, color: "{{primary_color}}" }

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
        content: "{{author}} / {{date}}"
        style: subtitle
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "目录"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "01  本期工作总结\\n02  关键成果展示\\n03  数据分析\\n04  下期计划"
        style: body
        position: { x: 30mm, y: 35mm, width: 194mm, height: 100mm }

  - layout: blank
    elements:
      - type: text
        content: "本期工作总结"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{work_summary}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "关键成果"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{table_rows}}
        cols: 3
        data: {{key_results}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 100mm }

  - layout: blank
    elements:
      - type: text
        content: "下期计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{next_plan}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
