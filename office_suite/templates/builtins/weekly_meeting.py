"""周会汇报模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="weekly_meeting",
    display_name="周会汇报",
    category="business",
    doc_type="presentation",
    description="适用于团队周会快速同步，包含本周进展、问题阻塞、下周计划。",
    variables={
        "title": "周会汇报",
        "team": "团队名称",
        "week": "第17周 (4.21 - 4.25)",
        "primary_color": "#0078D4",
        "done_items": "本周完成：\n\n1. 功能 A 开发完成并提测\n2. 修复 3 个线上 Bug\n3. 完成代码评审 5 项",
        "blocked_items": "阻塞问题：\n\n1. [阻塞] 第三方 API 响应超时，需协调\n2. [风险] 测试环境资源不足",
        "plan_items": "下周计划：\n\n1. 功能 B 开发\n2. 性能测试\n3. 技术方案评审",
        "table_rows": "4",
        "progress": '[["任务", "负责人", "状态"], ["功能A", "张三", "已完成"], ["功能B", "李四", "进行中"], ["Bug修复", "王五", "已完成"]]',
    },
    tags=["周会", "汇报", "同步"],
    content='''version: "4.0"
type: presentation
theme: fluent

styles:
  title:
    font: { size: 32, weight: 700, color: "#FFFFFF" }
    fill: { color: "{{primary_color}}" }
  heading:
    font: { size: 24, weight: 700, color: "#0F172A" }
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
        content: "{{team}} / {{week}}"
        style: { font: { size: 16, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "本周进展"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{done_items}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 60mm }
      - type: text
        content: "任务进度"
        style: heading
        position: { x: 20mm, y: 100mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{table_rows}}
        cols: 3
        data: {{progress}}
        position: { x: 20mm, y: 115mm, width: 214mm, height: 60mm }

  - layout: blank
    elements:
      - type: text
        content: "问题与阻塞"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{blocked_items}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "下周计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{plan_items}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
