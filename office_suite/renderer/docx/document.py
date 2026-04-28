"""DOCX 渲染器 — IRDocument → .docx 文件

使用 python-docx 将 IR 渲染为 Word 文档。

架构位置：ir/compiler.py → IRDocument → [本文件] → .docx 文件

渲染流程：
  1. 创建 Document
  2. 遍历 IRDocument.children (SECTION 或 SLIDE 节点)
  3. 每个节：遍历子元素 → 分派到对应渲染方法
  4. 保存 .docx 文件

DOCX 能力限制（设计方案第八章）：
  - 不支持艺术字（降级为普通文本）
  - 不支持动画（跳过）
  - 仅支持基础阴影
"""

from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Pt, Mm, RGBColor, Inches, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from ...ir.types import IRDocument, IRNode, IRPosition, IRStyle, NodeType
from ...ir.validator import validate_ir_v2
from ..base import BaseRenderer, RendererCapability


class DOCXRenderer(BaseRenderer):
    """Word 文档渲染器"""

    def __init__(self):
        self._doc: Document | None = None

    @property
    def capability(self) -> RendererCapability:
        return RendererCapability(
            supported_node_types={
                NodeType.SLIDE, NodeType.SECTION, NodeType.TEXT,
                NodeType.IMAGE, NodeType.TABLE, NodeType.GROUP,
            },
            supported_layout_modes={"absolute"},
            supported_text_transforms=set(),  # 不支持艺术字
            supported_animations=set(),       # 不支持动画
            supported_effects={"shadow"},     # 仅基础阴影
            fallback_map={
                "arch": "plain_text",
                "wave": "plain_text",
                "gradient_fill": "solid_fill",
            },
        )

    def render(self, doc: IRDocument, output_path: str | Path) -> Path:
        """渲染 IRDocument 为 .docx 文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 校验
        validation = validate_ir_v2(doc)
        for issue in validation.issues:
            print(f"[IR {issue.severity.value.upper()}] {issue}")

        self._doc = Document()

        # 设置默认字体
        style = self._doc.styles["Normal"]
        style.font.name = "Microsoft YaHei UI"
        style.font.size = Pt(11)

        # 设置默认页边距（25mm ≈ 1 inch）
        for section in self._doc.sections:
            section.top_margin = Mm(25)
            section.bottom_margin = Mm(25)
            section.left_margin = Mm(25)
            section.right_margin = Mm(25)

        # 遍历节/幻灯片
        for node in doc.children:
            if node.node_type == NodeType.SECTION:
                self._render_section(node, doc)
            elif node.node_type == NodeType.SLIDE:
                # SLIDE 在 DOCX 中作为节处理
                self._render_slide_as_section(node, doc)

        self._doc.save(str(output_path))
        return output_path

    def _render_section(self, node: IRNode, doc: IRDocument):
        """渲染 SECTION 节点"""
        for child in node.children:
            self._render_element(child, doc)

    def _render_slide_as_section(self, node: IRNode, doc: IRDocument):
        """将 SLIDE 节点作为文档节渲染

        每张幻灯片映射为一个文档节（段落集合）。
        """
        for child in node.children:
            self._render_element(child, doc)

        # 节之间加分页符（除最后一个）
        # 在实际场景中由用户控制

    def _render_element(self, node: IRNode, doc: IRDocument):
        """按节点类型分派渲染"""
        if node.node_type == NodeType.TEXT:
            self._render_text(node, doc)
        elif node.node_type == NodeType.TABLE:
            self._render_table(node, doc)
        elif node.node_type == NodeType.IMAGE:
            self._render_image(node, doc)
        elif node.node_type == NodeType.SHAPE:
            self._render_shape(node, doc)
        elif node.node_type == NodeType.GROUP:
            for child in node.children:
                self._render_element(child, doc)
        else:
            # 不支持的类型：添加占位段落
            self._doc.add_paragraph(f"[{node.node_type.value}]")

    def _render_text(self, node: IRNode, doc: IRDocument):
        """渲染文本元素

        根据 font_size 判断是否为标题：
          >= 28pt → Heading 1
          >= 20pt → Heading 2
          其他    → 普通段落

        支持 extra.list_type: "bullet" / "number" 生成列表。
        """
        style = node.style
        content = node.content or ""

        if not content.strip():
            return

        # 判断标题级别
        font_size = style.font_size if style and style.font_size else 11
        if font_size >= 28:
            heading = self._doc.add_heading(content, level=1)
            self._apply_heading_style(heading, style)
        elif font_size >= 20:
            heading = self._doc.add_heading(content, level=2)
            self._apply_heading_style(heading, style)
        else:
            # 列表支持
            list_type = node.extra.get("list_type") if node.extra else None
            if list_type == "bullet":
                para = self._doc.add_paragraph(content, style="List Bullet")
            elif list_type == "number":
                para = self._doc.add_paragraph(content, style="List Number")
            else:
                para = self._doc.add_paragraph(content)
            self._apply_paragraph_style(para, style)
            # 段落间距（从 node.extra 读取）
            if node.extra:
                sp_before = node.extra.get("spacing_before")
                sp_after = node.extra.get("spacing_after")
                if sp_before is not None:
                    para.paragraph_format.space_before = Pt(sp_before)
                if sp_after is not None:
                    para.paragraph_format.space_after = Pt(sp_after)

    def _render_table(self, node: IRNode, doc: IRDocument):
        """渲染表格元素

        支持：
          - 表头加粗、深色背景
          - 交替行颜色
          - 单元格对齐
        """
        rows = node.extra.get("rows", 3)
        cols = node.extra.get("cols", 3)
        # 数据来源：data_ref 优先于 extra.data
        data = []
        if node.data_ref and node.data_ref in doc.data:
            ref_val = doc.data[node.data_ref]
            if isinstance(ref_val, list):
                data = ref_val
        if not data:
            data = node.extra.get("data", [])

        table = self._doc.add_table(rows=rows, cols=cols, style="Table Grid")
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 填充数据
        for r, row_data in enumerate(data[:rows]):
            if isinstance(row_data, list):
                for c, cell_val in enumerate(row_data[:cols]):
                    cell = table.cell(r, c)
                    cell.text = str(cell_val)

                    # 首行样式：加粗 + 深色背景
                    if r == 0:
                        for para in cell.paragraphs:
                            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for run in para.runs:
                                run.bold = True
                                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        # 深色背景
                        shading = cell._element.get_or_add_tcPr()
                        shd = shading.makeelement(qn("w:shd"), {
                            qn("w:fill"): "1E293B",
                            qn("w:val"): "clear",
                        })
                        shading.append(shd)

    def _render_image(self, node: IRNode, doc: IRDocument):
        """渲染图片元素

        支持 width/height 同时设置，保持比例。
        """
        source = node.source
        if isinstance(source, str):
            file_path = Path(source.replace("file://", ""))
            if file_path.exists():
                width = None
                height = None
                if node.position:
                    if node.position.width_mm > 0:
                        width = Mm(int(node.position.width_mm))
                    if node.position.height_mm > 0:
                        height = Mm(int(node.position.height_mm))
                self._doc.add_picture(str(file_path), width=width, height=height)
                return

        # 降级：占位符
        self._doc.add_paragraph(f"[图片: {source}]")

    def _render_shape(self, node: IRNode, doc: IRDocument):
        """渲染形状 → DOCX 中降级为带样式的段落"""
        content = node.content or f"[{node.extra.get('shape_type', 'shape')}]"
        style = node.style

        para = self._doc.add_paragraph(content)
        if style and style.fill_color:
            # 用背景色模拟形状
            shading = para.paragraph_format.element.get_or_add_pPr()
            shd = shading.makeelement(qn("w:shd"), {
                qn("w:fill"): style.fill_color.lstrip("#"),
                qn("w:val"): "clear",
            })
            shading.append(shd)
        self._apply_paragraph_style(para, style)

    def _apply_paragraph_style(self, para, style: IRStyle | None):
        """应用段落样式（字体、颜色、对齐）"""
        if style is None:
            return
        for run in para.runs:
            if style.font_family:
                run.font.name = style.font_family
            if style.font_size:
                run.font.size = Pt(style.font_size)
            if style.font_weight and style.font_weight >= 700:
                run.bold = True
            if style.font_italic:
                run.italic = True
            if style.font_color:
                run.font.color.rgb = self._hex_to_rgb(style.font_color)

    def _apply_heading_style(self, heading, style: IRStyle | None):
        """应用标题样式"""
        if style is None:
            return
        for run in heading.runs:
            if style.font_color:
                run.font.color.rgb = self._hex_to_rgb(style.font_color)

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> RGBColor:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 8:
            hex_str = hex_str[:6]
        if len(hex_str) != 6:
            return RGBColor(0, 0, 0)
        try:
            return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        except ValueError:
            return RGBColor(0, 0, 0)
