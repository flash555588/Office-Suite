"""PPTX 渲染器 — IRDocument → .pptx 文件

使用 python-pptx 将 IR 渲染为 PowerPoint 文件。
坐标映射：mm → EMU (1mm = 36000 EMU)

架构位置：ir/compiler.py 输出 IRDocument → [本文件] → .pptx 文件

渲染流程：
  1. validate_ir_v2() — 渲染前校验 IR 合法性
  2. Presentation() — 创建空白演示文稿
  3. 遍历 IRDocument.children (SLIDE 节点)
  4. 每张幻灯片：设置背景 → 遍历子元素 → 分派到对应渲染方法
  5. 保存 .pptx 文件

模块拆分：
  - slide.py  — 幻灯片创建、背景、布局映射
  - shape.py  — 形状渲染、填充、边框
  - chart.py  — 图表渲染、数据构建
  - table.py  — 表格渲染、样式
  - style.py  — 样式解析、主题色、阴影/渐变/文本变换
  - animation.py — 动画 XML 注入
"""

import logging
from pathlib import Path

from pptx import Presentation
from pptx.util import Mm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from ...ir.types import IRDocument, IRNode, IRPosition, IRStyle, NodeType
from ...ir.validator import validate_ir_v2
from ..base import BaseRenderer, RendererCapability

from .slide import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM, render_slide, get_layout_index
from .shape import render_shape, get_shape_type
from .chart import render_chart, CHART_TYPE_MAP
from .table import render_table
from .style import resolve_style, apply_text_style, apply_shadow, apply_text_warp, hex_to_rgb
from .animation import apply_animations

logger = logging.getLogger(__name__)

# mm → EMU
MM_TO_EMU = 36000


class PPTXRenderer(BaseRenderer):
    """PowerPoint 渲染器

    Phase 2 增强：
    - 图表渲染（bar/column/line/pie/scatter 等）
    - 母版布局支持（预定义布局索引）
    - 渐变填充（线性/径向，多停止点）
    - 阴影/发光/透明度
    - 表格样式增强
    """

    def __init__(self):
        self._prs: Presentation | None = None

    @property
    def capability(self) -> RendererCapability:
        return RendererCapability(
            supported_node_types={
                NodeType.SLIDE, NodeType.TEXT, NodeType.IMAGE,
                NodeType.SHAPE, NodeType.TABLE, NodeType.CHART,
                NodeType.GROUP, NodeType.VIDEO,
            },
            supported_layout_modes={"absolute", "relative"},
            supported_text_transforms={"arch", "arch_up", "wave", "circle"},
            supported_animations={"slide_up", "fade_in", "scale_in", "fly_in"},
            supported_effects={"shadow", "glow", "gradient_fill", "opacity"},
            fallback_map={
                "duotone": "opacity",
                "blur": "shadow",
            },
        )

    def render(self, doc: IRDocument, output_path: str | Path) -> Path:
        """渲染 IRDocument 为 .pptx 文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        validation = validate_ir_v2(doc)
        for issue in validation.issues:
            print(f"[IR {issue.severity.value.upper()}] {issue}")
        if not validation.is_valid:
            print(f"[IR] 校验发现 {len(validation.errors)} 个错误，渲染可能不完整")

        self._prs = Presentation()
        self._prs.slide_width = Mm(int(SLIDE_WIDTH_MM))
        self._prs.slide_height = Mm(int(SLIDE_HEIGHT_MM))

        for slide_node in doc.children:
            if slide_node.node_type == NodeType.SLIDE:
                render_slide(self, slide_node, doc)

        self._prs.save(str(output_path))
        return output_path

    # ============================================================
    # 元素级分派
    # ============================================================

    def _render_element(self, slide, node: IRNode, doc: IRDocument):
        """渲染单个元素 — 按节点类型分派"""
        if node.node_type == NodeType.TEXT:
            self._render_text(slide, node, doc)
        elif node.node_type == NodeType.SHAPE:
            render_shape(self, slide, node, doc)
        elif node.node_type == NodeType.IMAGE:
            self._render_image(slide, node, doc)
        elif node.node_type == NodeType.TABLE:
            render_table(self, slide, node, doc)
        elif node.node_type == NodeType.CHART:
            render_chart(self, slide, node, doc)
        elif node.node_type == NodeType.GROUP:
            for child in node.children:
                self._render_element(slide, child, doc)
        else:
            self._render_placeholder(slide, node)

    def _render_text(self, slide, node: IRNode, doc: IRDocument):
        """渲染文本元素"""
        pos = node.position or IRPosition()
        style = resolve_style(self, node, doc)

        left, top, width, height = self._pos_to_emu(pos)
        if pos.is_center:
            left = Mm((SLIDE_WIDTH_MM - pos.width_mm) / 2)

        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = node.content or ""
        p.alignment = PP_ALIGN.LEFT

        if style:
            apply_text_style(p, style)

        if style and style.shadow:
            apply_shadow(txBox, style.shadow)

        if node.animations:
            apply_animations(slide, txBox, node.animations)

        if style and style.text_effect:
            apply_text_warp(txBox, style.text_effect)

    def _render_image(self, slide, node: IRNode, doc: IRDocument):
        """渲染图片元素"""
        pos = node.position or IRPosition()
        left, top, width, height = self._pos_to_emu(pos)

        source = node.source
        if isinstance(source, str):
            file_path = Path(source.replace("file://", ""))
            if file_path.exists():
                slide.shapes.add_picture(str(file_path), left, top, width, height)
                return

        self._render_placeholder(slide, node, left, top, width, height)

    def _render_placeholder(self, slide, node: IRNode, left=None, top=None, width=None, height=None):
        """渲染占位符（不支持的元素类型或缺失资源）"""
        if left is None:
            pos = node.position or IRPosition()
            left, top, width, height = self._pos_to_emu(pos)

        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(0xE0, 0xE0, 0xE0)
        shape.line.color.rgb = RGBColor(0x99, 0x99, 0x99)
        shape.line.dash_style = 2

        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"[{node.node_type.value}]"
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # ============================================================
    # 位置工具方法
    # ============================================================

    def _pos_to_emu(self, pos: IRPosition) -> tuple:
        """将 IRPosition (mm) 转换为 EMU 元组 (left, top, width, height)"""
        from pptx.util import Mm as _Mm

        x_mm = pos.x_mm
        y_mm = pos.y_mm
        w_mm = pos.width_mm if pos.width_mm > 0 else (SLIDE_WIDTH_MM - x_mm)
        h_mm = pos.height_mm if pos.height_mm > 0 else 7.5

        if y_mm + h_mm > SLIDE_HEIGHT_MM:
            original_h = h_mm
            h_mm = max(0, SLIDE_HEIGHT_MM - y_mm)
            if h_mm < original_h:
                logger.debug("[CLIP] y=%.1fmm h: %.1f->%.1fmm", y_mm, original_h, h_mm)

        if x_mm + w_mm > SLIDE_WIDTH_MM:
            original_w = w_mm
            w_mm = max(0, SLIDE_WIDTH_MM - x_mm)
            if w_mm < original_w:
                logger.debug("[CLIP] x=%.1fmm w: %.1f->%.1fmm", x_mm, original_w, w_mm)

        return _Mm(x_mm), _Mm(y_mm), _Mm(w_mm), _Mm(h_mm)

    # 样式代理方法（保持向后兼容）
    def _get_layout_index(self, name: str) -> int:
        return get_layout_index(name)

    def _resolve_style(self, node: IRNode, doc: IRDocument) -> IRStyle | None:
        return resolve_style(self, node, doc)

    def _apply_text_style(self, paragraph, style: IRStyle):
        apply_text_style(paragraph, style)

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> RGBColor:
        return hex_to_rgb(hex_str)

    @staticmethod
    def _get_shape_type(name: str):
        return get_shape_type(name)


# 需要在 _render_placeholder 中使用
from pptx.util import Pt
