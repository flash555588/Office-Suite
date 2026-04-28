"""项目方案模板"""

from ..registry import TemplateInfo, register_template

register_template(TemplateInfo(
    name="project_proposal",
    display_name="项目方案",
    category="business",
    doc_type="presentation",
    description="适用于项目立项、技术方案评审，包含背景、方案、架构、计划、预算。",
    variables={
        "title": "项目方案",
        "team": "技术团队",
        "date": "2026年4月",
        "primary_color": "#1E40AF",
        "background": "当前业务面临以下挑战：\n\n1. 用户量增长导致系统性能瓶颈\n2. 现有架构难以支撑新业务需求\n3. 运维成本持续上升",
        "solution": "核心方案：\n\n1. 微服务架构改造\n2. 引入缓存层和消息队列\n3. 数据库分库分表\n4. CI/CD 流水线自动化",
        "architecture": "系统架构：\n\n前端 -> API Gateway -> 微服务集群 -> 数据层\n\n技术栈：Go + gRPC + Redis + PostgreSQL + K8s",
        "timeline_rows": "4",
        "timeline": '[["阶段", "时间", "交付物"], ["需求分析", "第1-2周", "需求文档"], ["架构设计", "第3-4周", "设计文档"], ["开发实现", "第5-10周", "核心功能"]]',
        "budget": "预算概览：\n\n人力成本：6人 x 3个月 = 18人月\n基础设施：云服务器 + CDN + 存储\n总计预估：约 50 万元",
    },
    tags=["项目", "方案", "立项"],
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
        content: "{{team}} / {{date}}"
        style: { font: { size: 16, color: "#FFFFFF" } }
        position: { x: 30mm, y: 75mm, width: 194mm, height: 12mm }

  - layout: blank
    elements:
      - type: text
        content: "项目背景"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{background}}"
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
        content: "技术架构"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{architecture}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }

  - layout: blank
    elements:
      - type: text
        content: "实施计划"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: table
        rows: {{timeline_rows}}
        cols: 3
        data: {{timeline}}
        position: { x: 20mm, y: 30mm, width: 214mm, height: 100mm }

  - layout: blank
    elements:
      - type: text
        content: "预算与资源"
        style: heading
        position: { x: 20mm, y: 10mm, width: 214mm, height: 12mm }
      - type: text
        content: "{{budget}}"
        style: body
        position: { x: 20mm, y: 35mm, width: 214mm, height: 140mm }
''',
))
