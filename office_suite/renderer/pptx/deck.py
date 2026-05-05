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

样式处理：
  编译器已完成级联，node.style 是最终合并后的 IRStyle。
  渲染器用 _style_val() 处理 None 值，回退到 _STYLE_DEFAULTS。

降级策略（设计方案第八章）：
  capability 声明了支持的节点类型和效果，
  不支持的特性通过 fallback_map 降级（如 duotone → opacity）。
"""

import logging
from dataclasses import replace as dc_replace
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Mm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData

from ...ir.types import IRDocument, IRNode, IRPosition, IRStyle, NodeType
from ...ir.validator import validate_ir_v2
from ..base import BaseRenderer, RendererCapability
from .animation import apply_animations
from ...engine.text.path_text import parse_svg_path_struct

# mm → EMU
MM_TO_EMU = 36000

from ...constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM

# 图表类型映射
CHART_TYPE_MAP = {
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "bar_stacked": XL_CHART_TYPE.BAR_STACKED,
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "column_stacked": XL_CHART_TYPE.COLUMN_STACKED,
    "line": XL_CHART_TYPE.LINE,
    "line_marked": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
    "doughnut": XL_CHART_TYPE.DOUGHNUT,
    "area": XL_CHART_TYPE.AREA,
    "scatter": XL_CHART_TYPE.XY_SCATTER,
    "radar": XL_CHART_TYPE.RADAR,
}


def _ensure_run_rpr(run):
    """确保文本 run 有 a:rPr 元素。

    OOXML 规范要求每个 a:r 必须有 a:rPr 子元素。
    python-pptx 只在设置 font 属性时才创建 rPr，
    因此当 run 未设置任何格式时手动注入空 <a:rPr/>（不影响样式继承）。
    """
    from lxml import etree
    rPr_ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}rPr"
    if run._r.find(rPr_ns) is None:
        # a:rPr 必须是 a:r 的第一个子元素（在 a:t 之前）
        rpr = etree.Element(rPr_ns)
        run._r.insert(0, rpr)


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
            supported_layout_modes={"absolute", "relative", "grid", "flex", "constraint"},
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

        # 增强版 IR 校验
        validation = validate_ir_v2(doc)
        for issue in validation.issues:
            logger.log(
                logging.ERROR if issue.severity.value == "error" else logging.WARNING,
                "[IR %s] %s", issue.severity.value.upper(), issue,
            )
        if not validation.is_valid:
            logger.warning("[IR] 校验发现 %d 个错误，渲染可能不完整", len(validation.errors))

        # 创建演示文稿
        self._prs = Presentation()
        self._prs.slide_width = Mm(SLIDE_WIDTH_MM)
        self._prs.slide_height = Mm(SLIDE_HEIGHT_MM)

        # 渲染每张幻灯片
        for slide_node in doc.children:
            if slide_node.node_type == NodeType.SLIDE:
                self._render_slide(slide_node, doc)

        # 保存
        self._prs.save(str(output_path))
        return output_path

    # ============================================================
    # 幻灯片级渲染
    # ============================================================

    def _render_slide(self, slide_node: IRNode, doc: IRDocument):
        """渲染单张幻灯片

        母版布局索引（python-pptx 默认模板）：
          0  = Title Slide
          1  = Title and Content
          2  = Section Header
          3  = Two Content
          4  = Comparison
          5  = Title Only
          6  = Blank
          7  = Content with Caption
          8  = Picture with Caption
        """
        # 获取布局（默认 blank=6）
        layout_name = slide_node.extra.get("layout", "blank")
        layout_idx = self._get_layout_index(layout_name)
        slide_layout = self._prs.slide_layouts[layout_idx]
        slide = self._prs.slides.add_slide(slide_layout)

        # 重置动画计数器和缓冲区，确保每个 slide 内 ID 唯一
        from .animation import reset_anim_id_counter, reset_anim_buffer, flush_slide_animations
        reset_anim_id_counter()
        reset_anim_buffer()

        # 设置背景
        bg_board = slide_node.extra.get("background_board")
        if bg_board:
            self._render_background_board(slide, bg_board)

        bg_data = slide_node.extra.get("background")
        if bg_data and not bg_board:
            self._set_background(slide, bg_data)
        elif not bg_board and not bg_data:
            self._set_background(slide, {"type": "color", "color": "#FFFFFF"})

        # 布局解析：grid / flex / constraint / 语义布局 模式
        self._resolve_layout_if_needed(slide_node)

        # card_container：为子元素添加背景卡片（圆角 + 阴影）
        if slide_node.extra.get("card_container"):
            self._apply_card_container(slide, slide_node)

        # 渲染元素
        for elem_node in slide_node.children:
            self._render_element(slide, elem_node, doc)

        # 幻灯片切换效果
        transition_data = slide_node.extra.get("transition")
        if transition_data:
            from .transition import apply_transition
            apply_transition(slide, transition_data)

        # 所有形状渲染完毕后，统一分组写入动画 XML
        flush_slide_animations(slide)

    def _resolve_layout_if_needed(self, slide_node: IRNode):
        """若幻灯片使用 grid/flex/constraint/语义布局，解析子元素位置。"""
        from ..layout_resolver import LayoutResolver

        resolver = LayoutResolver(
            container_width=SLIDE_WIDTH_MM,
            container_height=SLIDE_HEIGHT_MM,
        )
        # LayoutResolver.resolve_children 内部已处理语义布局名称解析
        positions = resolver.resolve_children(slide_node)
        for i, child in enumerate(slide_node.children):
            key = child.id or str(i)
            if key in positions:
                child.position = positions[key]

    def _apply_card_container(self, slide, slide_node: IRNode):
        """为 grid/flex 子元素添加卡片背景（圆角矩形 + 白底 + 微阴影）"""
        from lxml import etree

        card_radius = slide_node.extra.get("card_radius", 3.0)
        card_color = slide_node.extra.get("card_color", "#FFFFFF")
        card_shadow = slide_node.extra.get("card_shadow", {
            "color": "#000000",
            "opacity": 0.08,
            "blur": 4,
            "offset_x": 0,
            "offset_y": 2,
        })

        for child in slide_node.children:
            pos = child.position
            if pos is None or pos.width_mm <= 0 or pos.height_mm <= 0:
                continue

            left, top, width, height = self._pos_to_emu(pos)
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
            )
            card.line.fill.background()
            card.fill.solid()
            card.fill.fore_color.rgb = self._hex_to_rgb(card_color)
            self._apply_shadow(card, card_shadow)

            # 调整圆角程度（通过 adj 值）
            sp_pr = getattr(card._element, 'spPr', None)
            if sp_pr is not None:
                a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
                for avLst in sp_pr.findall(f'{{{a_ns}}}avLst'):
                    for gd in avLst.findall(f'{{{a_ns}}}gd'):
                        if gd.get('name') == 'adj':
                            # adj 值越大圆角越小，16667 ≈ 小圆角
                            gd.set('fmla', f'val {int(card_radius * 5000)}')

    def _get_layout_index(self, name: str) -> int:
        """布局名称 → 幻灯片布局索引"""
        mapping = {
            "title": 0,
            "title_content": 1,
            "section": 2,
            "two_content": 3,
            "comparison": 4,
            "title_only": 5,
            "blank": 6,
            "caption": 7,
            "picture_caption": 8,
        }
        return mapping.get(name, 6)

    def _set_background(self, slide, bg_data: dict[str, Any]):
        """设置幻灯片背景

        支持：
          - 纯色: { color: "#RRGGBB" }
          - 线性渐变: { gradient: { type: linear, angle: 135, stops: [...] } }
          - 径向渐变: { gradient: { type: radial, stops: [...] } }
        """
        background = slide.background
        fill = background.fill
        fill.solid()

        gradient = bg_data.get("gradient")
        if gradient:
            self._apply_gradient_fill(fill, gradient)
        elif "color" in bg_data:
            fill.fore_color.rgb = self._hex_to_rgb(bg_data["color"])

    # ============================================================
    # 背景板渲染
    # ============================================================

    def _render_background_board(self, slide, board: dict[str, Any]):
        """Render the slide background board in fixed layer order.

        Layer order: background -> illustration -> scrim -> ornament.
        safe_area/content_zone is metadata for layout decisions and is not rendered.

        DSL 也支持 layers 键（扁平列表），优先级低于结构化键。
        """
        if not isinstance(board, dict):
            return
        has_structured = any(board.get(k) for k in ("background", "illustration", "scrim", "ornament"))
        if has_structured:
            for layer_key in ("background", "illustration", "scrim", "ornament"):
                for layer in self._layer_items(board.get(layer_key)):
                    self._render_background_layer(slide, layer, layer_key)
        else:
            # DSL 扁平 layers 模式
            for layer in self._layer_items(board.get("layers")):
                self._render_background_layer(slide, layer, "background")

    def _layer_items(self, value) -> list[dict[str, Any]]:
        if not value:
            return []
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
        return []

    def _render_background_layer(self, slide, layer: dict[str, Any], role: str):
        layer_type = str(layer.get("type", "")).lower()
        if not layer_type:
            if layer.get("src") or layer.get("source"):
                layer_type = "image"
            elif layer.get("gradient"):
                layer_type = "gradient"
            else:
                layer_type = "color"

        left, top, width, height = self._layer_position_to_emu(layer.get("position"))

        if layer_type in {"image", "texture"}:
            src = layer.get("src", layer.get("source"))
            if isinstance(src, str):
                file_path = Path(src.replace("file://", ""))
                if file_path.exists():
                    self._add_picture_with_fit(
                        slide, file_path, left, top, width, height,
                        fit=layer.get("fit", "cover"),
                    )
                else:
                    logger.warning("background_board image not found: %s", file_path)
            else:
                logger.warning("background_board %s layer has no source path", role)
            return

        shape_name = layer.get("shape", "rect")
        shape_type = self._get_shape_type(shape_name)
        shape = slide.shapes.add_shape(shape_type, left, top, width, height)
        shape.line.fill.background()

        gradient = layer.get("gradient")
        if layer_type in {"gradient", "linear_gradient", "radial_gradient"}:
            gradient = {
                "type": "radial" if layer_type == "radial_gradient" else "linear",
                "angle": layer.get("angle", 0),
                "stops": self._normalize_gradient_stops(layer.get("stops", [])),
            }

        style_fill = {}
        style = layer.get("style")
        if isinstance(style, dict) and isinstance(style.get("fill"), dict):
            style_fill = style["fill"]

        if gradient:
            self._apply_gradient_fill(shape.fill, gradient)
        else:
            shape.fill.solid()
            fill_color = layer.get("color", style_fill.get("color", "#000000"))
            shape.fill.fore_color.rgb = self._hex_to_rgb(fill_color)

        opacity = layer.get("opacity", style_fill.get("opacity"))
        if opacity is not None:
            self._apply_fill_alpha(shape, float(opacity))

        # 边框
        border = style_fill.get("border") if isinstance(style_fill.get("border"), dict) else None
        if not border:
            border = layer.get("border") if isinstance(layer.get("border"), dict) else None
        if border:
            from pptx.util import Pt as _Pt
            shape.line.color.rgb = self._hex_to_rgb(border.get("color", "#000000"))
            shape.line.width = _Pt(border.get("width", 1))

    def _normalize_gradient_stops(self, stops) -> list[str]:
        if not isinstance(stops, list) or not stops:
            return ["#000000", "#FFFFFF"]
        normalized = []
        for stop in stops:
            if isinstance(stop, str):
                normalized.append(stop)
            elif isinstance(stop, dict):
                normalized.append(stop.get("color", "#000000"))
        return normalized or ["#000000", "#FFFFFF"]

    def _layer_position_to_emu(self, raw_position) -> tuple:
        if not isinstance(raw_position, dict):
            return Mm(0), Mm(0), Mm(SLIDE_WIDTH_MM), Mm(SLIDE_HEIGHT_MM)
        pos = IRPosition(
            x_mm=self._parse_layer_length(raw_position.get("x"), SLIDE_WIDTH_MM),
            y_mm=self._parse_layer_length(raw_position.get("y"), SLIDE_HEIGHT_MM),
            width_mm=self._parse_layer_length(
                raw_position.get("width", raw_position.get("w", SLIDE_WIDTH_MM)),
                SLIDE_WIDTH_MM,
            ),
            height_mm=self._parse_layer_length(
                raw_position.get("height", raw_position.get("h", SLIDE_HEIGHT_MM)),
                SLIDE_HEIGHT_MM,
            ),
        )
        return self._pos_to_emu(pos)

    def _parse_layer_length(self, value, parent_size: float) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if text.endswith("mm"):
            return float(text[:-2])
        if text.endswith("cm"):
            return float(text[:-2]) * 10.0
        if text.endswith("px"):
            return float(text[:-2]) * 0.2646
        if text.endswith("%"):
            return parent_size * float(text[:-1]) / 100.0
        if text.endswith("in"):
            return float(text[:-2]) * 25.4
        try:
            return float(text)
        except ValueError:
            return 0.0

    # ============================================================
    # 元素级渲染
    # ============================================================

    def _render_element(self, slide, node: IRNode, doc: IRDocument):
        """渲染单个元素 — 按节点类型分派"""
        if node.node_type == NodeType.TEXT:
            self._render_text(slide, node, doc)
        elif node.node_type == NodeType.SHAPE:
            self._render_shape(slide, node, doc)
        elif node.node_type == NodeType.IMAGE:
            self._render_image(slide, node, doc)
        elif node.node_type == NodeType.TABLE:
            self._render_table(slide, node, doc)
        elif node.node_type == NodeType.CHART:
            self._render_chart(slide, node, doc)
        elif node.node_type == NodeType.GROUP:
            # GROUP 子元素位置相对于 group 原点，需要偏移到绝对坐标
            from dataclasses import replace
            group_pos = node.position
            for child in node.children:
                if child.position and group_pos:
                    child = replace(child, position=replace(
                        child.position,
                        x_mm=child.position.x_mm + group_pos.x_mm,
                        y_mm=child.position.y_mm + group_pos.y_mm,
                    ))
                self._render_element(slide, child, doc)
        else:
            self._render_placeholder(slide, node)

    def _render_text(self, slide, node: IRNode, doc: IRDocument):
        """渲染文本元素"""
        # 路径文字：沿曲线排列，使用独立字符放置
        if node.path_text:
            self._render_path_text(slide, node, doc)
            return

        pos = self._get_position(node)
        style = self._resolve_style(node, doc)

        # 根据 content_format 预处理内容
        content = node.content or ""
        rich_doc = None
        if node.content_format == "markdown" and content:
            from ...engine.text.markdown_parser import parse_markdown
            rich_doc = parse_markdown(content)
            content = rich_doc.plain_text
        elif node.content_format == "latex" and content:
            from ...engine.text.latex_parser import latex_to_unicode
            content = latex_to_unicode(content)
        elif node.content_format == "rich" and isinstance(node.content, (list, dict)):
            from ...engine.text.rich_text import parse_rich_text
            rich_doc = parse_rich_text(node.content)
            content = rich_doc.plain_text

        style = self._fit_text_style_to_box(content, pos, style, node)

        left, top, width, height = self._pos_to_emu(pos)
        if pos.is_center:
            actual_w_mm = pos.width_mm if pos.width_mm > 0 else width / MM_TO_EMU
            left = Mm((SLIDE_WIDTH_MM - actual_w_mm) / 2)

        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = not self._is_wrap_disabled(node)

        p = tf.paragraphs[0]

        # 有 rich_doc 时使用多 run 渲染，否则用纯文本
        if rich_doc and rich_doc.paragraphs:
            first_para = rich_doc.paragraphs[0]
            from ...engine.text.rich_text import to_pptx_runs
            run_params = to_pptx_runs(first_para)
            if run_params:
                # 清空默认 run，用解析后的 runs 替代
                p.clear()
                for rp in run_params:
                    run = p.add_run()
                    run.text = rp["text"]
                    _ensure_run_rpr(run)
                    if rp.get("bold"):
                        run.font.bold = True
                    if rp.get("italic"):
                        run.font.italic = True
                    if rp.get("underline"):
                        run.font.underline = True
                    if rp.get("color"):
                        run.font.color.rgb = self._hex_to_rgb(rp["color"])
                    if rp.get("font_size"):
                        from pptx.util import Pt
                        run.font.size = Pt(rp["font_size"])
                    if rp.get("font_family"):
                        run.font.name = rp["font_family"]

                # 后续段落（Markdown 的多段落）
                for para_data in rich_doc.paragraphs[1:]:
                    new_p = tf.add_paragraph()
                    for rp in to_pptx_runs(para_data):
                        run = new_p.add_run()
                        run.text = rp["text"]
                        _ensure_run_rpr(run)
                        if rp.get("bold"):
                            run.font.bold = True
                        if rp.get("italic"):
                            run.font.italic = True
                        if rp.get("color"):
                            run.font.color.rgb = self._hex_to_rgb(rp["color"])
                        if rp.get("font_size"):
                            from pptx.util import Pt
                            run.font.size = Pt(rp["font_size"])
                        if rp.get("font_family"):
                            run.font.name = rp["font_family"]
                # 使用第一个段落作为主段落引用
                p = tf.paragraphs[0]
            else:
                p.text = content
                for run in p.runs:
                    _ensure_run_rpr(run)
        else:
            p.text = content
            for run in p.runs:
                _ensure_run_rpr(run)

        self._apply_text_layout(tf, p, node)

        if style:
            self._apply_text_style(p, style)

        # 阴影
        if style and style.shadow:
            self._apply_shadow(txBox, style.shadow)

        # 应用动画
        if node.animations:
            apply_animations(slide, txBox, node.animations)

        # 应用文本变换 (WordArt)
        if style and style.text_effect:
            self._apply_text_warp(txBox, style.text_effect)

        # 文本描边
        if style and style.text_outline:
            self._apply_text_outline(txBox, style.text_outline)
        elif style and style.text_effect and ("stroke" in style.text_effect or "outline" in style.text_effect):
            outline = style.text_effect.get("stroke") or style.text_effect.get("outline")
            if outline:
                self._apply_text_outline(txBox, outline)

        # 倒影
        if style and style.text_reflection:
            self._apply_text_reflection(txBox, style.text_reflection)
        elif style and style.text_effect and "reflection" in style.text_effect:
            self._apply_text_reflection(txBox, style.text_effect["reflection"])

        # 斜面浮雕
        if style and style.text_bevel:
            self._apply_text_bevel(txBox, style.text_bevel)
        elif style and style.text_effect and "bevel" in style.text_effect:
            self._apply_text_bevel(txBox, style.text_effect["bevel"])

        # 字距/词距
        ls = style.letter_spacing if style else None
        ws = style.word_spacing if style else None
        if ls is not None or ws is not None:
            self._apply_text_spacing(p, ls, ws)

    def _render_path_text(self, slide, node: IRNode, doc: IRDocument):
        """渲染路径文字 — 将文本沿曲线排列

        标准预设路径（arc/wave/circle 等）使用 PPTX 原生 presetTextWarp（单 shape），
        custom SVG 路径使用逐字符旋转文本框。
        """
        from ...engine.text.path_text import (
            PathTextConfig, to_pptx_placements, PATH_TYPE_TO_PPTX_PRESET,
        )

        content = node.content or ""
        if not content or not node.path_text:
            return

        style = self._resolve_style(node, doc)
        pos = self._get_position(node)

        pt = node.path_text
        path_type = pt.path_type

        # 标准预设路径 → presetTextWarp（单 shape，原生 WordArt 效果）
        if path_type in PATH_TYPE_TO_PPTX_PRESET:
            self._render_path_text_preset(slide, node, doc, pt, content, style, pos)
            return

        # custom SVG 路径 → 逐字符旋转文本框
        config = PathTextConfig(
            path_type=pt.path_type,
            radius=pt.radius,
            start_angle=pt.start_angle,
            end_angle=pt.end_angle,
            amplitude=pt.amplitude,
            wavelength=pt.wavelength,
            custom_path=pt.custom_path,
            char_spacing=pt.char_spacing,
            bend=pt.bend,
        )

        font_size = self._style_val(style, "font_size") or 14
        placements = to_pptx_placements(content, config, font_size)
        origin_x, origin_y = pos.x_mm, pos.y_mm

        for cp in placements:
            char_left = Mm(origin_x + cp.x - cp.width / 2)
            char_top = Mm(origin_y + cp.y - font_size * 0.35 / 2)
            char_w = Mm(max(cp.width, font_size * 0.35))
            char_h = Mm(font_size * 0.5)

            txBox = slide.shapes.add_textbox(char_left, char_top, char_w, char_h)
            tf = txBox.text_frame
            tf.word_wrap = False
            p = tf.paragraphs[0]
            p.text = cp.char
            if style:
                self._apply_text_style(p, style)
            if cp.rotation != 0:
                txBox.rotation = cp.rotation

    def _render_path_text_preset(
        self, slide, node: IRNode, doc: IRDocument,
        pt, content: str, style: IRStyle, pos: IRPosition,
    ):
        """使用 presetTextWarp 渲染标准路径文字（单 shape，原生 WordArt）"""
        from ...engine.text.path_text import PATH_TYPE_TO_PPTX_PRESET

        left, top, width, height = self._pos_to_emu(pos)
        if pos.is_center:
            actual_w_mm = pos.width_mm if pos.width_mm > 0 else width / MM_TO_EMU
            left = Mm((SLIDE_WIDTH_MM - actual_w_mm) / 2)

        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = content
        if style:
            self._apply_text_style(p, style)

        # 应用 presetTextWarp（原生 WordArt 曲线效果）
        self._apply_text_warp(txBox, {
            "transform": pt.path_type,
            "bend": pt.bend,
        })

    def _render_shape(self, slide, node: IRNode, doc: IRDocument):
        """渲染形状元素

        支持的形状类型：rectangle, rounded_rectangle, circle, oval,
        triangle, diamond, arrow, star, hexagon, pentagon
        """
        pos = self._get_position(node)
        style = self._resolve_style(node, doc)

        left, top, width, height = self._pos_to_emu(pos)
        shape_type = node.extra.get("shape_type", "rectangle")
        if shape_type == "line":
            points = node.extra.get("line_points")
            if isinstance(points, dict):
                shape = slide.shapes.add_connector(
                    MSO_CONNECTOR.STRAIGHT,
                    Mm(float(points.get("x1", pos.x_mm))),
                    Mm(float(points.get("y1", pos.y_mm))),
                    Mm(float(points.get("x2", pos.x_mm + pos.width_mm))),
                    Mm(float(points.get("y2", pos.y_mm + pos.height_mm))),
                )
                self._apply_shape_border(shape, node)
                return
            shape = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                left,
                top,
                left + width,
                top + height,
            )
            self._apply_shape_border(shape, node)
            return

        if shape_type == "freeform":
            self._render_freeform_shape(slide, node, pos)
            return

        mso_shape = self._get_shape_type(shape_type)

        shape = slide.shapes.add_shape(mso_shape, left, top, width, height)

        # 填充
        self._apply_shape_fill(shape, style, node)

        # 边框
        self._apply_shape_border(shape, node)

        # 形状内文本
        if node.content:
            tf = shape.text_frame
            tf.word_wrap = not self._is_wrap_disabled(node)
            p = tf.paragraphs[0]
            p.text = node.content
            # OOXML 要求每个 a:r 必须有 a:rPr 子元素
            for run in p.runs:
                _ensure_run_rpr(run)
            self._apply_text_layout(tf, p, node)
            if style:
                fitted = self._fit_text_style_to_box(node.content, pos, style, node)
                self._apply_text_style(p, fitted)

        # 文本描边
        if style and style.text_outline:
            self._apply_text_outline(shape, style.text_outline)
        elif style and style.text_effect and ("stroke" in style.text_effect or "outline" in style.text_effect):
            outline = style.text_effect.get("stroke") or style.text_effect.get("outline")
            if outline:
                self._apply_text_outline(shape, outline)

        # 倒影
        if style and style.text_reflection:
            self._apply_text_reflection(shape, style.text_reflection)
        elif style and style.text_effect and "reflection" in style.text_effect:
            self._apply_text_reflection(shape, style.text_effect["reflection"])

        # 斜面浮雕
        if style and style.text_bevel:
            self._apply_text_bevel(shape, style.text_bevel)
        elif style and style.text_effect and "bevel" in style.text_effect:
            self._apply_text_bevel(shape, style.text_effect["bevel"])

        # 应用动画
        if node.animations:
            apply_animations(slide, shape, node.animations)

    def _render_freeform_shape(self, slide, node: IRNode, pos: IRPosition):
        """渲染自由贝塞尔形状 — 通过 lxml 直接构造 <a:custGeom>"""
        from lxml import etree

        freeform_path = node.extra.get("freeform_path", "")
        if not freeform_path:
            logger.warning("freeform shape missing freeform_path, skipping")
            return

        nodes = parse_svg_path_struct(freeform_path)
        if not nodes:
            return

        style = node.style if hasattr(node, "style") and node.style else None

        left, top, width, height = self._pos_to_emu(pos)

        # OOXML 命名空间
        nsmap = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        }

        # 路径坐标归一化范围（使用 21600000 EMU 标准路径尺寸）
        path_w = 21600000
        path_h = 21600000

        # 命名空间前缀常量
        a = "{" + nsmap["a"] + "}"
        p = "{" + nsmap["p"] + "}"

        # 构建 spPr
        spPr = etree.Element(f"{p}spPr")

        # xfrm
        xfrm = etree.SubElement(spPr, f"{a}xfrm")
        off = etree.SubElement(xfrm, f"{a}off")
        off.set("x", str(left))
        off.set("y", str(top))
        ext = etree.SubElement(xfrm, f"{a}ext")
        ext.set("cx", str(width))
        ext.set("cy", str(height))

        # custGeom
        custGeom = etree.SubElement(spPr, f"{a}custGeom")
        custGeom.set("prst", "")
        etree.SubElement(custGeom, f"{a}avLst")
        etree.SubElement(custGeom, f"{a}gdLst")
        etree.SubElement(custGeom, f"{a}ahLst")
        etree.SubElement(custGeom, f"{a}cxnLst")
        rect = etree.SubElement(custGeom, f"{a}rect")
        rect.set("l", "0")
        rect.set("t", "0")
        rect.set("r", "w")
        rect.set("b", "h")

        # pathLst > path
        pathLst = etree.SubElement(custGeom, f"{a}pathLst")
        path_el = etree.SubElement(pathLst, f"{a}path")
        path_el.set("w", str(path_w))
        path_el.set("h", str(path_h))

        # 将百分比坐标（0-100）映射到 path 坐标（0-path_w/h）
        def scale_x(v: float) -> int:
            return int(v / 100.0 * path_w)

        def scale_y(v: float) -> int:
            return int(v / 100.0 * path_h)

        for nd in nodes:
            if nd["type"] == "move":
                moveTo = etree.SubElement(path_el, f"{a}moveTo")
                pt = etree.SubElement(moveTo, f"{a}pt")
                pt.set("x", str(scale_x(nd["points"][0][0])))
                pt.set("y", str(scale_y(nd["points"][0][1])))
            elif nd["type"] == "line":
                lnTo = etree.SubElement(path_el, f"{a}lnTo")
                pt = etree.SubElement(lnTo, f"{a}pt")
                pt.set("x", str(scale_x(nd["points"][0][0])))
                pt.set("y", str(scale_y(nd["points"][0][1])))
            elif nd["type"] == "cubic":
                cubicBezTo = etree.SubElement(path_el, f"{a}cubicBezTo")
                for pp in nd["points"]:
                    pt = etree.SubElement(cubicBezTo, f"{a}pt")
                    pt.set("x", str(scale_x(pp[0])))
                    pt.set("y", str(scale_y(pp[1])))
            elif nd["type"] == "quad":
                quad_pts = nd["points"]
                prev_end = None
                for prev in reversed(nodes[:nodes.index(nd)]):
                    if prev["type"] == "move":
                        prev_end = prev["points"][0]
                        break
                    elif prev["type"] == "line":
                        prev_end = prev["points"][0]
                        break
                    elif prev["type"] == "cubic":
                        prev_end = prev["points"][2]
                        break
                    elif prev["type"] == "quad":
                        prev_end = prev["points"][1]
                        break
                if prev_end is None:
                    prev_end = (0.0, 0.0)
                qx, qy = quad_pts[0]
                ex, ey = quad_pts[1]
                cp1x = prev_end[0] + 2.0 / 3.0 * (qx - prev_end[0])
                cp1y = prev_end[1] + 2.0 / 3.0 * (qy - prev_end[1])
                cp2x = ex + 2.0 / 3.0 * (qx - ex)
                cp2y = ey + 2.0 / 3.0 * (qy - ey)
                cubicBezTo = etree.SubElement(path_el, f"{a}cubicBezTo")
                for px, py in [(cp1x, cp1y), (cp2x, cp2y), (ex, ey)]:
                    pt = etree.SubElement(cubicBezTo, f"{a}pt")
                    pt.set("x", str(scale_x(px)))
                    pt.set("y", str(scale_y(py)))
            elif nd["type"] == "close":
                etree.SubElement(path_el, f"{a}close")

        # 构建完整的 p:sp 元素
        sp = etree.Element(f"{p}sp")
        nvSpPr = etree.SubElement(sp, f"{p}nvSpPr")
        cNvPr = etree.SubElement(nvSpPr, f"{p}cNvPr")
        cNvPr.set("id", "0")
        cNvPr.set("name", "FreeformShape")
        etree.SubElement(nvSpPr, f"{p}cNvSpPr")
        etree.SubElement(nvSpPr, f"{p}nvPr")

        sp.append(spPr)

        # 空 txBody
        txBody = etree.SubElement(sp, f"{p}txBody")
        etree.SubElement(txBody, f"{a}bodyPr")
        etree.SubElement(txBody, f"{a}lstStyle")
        p_el = etree.SubElement(txBody, f"{a}p")
        etree.SubElement(p_el, f"{a}endParaRPr")

        # 注入到 slide 的 spTree
        spTree = slide.shapes._spTree
        spTree.append(sp)

        # 直接通过 lxml 应用填充样式到 spPr（避免 slide.shapes[-1] 的兼容问题）
        if style and style.fill_color:
            from pptx.oxml.ns import qn
            solidFill = etree.SubElement(spPr, qn("a:solidFill"))
            srgbClr = etree.SubElement(solidFill, qn("a:srgbClr"))
            srgbClr.set("val", style.fill_color.lstrip("#"))
        elif style and style.fill_gradient:
            gradFill = etree.SubElement(spPr, qn("a:gradFill"))
            gsLst = etree.SubElement(gradFill, qn("a:gsLst"))
            stops = style.fill_gradient.get("stops", ["#000000", "#FFFFFF"])
            for i, hex_color in enumerate(stops):
                pos_val = str(int(i / max(len(stops) - 1, 1) * 100000))
                gs = etree.SubElement(gsLst, qn("a:gs"))
                gs.set("pos", pos_val)
                clr = etree.SubElement(gs, qn("a:srgbClr"))
                clr.set("val", hex_color.lstrip("#"))
            angle = style.fill_gradient.get("angle", 0)
            lin = etree.SubElement(gradFill, qn("a:lin"))
            lin.set("ang", str(int(angle * 60000)))
            lin.set("scaled", "1")

    def _render_image(self, slide, node: IRNode, doc: IRDocument):
        """渲染图片元素

        支持：
          - 本地文件: source="file://path" 或 source="path"
          - MCP/AI 资源: source={mcp__unsplash, query: "..."} → 占位符
        """
        pos = self._get_position(node)
        left, top, width, height = self._pos_to_emu(pos)

        source = node.source
        if isinstance(source, str):
            # 尝试作为本地文件
            file_path = Path(source.replace("file://", ""))
            if file_path.exists():
                picture = self._add_picture_with_fit(
                    slide, file_path, left, top, width, height,
                    fit=node.extra.get("fit", "cover"),
                )
                # 应用图片滤镜（支持单个或多个叠加）
                filter_spec = node.extra.get("filter")
                if filter_spec and picture:
                    self._apply_image_filter(picture, filter_spec)
                # 应用 IRStyle 中的 fill_opacity
                style = self._resolve_style(node, doc)
                if style and style.fill_opacity is not None and style.fill_opacity < 1.0 and picture:
                    self._apply_image_opacity(picture._element.find(
                        f'.//{{{{http://schemas.openxmlformats.org/drawingml/2006/main}}}}blip'
                    ), {"value": int(style.fill_opacity * 100)})
                return

        # 降级：占位符
        self._render_placeholder(slide, node, left, top, width, height)

    def _render_table(self, slide, node: IRNode, doc: IRDocument):
        """渲染表格元素

        数据来源（优先级从高到低）：
          - data_ref: 引用 doc.data 中的键（二维数组）
          - extra.data: 内联二维数组
          - extra.rows/extra.cols: 行列数（空表格）
        """
        pos = self._get_position(node)
        left, top, width, height = self._pos_to_emu(pos)

        # 解析数据：data_ref 优先于 extra.data
        resolved_data: list | None = None
        if node.data_ref and node.data_ref in doc.data:
            ref_val = doc.data[node.data_ref]
            if isinstance(ref_val, list):
                resolved_data = ref_val
        if resolved_data is None:
            inline_data = node.extra.get("data")
            if isinstance(inline_data, list):
                resolved_data = inline_data

        # 推断行列数
        if resolved_data:
            rows = len(resolved_data)
            cols = max((len(r) for r in resolved_data if isinstance(r, list)), default=1)
        else:
            rows = node.extra.get("rows", 3)
            cols = node.extra.get("cols", 3)

        table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
        table = table_shape.table

        # 填充数据
        style = self._resolve_style(node, doc)
        inline_data = resolved_data
        if isinstance(inline_data, list):
            for r, row_data in enumerate(inline_data[:rows]):
                if isinstance(row_data, list):
                    for c, cell_val in enumerate(row_data[:cols]):
                        cell = table.cell(r, c)
                        cell.text = str(cell_val)
                        # 应用 IRStyle 到单元格文本
                        if style:
                            for paragraph in cell.text_frame.paragraphs:
                                self._apply_text_style(paragraph, style)
                        # 首行加粗（表头）
                        if r == 0:
                            for paragraph in cell.text_frame.paragraphs:
                                for run in paragraph.runs:
                                    run.font.bold = True

        # 表格样式（交替行颜色）
        self._apply_table_style(table, rows, cols)

    def _render_chart(self, slide, node: IRNode, doc: IRDocument):
        """渲染图表元素

        DSL 示例：
          - type: chart
            chart_type: bar
            data_ref: revenue
            position: { x: 20mm, y: 40mm, width: 200mm, height: 100mm }
            extra:
              categories: ["Q1", "Q2", "Q3", "Q4"]
              series:
                - name: "营收"
                  values: [100, 120, 150, 180]
                - name: "利润"
                  values: [30, 40, 50, 60]

        外部引擎示例（extra.engine 指定渲染器）：
          - type: chart
            chart_type: bar
            position: { x: 20mm, y: 40mm, width: 200mm, height: 100mm }
            extra:
              engine: matplotlib        # matplotlib / plotly / vega-lite / ggplot2 / pgfplots
              categories: ["Q1", "Q2", "Q3", "Q4"]
              series:
                - name: "营收"
                  values: [100, 120, 150, 180]
        """
        # 外部图表引擎：渲染为 PNG 后嵌入
        engine_name = node.extra.get("engine")
        if engine_name and engine_name != "native":
            self._render_engine_chart(slide, node, doc)
            return

        pos = self._get_position(node)
        left, top, width, height = self._pos_to_emu(pos)

        chart_type_str = node.chart_type or node.extra.get("chart_type", "bar")
        xl_chart_type = CHART_TYPE_MAP.get(chart_type_str, XL_CHART_TYPE.BAR_CLUSTERED)

        # 构建图表数据
        chart_data = self._build_chart_data(node, doc)

        # 添加图表
        chart_frame = slide.shapes.add_chart(
            xl_chart_type, left, top, width, height, chart_data
        )
        chart = chart_frame.chart

        # 图表标题
        title = node.extra.get("title")
        if title:
            chart.has_title = True
            chart.chart_title.text_frame.paragraphs[0].text = title

        # 图例
        show_legend = node.extra.get("legend", True)
        chart.has_legend = show_legend
        if show_legend:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False

        # 应用主题色到系列
        self._apply_chart_colors(chart, node)

    def _render_engine_chart(self, slide, node: IRNode, doc: IRDocument):
        """通过外部图表引擎渲染为 PNG 后以图片形式嵌入

        支持引擎：matplotlib / plotly / vega-lite / ggplot2 / pgfplots
        """
        import logging
        import tempfile
        from pathlib import Path as _Path
        from ...engine.chart import render_chart_image

        log = logging.getLogger(__name__)

        # 收集数据
        data: dict = {}
        if node.data_ref and doc is not None and node.data_ref in doc.data:
            ref_val = doc.data[node.data_ref]
            if isinstance(ref_val, dict):
                data = ref_val
        if not data:
            data = {
                "categories": node.extra.get("categories", []),
                "series": node.extra.get("series", []),
            }
            if "data" in node.extra:
                data["raw_data"] = node.extra["data"]

        chart_type = node.chart_type or node.extra.get("chart_type", "bar")
        pos = self._get_position(node)
        # 估算像素尺寸：1mm ≈ 7.56px (192 DPI)，保证图表高清
        w_px = int(pos.width_mm * 7.56)
        h_px = int(pos.height_mm * 7.56)

        # 渲染到临时目录，再嵌入 PPTX
        out_dir = _Path(tempfile.mkdtemp(prefix="pptx_chart_"))
        try:
            png_path = render_chart_image(
                chart_type=chart_type,
                data=data,
                extra=dict(node.extra),
                output_dir=out_dir,
                width_px=max(w_px, 1920),
                height_px=max(h_px, 1080),
                dpi=node.extra.get("dpi", 150),
            )
            # 以图片形式嵌入
            left, top, width, height = self._pos_to_emu(pos)
            if png_path.exists():
                slide.shapes.add_picture(str(png_path), left, top, width, height)
            else:
                log.warning(f"图表引擎未生成文件: {png_path}")
                self._render_placeholder(slide, node, left, top, width, height)
        except Exception as e:
            log.warning(f"外部图表引擎渲染失败: {e}")
            # 降级为原生 python-pptx 图表
            try:
                chart_type_str = chart_type
                xl_chart_type = CHART_TYPE_MAP.get(chart_type_str, XL_CHART_TYPE.BAR_CLUSTERED)
                chart_data = self._build_chart_data(node, doc)
                left_emu, top_emu, w_emu, h_emu = self._pos_to_emu(pos)
                slide.shapes.add_chart(xl_chart_type, left_emu, top_emu, w_emu, h_emu, chart_data)
            except Exception:
                left, top, width, height = self._pos_to_emu(pos)
                self._render_placeholder(slide, node, left, top, width, height)

    def _build_chart_data(self, node: IRNode, doc: IRDocument | None = None) -> CategoryChartData:
        """从 IRNode 构建 CategoryChartData

        数据来源（优先级从高到低）：
          - data_ref: 引用 doc.data 中的键，格式：
              { categories: [...], series: [{name, values}, ...] }
          - extra.categories / extra.series: 内联数据
        """
        categories: list = []
        series_list: list = []

        # 优先从 data_ref 读取
        if node.data_ref and doc is not None and node.data_ref in doc.data:
            ref_val = doc.data[node.data_ref]
            if isinstance(ref_val, dict):
                categories = ref_val.get("categories", [])
                series_list = ref_val.get("series", [])
            else:
                logger.warning(
                    "[Chart] data_ref '%s' 返回 %s，期望 dict(categories, series)",
                    node.data_ref, type(ref_val).__name__,
                )

        # 回退到 extra 内联数据
        if not categories:
            categories = node.extra.get("categories", [])
        if not series_list:
            series_list = node.extra.get("series", [])

        chart_data = CategoryChartData()
        chart_data.categories = categories

        for series in series_list:
            name = series.get("name", "")
            values = series.get("values", [])
            chart_data.add_series(name, values)

        return chart_data

    def _apply_chart_colors(self, chart, node: IRNode):
        """为图表系列应用颜色

        从 node.extra.colors 读取颜色列表，或使用默认主题色。
        """
        colors = node.extra.get("colors", [
            "#2563EB", "#16A34A", "#EA580C", "#9333EA",
            "#E11D48", "#0891B2", "#CA8A04", "#4F46E5",
        ])
        for i, series in enumerate(chart.series):
            color_hex = colors[i % len(colors)]
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = self._hex_to_rgb(color_hex)

    def _render_placeholder(self, slide, node: IRNode, left=None, top=None, width=None, height=None):
        """渲染占位符（不支持的元素类型或缺失资源）"""
        if left is None:
            pos = self._get_position(node)
            left, top, width, height = self._pos_to_emu(pos)

        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, left, top, width, height
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(0xE0, 0xE0, 0xE0)
        shape.line.color.rgb = RGBColor(0x99, 0x99, 0x99)
        shape.line.dash_style = 2  # 虚线

        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"[{node.node_type.value}]"
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # ============================================================
    # 填充/边框/样式辅助方法
    # ============================================================

    def _apply_shape_fill(self, shape, style: IRStyle | None, node: IRNode):
        """应用形状填充（纯色 / 渐变 / 透明度）"""
        if style and style.fill_gradient:
            shape.fill.gradient()
            self._apply_gradient_fill(shape.fill, style.fill_gradient)
        elif style and style.fill_color:
            shape.fill.solid()
            shape.fill.fore_color.rgb = self._hex_to_rgb(style.fill_color)
            # 透明度
            if style.fill_opacity is not None and style.fill_opacity < 1.0:
                self._apply_fill_alpha(shape, style.fill_opacity)
        else:
            shape.fill.background()

        # 阴影
        if style and style.shadow:
            self._apply_shadow(shape, style.shadow)
        if style and style.text_effect and style.text_effect.get("glow"):
            self._apply_glow(shape, style.text_effect["glow"])

    def _apply_gradient_fill(self, fill, gradient: dict[str, Any]):
        """应用渐变填充

        支持 linear 和 radial 类型。
        python-pptx 的 gradient API 通过 gradient_stops 操作。
        当停止点 >2 时回退到 lxml 直接注入 gsLst。
        """
        from lxml import etree

        fill.gradient()
        stops = gradient.get("stops", ["#000000", "#FFFFFF"])
        angle = gradient.get("angle", 0)

        if len(stops) <= 2:
            # python-pptx API 路径（原生 2 停靠点）
            for i, color_hex in enumerate(stops):
                position = i / max(len(stops) - 1, 1)
                if i < len(fill.gradient_stops):
                    fill.gradient_stops[i].color.rgb = self._hex_to_rgb(color_hex)
                    fill.gradient_stops[i].position = position
        else:
            # lxml 直接注入：支持任意数量停止点
            a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
            grad_fill = getattr(fill._fill, '_gradFill', None)
            if grad_fill is None:
                return
            gs_lst = grad_fill.find(f'{{{a_ns}}}gsLst')
            if gs_lst is None:
                gs_lst = etree.SubElement(grad_fill, f'{{{a_ns}}}gsLst')
            else:
                for old in list(gs_lst):
                    gs_lst.remove(old)
            for i, color_hex in enumerate(stops):
                position = int(i / max(len(stops) - 1, 1) * 100000)
                gs = etree.SubElement(gs_lst, f'{{{a_ns}}}gs')
                gs.set('pos', str(position))
                srgb = etree.SubElement(gs, f'{{{a_ns}}}srgbClr')
                srgb.set('val', str(color_hex).lstrip('#')[:6])

        # 角度（linear 时有效）
        if gradient.get("type") == "linear":
            # python-pptx 使用 angle 属性（0-360 度）
            try:
                fill.gradient_angle = angle
            except AttributeError:
                pass  # 某些版本不支持

    def _apply_fill_alpha(self, shape, opacity: float):
        """向 solidFill 注入透明度。opacity=1 不透明，0 全透明。"""
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        sp_pr = getattr(shape._element, 'spPr', None)
        if sp_pr is None:
            return
        solid_fill = sp_pr.find(f'{{{a_ns}}}solidFill')
        if solid_fill is None:
            return
        color = solid_fill.find(f'{{{a_ns}}}srgbClr')
        if color is None:
            color = solid_fill.find(f'{{{a_ns}}}schemeClr')
        if color is None:
            return
        for old in color.findall(f'{{{a_ns}}}alpha'):
            color.remove(old)
        alpha = etree.SubElement(color, f'{{{a_ns}}}alpha')
        alpha.set('val', str(int(max(0.0, min(1.0, opacity)) * 100000)))

    def _apply_glow(self, shape, glow: dict[str, Any]):
        """通过 DrawingML 注入发光效果。"""
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        sp_pr = getattr(shape._element, 'spPr', None)
        if sp_pr is None:
            return
        effect_lst = sp_pr.find(f'{{{a_ns}}}effectLst')
        if effect_lst is None:
            effect_lst = etree.SubElement(sp_pr, f'{{{a_ns}}}effectLst')
        for old in effect_lst.findall(f'{{{a_ns}}}glow'):
            effect_lst.remove(old)

        glow_elem = etree.SubElement(effect_lst, f'{{{a_ns}}}glow')
        glow_elem.set('rad', str(int(float(glow.get("radius", 6)) * 12700)))
        color_hex = str(glow.get("color", "#2563EB")).lstrip("#")
        # OOXML srgbClr val 必须是 6 位 hex，3 位需展开补零
        if len(color_hex) == 3:
            color_hex = color_hex[0]*2 + color_hex[1]*2 + color_hex[2]*2
        srgb = etree.SubElement(glow_elem, f'{{{a_ns}}}srgbClr')
        srgb.set('val', color_hex[:6] if len(color_hex) >= 6 else "2563EB")
        alpha = etree.SubElement(srgb, f'{{{a_ns}}}alpha')
        alpha.set('val', str(int(float(glow.get("opacity", 0.35)) * 100000)))

    def _apply_shadow(self, shape, shadow: dict[str, Any]):
        """通过 DrawingML XML 注入阴影效果

        shadow 字典格式：
          { color: "#000000", opacity: 0.5, blur: 4, offset_x: 3, offset_y: 3, angle: 45 }

        python-pptx 未暴露阴影 API，直接操作底层 XML。
        spPr 通过 shape._element.spPr 属性访问（python-pptx 内部属性），
        避免因命名空间差异（p: vs a:）导致 find() 返回 None。
        """
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        # 优先使用 python-pptx 内部属性直接获取 spPr，
        # 回退到 XPath 搜索（兼容不同 shape 类型）
        sp_pr = getattr(shape._element, 'spPr', None)
        if sp_pr is None:
            # 在整个元素树中搜索（p:spPr 和 xdr:spPr 均可匹配）
            for ns in (
                'http://schemas.openxmlformats.org/presentationml/2006/main',
                'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
            ):
                sp_pr = shape._element.find(f'.//{{{ns}}}spPr')
                if sp_pr is not None:
                    break
        if sp_pr is None:
            return

        # 获取或创建 effectLst
        effect_lst = sp_pr.find(f'{{{a_ns}}}effectLst')
        if effect_lst is None:
            effect_lst = etree.SubElement(sp_pr, f'{{{a_ns}}}effectLst')

        # 移除已有阴影（避免重复）
        for old in effect_lst.findall(f'{{{a_ns}}}outerShdw'):
            effect_lst.remove(old)

        # 参数解析
        color_hex = shadow.get("color", "#000000").lstrip("#")
        opacity = shadow.get("opacity", 0.5)
        blur_pt = shadow.get("blur", 4)
        offset_x = shadow.get("offset_x", 3)
        offset_y = shadow.get("offset_y", 3)
        angle_deg = shadow.get("angle", 45)

        # EMU 换算：1pt = 12700 EMU
        blur_emu = int(blur_pt * 12700)
        dist_emu = int((offset_x ** 2 + offset_y ** 2) ** 0.5 * 12700)
        dir_60k = int(angle_deg * 60000)  # 角度单位：60000分之一度
        alpha_pct = int(opacity * 100000)  # 透明度单位：100000分之一

        # 构建 outerShdw 元素
        outer_shdw = etree.SubElement(effect_lst, f'{{{a_ns}}}outerShdw')
        outer_shdw.set('blurRad', str(blur_emu))
        outer_shdw.set('dist', str(dist_emu))
        outer_shdw.set('dir', str(dir_60k))
        outer_shdw.set('algn', 'tl')
        outer_shdw.set('rotWithShape', '0')

        # 颜色节点
        srgb_clr = etree.SubElement(outer_shdw, f'{{{a_ns}}}srgbClr')
        srgb_clr.set('val', color_hex if len(color_hex) == 6 else '000000')
        alpha = etree.SubElement(srgb_clr, f'{{{a_ns}}}alpha')
        alpha.set('val', str(alpha_pct))

    def _apply_shape_border(self, shape, node: IRNode):
        """应用形状边框"""
        outline = node.extra.get("outline")
        if outline:
            shape.line.color.rgb = self._hex_to_rgb(outline.get("color", "#000000"))
            shape.line.width = Pt(outline.get("width", 1))
            # 虚线样式
            dash = outline.get("dash")
            if dash == "solid":
                shape.line.dash_style = 1
            elif dash == "dashed":
                shape.line.dash_style = 4
            elif dash == "dotted":
                shape.line.dash_style = 2
        else:
            shape.line.fill.background()

    def _add_picture_with_fit(self, slide, file_path: Path, left, top, width, height, fit: str = "cover"):
        """添加图片并按比例适配目标框。

        fit:
          - cover: 填满目标框，超出部分用 PPT 裁切参数隐藏
          - contain: 保持完整图片，居中留白
          - stretch: 直接拉伸到目标框
        """
        fit = (fit or "cover").lower()
        if fit == "stretch":
            return slide.shapes.add_picture(str(file_path), left, top, width, height)

        try:
            with Image.open(file_path) as img:
                img_w, img_h = img.size
        except Exception:
            logger.debug("PIL 打开图片失败，直接添加: %s", file_path, exc_info=True)
            return slide.shapes.add_picture(str(file_path), left, top, width, height)

        if img_w <= 0 or img_h <= 0:
            return slide.shapes.add_picture(str(file_path), left, top, width, height)

        box_w = int(width)
        box_h = int(height)
        image_ratio = img_w / img_h
        box_ratio = box_w / box_h if box_h else image_ratio

        if fit == "contain":
            if image_ratio >= box_ratio:
                new_w = box_w
                new_h = int(box_w / image_ratio)
            else:
                new_h = box_h
                new_w = int(box_h * image_ratio)
            pic_left = left + int((box_w - new_w) / 2)
            pic_top = top + int((box_h - new_h) / 2)
            return slide.shapes.add_picture(str(file_path), pic_left, pic_top, new_w, new_h)

        picture = slide.shapes.add_picture(str(file_path), left, top, width, height)
        if image_ratio > box_ratio:
            visible_ratio = box_ratio / image_ratio
            crop = max(0.0, min(0.5, (1.0 - visible_ratio) / 2))
            picture.crop_left = crop
            picture.crop_right = crop
        elif image_ratio < box_ratio:
            visible_ratio = image_ratio / box_ratio
            crop = max(0.0, min(0.5, (1.0 - visible_ratio) / 2))
            picture.crop_top = crop
            picture.crop_bottom = crop
        return picture

    def _apply_table_style(self, table, rows: int, cols: int):
        """应用表格样式（交替行颜色）"""
        for r in range(rows):
            for c in range(cols):
                cell = table.cell(r, c)
                if r == 0:
                    # 表头：深色背景
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x3B)
                    for p in cell.text_frame.paragraphs:
                        for run in p.runs:
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                            run.font.size = Pt(11)
                elif r % 2 == 0:
                    # 偶数行：浅灰背景
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(0xF1, 0xF5, 0xF9)
                else:
                    # 奇数行：白色
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # ============================================================
    # 位置/样式工具方法
    # ============================================================

    def _get_position(self, node: IRNode) -> IRPosition:
        """获取节点位置，无位置时返回默认"""
        return node.position or IRPosition()

    def _pos_to_emu(self, pos: IRPosition) -> tuple:
        """将 IRPosition (mm) 转换为 EMU 元组 (left, top, width, height)

        使用浮点精度而非 int() 截断，避免坐标偏移。
        超出幻灯片边界的元素会被裁剪到边界内。
        """
        x_mm = pos.x_mm
        y_mm = pos.y_mm
        w_mm = pos.width_mm if pos.width_mm > 0 else (SLIDE_WIDTH_MM - x_mm)
        h_mm = pos.height_mm if pos.height_mm > 0 else 7.5  # 默认 7.5mm

        # 负坐标裁剪：元素左/上边缘超出幻灯片
        if x_mm < 0:
            w_mm = max(0, w_mm + x_mm)
            x_mm = 0.0
        if y_mm < 0:
            h_mm = max(0, h_mm + y_mm)
            y_mm = 0.0

        # 右/下越界裁剪
        if y_mm + h_mm > SLIDE_HEIGHT_MM:
            original_h = h_mm
            h_mm = max(0, SLIDE_HEIGHT_MM - y_mm)
            if h_mm < original_h:
                logger.debug(
                    "[CLIP] 元素高度被裁剪: y=%.1fmm, h: %.1fmm -> %.1fmm",
                    y_mm, original_h, h_mm,
                )

        if x_mm + w_mm > SLIDE_WIDTH_MM:
            original_w = w_mm
            w_mm = max(0, SLIDE_WIDTH_MM - x_mm)
            if w_mm < original_w:
                logger.debug(
                    "[CLIP] 元素宽度被裁剪: x=%.1fmm, w=%.1fmm -> %.1fmm",
                    x_mm, original_w, w_mm,
                )

        # 元素完全在幻灯片外
        w_mm = max(0, w_mm)
        h_mm = max(0, h_mm)

        left = Mm(x_mm)
        top = Mm(y_mm)
        width = Mm(w_mm)
        height = Mm(h_mm)
        return left, top, width, height

    # 内置主题色表（对应 Office 默认主题 "Office Theme"）
    _THEME_COLORS: dict[str, str] = {
        "dk1":     "#000000",  # 深色 1
        "lt1":     "#FFFFFF",  # 浅色 1
        "dk2":     "#1F3864",  # 深色 2
        "lt2":     "#E7E6E6",  # 浅色 2
        "accent1": "#4472C4",
        "accent2": "#ED7D31",
        "accent3": "#A9D18E",
        "accent4": "#FFC000",
        "accent5": "#5B9BD5",
        "accent6": "#70AD47",
        "hlink":   "#0563C1",  # 超链接
        "folHlink":"#954F72",  # 已访问超链接
        # 语义别名
        "primary":   "#4472C4",
        "secondary": "#ED7D31",
        "success":   "#70AD47",
        "warning":   "#FFC000",
        "danger":    "#FF0000",
        "info":      "#5B9BD5",
        "light":     "#E7E6E6",
        "dark":      "#1F3864",
    }

    def _resolve_style(self, node: IRNode, doc: IRDocument) -> IRStyle | None:
        """解析节点样式

        编译器已做级联，这里直接使用 node.style。
        回退到 doc.styles 的场景：节点仅设了 style_ref 但未级联（旧代码兼容）。
        若样式含 theme_ref，将其解析为实际颜色并回填 font_color / fill_color。
        """
        style = node.style
        if style is None:
            if node.style_ref and node.style_ref in doc.styles:
                style = doc.styles[node.style_ref]
        if style is None:
            return None

        # 解析 theme_ref → 实际颜色
        if style.theme_ref:
            resolved_color = self._THEME_COLORS.get(style.theme_ref)
            if resolved_color:
                # 创建副本，避免修改原始 IR
                from dataclasses import replace as dc_replace
                style = dc_replace(
                    style,
                    font_color=style.font_color or resolved_color,
                    fill_color=style.fill_color or resolved_color,
                    theme_ref=None,  # 已解析，清除引用
                )

        return style

    # 级联后的默认回退值
    _STYLE_DEFAULTS = {
        "font_family": "Microsoft YaHei UI",
        "font_size": 18,
        "font_weight": 400,
        "font_italic": False,
        "font_color": "#000000",
        "fill_opacity": 1.0,
    }

    def _style_val(self, style: IRStyle, field: str):
        """获取样式字段值，None 时回退到默认"""
        val = getattr(style, field, None)
        if val is None:
            return self._STYLE_DEFAULTS.get(field)
        return val

    def _apply_text_style(self, paragraph, style: IRStyle):
        """应用文本样式到段落"""
        font = paragraph.font
        family = self._style_val(style, "font_family")
        size = self._style_val(style, "font_size")
        weight = self._style_val(style, "font_weight")
        italic = self._style_val(style, "font_italic")
        color = self._style_val(style, "font_color")

        if family:
            font.name = family
        if size:
            font.size = Pt(size)
        if weight:
            font.bold = weight >= 700
        if italic is not None:
            font.italic = italic
        if color:
            font.color.rgb = self._hex_to_rgb(color)

    def _apply_text_layout(self, text_frame, paragraph, node: IRNode):
        """Apply text box layout options carried in node.extra.

        Supported DSL extras:
          align: left | center | right
          vertical_align: top | middle | bottom
          margin: number in mm, or margins: {left, right, top, bottom}
        """
        align = str(node.extra.get("align", node.extra.get("text_align", "left"))).lower()
        paragraph.alignment = {
            "left": PP_ALIGN.LEFT,
            "center": PP_ALIGN.CENTER,
            "right": PP_ALIGN.RIGHT,
        }.get(align, PP_ALIGN.LEFT)

        vertical_align = str(node.extra.get(
            "vertical_align",
            node.extra.get("verticalAlign", node.extra.get("valign", "top")),
        )).lower()
        text_frame.vertical_anchor = {
            "top": MSO_ANCHOR.TOP,
            "middle": MSO_ANCHOR.MIDDLE,
            "center": MSO_ANCHOR.MIDDLE,
            "bottom": MSO_ANCHOR.BOTTOM,
        }.get(vertical_align, MSO_ANCHOR.TOP)

        margins = node.extra.get("margins")
        margin = node.extra.get("margin")
        if isinstance(margins, dict):
            text_frame.margin_left = Mm(float(margins.get("left", node.extra.get("margin_left", 0))))
            text_frame.margin_right = Mm(float(margins.get("right", node.extra.get("margin_right", 0))))
            text_frame.margin_top = Mm(float(margins.get("top", node.extra.get("margin_top", 0))))
            text_frame.margin_bottom = Mm(float(margins.get("bottom", node.extra.get("margin_bottom", 0))))
        elif margin is not None:
            margin_mm = Mm(float(margin))
            text_frame.margin_left = margin_mm
            text_frame.margin_right = margin_mm
            text_frame.margin_top = margin_mm
            text_frame.margin_bottom = margin_mm
        else:
            if "margin_left" in node.extra:
                text_frame.margin_left = Mm(float(node.extra["margin_left"]))
            if "margin_right" in node.extra:
                text_frame.margin_right = Mm(float(node.extra["margin_right"]))
            if "margin_top" in node.extra:
                text_frame.margin_top = Mm(float(node.extra["margin_top"]))
            if "margin_bottom" in node.extra:
                text_frame.margin_bottom = Mm(float(node.extra["margin_bottom"]))

    @staticmethod
    def _is_wrap_disabled(node: IRNode) -> bool:
        value = node.extra.get("wrap", node.extra.get("word_wrap", True))
        if isinstance(value, str):
            return value.lower() in {"false", "no", "0", "nowrap", "none"}
        return value is False

    def _apply_text_warp(self, shape, text_effect: dict[str, Any]):
        """应用 WordArt 文本变换

        通过 Oxml 注入 <a:bodyPr> 的 presetTextWarp 属性。
        text_effect 示例: { transform: "arch", bend: 50 }
        """
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        # 获取 shape 的 txBody
        tx_body = shape._element.find(f'.//{{{a_ns}}}txBody')
        if tx_body is None:
            return

        # 获取或创建 bodyPr
        body_pr = tx_body.find(f'{{{a_ns}}}bodyPr')
        if body_pr is None:
            body_pr = etree.SubElement(tx_body, f'{{{a_ns}}}bodyPr')

        # 文本变换映射
        transform_map = {
            "arch": "textArchDown",
            "arch_up": "textArchUp",
            "wave": "textWave1",
            "circle": "textCircle",
            "slant_up": "textSlantUp",
            "slant_down": "textSlantDown",
            "triangle": "textTriangle",
            "chevron_up": "textChevronUp",
            "chevron_down": "textChevronDown",
            "button": "textButton",
            "deflate": "textDeflate",
            "inflate": "textInflate",
            "fade_up": "textFadeUp",
            "fade_down": "textFadeDown",
        }

        transform_type = text_effect.get("transform", text_effect.get("type", "plain"))
        preset = transform_map.get(transform_type, "textPlain")

        # 注入 presetTextWarp
        prst_tx_warp = etree.SubElement(body_pr, f'{{{a_ns}}}prstTxWarp')
        prst_tx_warp.set('prst', preset)

        # avLst (adjust value list)
        av_lst = etree.SubElement(prst_tx_warp, f'{{{a_ns}}}avLst')

        # bend 参数
        bend = text_effect.get("bend", 0)
        if bend != 0:
            gd = etree.SubElement(av_lst, f'{{{a_ns}}}gd')
            gd.set('name', 'adj')
            # PPTX bend 范围: -100000 ~ 100000 (万分比)
            gd.set('fmla', f'val {int(bend * 1000)}')

    def _apply_text_outline(self, shape, outline: dict[str, Any]):
        """应用文本描边 — <a:ln> 在文本 run 的 rPr 中

        outline: {color: "#RRGGBB", width: 1.5, dash: "solid"|"dash"|"dot"}
        """
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        p_ns = 'http://schemas.openxmlformats.org/presentationml/2006/main'
        tx_body = shape._element.find(f'.//{{{p_ns}}}txBody')
        if tx_body is None:
            return

        color = outline.get("color", "#000000")
        width_pt = outline.get("width", 1.0)
        dash = outline.get("dash", "solid")

        # 遍历所有 run 的 rPr（包括 defRPr）
        targets = tx_body.findall(f'.//{{{a_ns}}}rPr') + tx_body.findall(f'.//{{{a_ns}}}defRPr')
        for rPr in targets:
            ln = etree.SubElement(rPr, f'{{{a_ns}}}ln')
            ln.set('w', str(int(width_pt * 12700)))  # pt → EMU
            sf = etree.SubElement(ln, f'{{{a_ns}}}solidFill')
            clr = etree.SubElement(sf, f'{{{a_ns}}}srgbClr')
            clr.set('val', self._normalize_hex(color))

            if dash != "solid":
                prst_dash = etree.SubElement(ln, f'{{{a_ns}}}prstDash')
                prst_dash.set('val', {'dash': 'dash', 'dot': 'dot', 'dashDot': 'dashDot'}.get(dash, 'dash'))

    def _apply_text_reflection(self, shape, reflection: dict[str, Any]):
        """应用倒影效果 — <a:reflection> 在 effectLst 中

        reflection: {opacity: 50, distance: 3, blur: 2, direction: 5400000}
        """
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        sp_pr = shape._element.find(f'.//{{{a_ns}}}spPr')
        if sp_pr is None:
            sp_pr = etree.SubElement(shape._element, f'{{{a_ns}}}spPr')

        effect_lst = sp_pr.find(f'{{{a_ns}}}effectLst')
        if effect_lst is None:
            effect_lst = etree.SubElement(sp_pr, f'{{{a_ns}}}effectLst')

        ref_elem = etree.SubElement(effect_lst, f'{{{a_ns}}}reflection')
        opacity = reflection.get("opacity", 50)
        ref_elem.set('st', '0')
        ref_elem.set('endA', str(int(opacity / 100 * 100000)))
        ref_elem.set('dist', str(int(reflection.get("distance", 3) * 12700)))
        ref_elem.set('blurRad', str(int(reflection.get("blur", 2) * 12700)))
        # direction: 用户传入角度值，OOXML 使用 1/60000 度
        direction_deg = reflection.get("direction", 90)
        if direction_deg < 10000:
            direction_deg = direction_deg * 60000
        ref_elem.set('dir', str(int(direction_deg)))

    def _apply_text_bevel(self, shape, bevel: dict[str, Any]):
        """应用斜面浮雕 — <a:bevel> 在 sp3d 中

        bevel: {type: "relaxedInset", width: 3, height: 3, material: "matte"}
        """
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        sp_pr = shape._element.find(f'.//{{{a_ns}}}spPr')
        if sp_pr is None:
            sp_pr = etree.SubElement(shape._element, f'{{{a_ns}}}spPr')

        sp3d = sp_pr.find(f'{{{a_ns}}}sp3d')
        if sp3d is None:
            sp3d = etree.SubElement(sp_pr, f'{{{a_ns}}}sp3d')

        bevel_type = bevel.get("type", "relaxedInset")
        width_emu = int(bevel.get("width", 3) * 12700)
        height_emu = int(bevel.get("height", 3) * 12700)

        bevel_elem = etree.SubElement(sp3d, f'{{{a_ns}}}bevel')
        bevel_elem.set('prst', bevel_type)
        bevel_elem.set('w', str(width_emu))
        bevel_elem.set('h', str(height_emu))

    @staticmethod
    def _apply_text_spacing(paragraph, letter_spacing_pt: float | None, word_spacing_pt: float | None):
        """应用字距/词距 — <a:spc> 在 run 的 rPr 中

        PPTX 使用 hundredths of a point（hundredths of a point）。
        """
        if letter_spacing_pt is None and word_spacing_pt is None:
            return

        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        targets = paragraph._p.findall(f'.//{{{a_ns}}}rPr') + paragraph._p.findall(f'.//{{{a_ns}}}defRPr')

        for rPr in targets:
            # 字距：<a:spc><a:spcPts val="150"/></a:spc>（值为 hundredths of a point）
            if letter_spacing_pt is not None:
                spc = etree.SubElement(rPr, f'{{{a_ns}}}spc')
                spc_pts = etree.SubElement(spc, f'{{{a_ns}}}spcPts')
                spc_pts.set('val', str(int(letter_spacing_pt * 100)))
            # 词距：<a:spc><a:spcPct val="110000"/></a:spc>（110000 = 110%）
            if word_spacing_pt is not None:
                spc = etree.SubElement(rPr, f'{{{a_ns}}}spc')
                spc_pct = etree.SubElement(spc, f'{{{a_ns}}}spcPct')
                spc_pct.set('val', str(int(word_spacing_pt * 1000)))

    @staticmethod
    def _normalize_hex(hex_str: str) -> str:
        """规范化 hex 颜色为 6 位（#FFF → FFFFFF）"""
        h = str(hex_str).lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        return h[:6] if len(h) >= 6 else "000000"

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> RGBColor:
        """将 HEX 颜色转为 RGBColor，支持 #RGB / #RRGGBB / #RRGGBBAA"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = hex_str[0]*2 + hex_str[1]*2 + hex_str[2]*2
        elif len(hex_str) == 8:
            hex_str = hex_str[:6]
        if len(hex_str) != 6:
            return RGBColor(0, 0, 0)
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return RGBColor(r, g, b)
        except ValueError:
            return RGBColor(0, 0, 0)

    @staticmethod
    def _get_shape_type(name: str):
        """形状名称 → MSO_SHAPE 枚举"""
        mapping = {
            "rectangle": MSO_SHAPE.RECTANGLE,
            "rect": MSO_SHAPE.RECTANGLE,
            "rounded_rectangle": MSO_SHAPE.ROUNDED_RECTANGLE,
            "round_rect": MSO_SHAPE.ROUNDED_RECTANGLE,
            "circle": MSO_SHAPE.OVAL,
            "ellipse": MSO_SHAPE.OVAL,
            "oval": MSO_SHAPE.OVAL,
            "triangle": MSO_SHAPE.ISOSCELES_TRIANGLE,
            "diamond": MSO_SHAPE.DIAMOND,
            "arrow": MSO_SHAPE.RIGHT_ARROW,
            "arrow_right": MSO_SHAPE.RIGHT_ARROW,
            "circular_arrow": MSO_SHAPE.CIRCULAR_ARROW,
            "arc": MSO_SHAPE.ARC,
            "document": MSO_SHAPE.FLOWCHART_DOCUMENT,
            "lightning": MSO_SHAPE.LIGHTNING_BOLT,
            "star": MSO_SHAPE.STAR_5_POINT,
            "hexagon": MSO_SHAPE.HEXAGON,
            "pentagon": MSO_SHAPE.PENTAGON,
            "chevron": MSO_SHAPE.CHEVRON,
            "cross": MSO_SHAPE.CROSS,
        }
        return mapping.get(name, MSO_SHAPE.RECTANGLE)

    def _fit_text_style_to_box(
        self,
        text: str,
        pos: IRPosition,
        style: IRStyle | None,
        node: IRNode,
    ) -> IRStyle | None:
        """在文本明显放不下时缩小字号，避免输出 PPT 内文字溢出。"""
        if style is None:
            style = IRStyle()
        if node.extra.get("auto_fit", True) is False:
            return style

        font_size = self._style_val(style, "font_size") or 18
        if pos.width_mm <= 0 or pos.height_mm <= 0 or not text:
            return style

        min_size = int(node.extra.get("min_font_size", 8))
        chars_per_line = max(1, int(pos.width_mm / max(1.0, font_size * 0.18)))
        lines = str(text).splitlines() or [""]
        estimated_lines = sum(max(1, (len(line) + chars_per_line - 1) // chars_per_line) for line in lines)
        needed_height = estimated_lines * font_size * 0.48 + 3
        if needed_height <= pos.height_mm:
            return style

        scale = max(min_size / font_size, pos.height_mm / needed_height)
        fitted_size = max(min_size, int(font_size * min(1.0, scale)))
        if fitted_size == font_size:
            return style
        return dc_replace(style, font_size=fitted_size)

    # ============================================================
    # 图片滤镜
    # ============================================================

    def _apply_image_filter(self, picture, filter_spec: dict[str, Any]):
        """应用图片滤镜

        支持的滤镜类型（PPTX 原生）：
          - duotone: 双色调 { highlight: "#FFF", shadow: "#000" }
          - grayscale: 灰度（无参数）
          - biLevel: 双色阶黑白 { threshold: 0-100 }
          - blur: 模糊 { radius: 1-100, grow: true/false }
          - opacity: 透明度 { value: 0-100 }
          - brightness: 亮度 { value: -100 to 100 }
          - contrast: 对比度 { value: -100 to 100 }

        也支持简写形式：
          filter: { highlight: "#FFF", shadow: "#000" }  # 默认 duotone
          filter: { type: grayscale }
          filter: [{ type: grayscale }, { type: blur, radius: 5 }]  # 多效果叠加
        """
        # 支持单个滤镜或滤镜列表
        if isinstance(filter_spec, list):
            for f in filter_spec:
                self._apply_single_filter(picture, f)
        else:
            self._apply_single_filter(picture, filter_spec)

    def _apply_single_filter(self, picture, filter_spec: dict[str, Any]):
        """应用单个图片滤镜"""
        from lxml import etree

        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        # 获取 blip 元素
        blip = picture._element.find(f'.//{{{a_ns}}}blip')
        if blip is None:
            return

        # 推断类型：有 highlight/shadow → duotone，否则从 type 字段读
        filter_type = filter_spec.get("type")
        if filter_type is None and ("highlight" in filter_spec or "shadow" in filter_spec):
            filter_type = "duotone"
        if not filter_type:
            return  # 无有效滤镜类型，不做任何处理

        # 类型分派
        if filter_type == "duotone":
            self._apply_duotone(blip, filter_spec)
        elif filter_type == "grayscale":
            self._apply_grayscale(blip)
        elif filter_type == "biLevel":
            self._apply_bilevel(blip, filter_spec)
        elif filter_type == "blur":
            self._apply_blur(picture, filter_spec)
        elif filter_type == "opacity":
            self._apply_image_opacity(blip, filter_spec)
        elif filter_type in ("brightness", "contrast"):
            self._apply_luminance(blip, filter_spec)

    def _apply_duotone(self, blip, spec: dict[str, Any]):
        """双色调"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        for old in blip.findall(f'{{{a_ns}}}duotone'):
            blip.remove(old)

        duotone = etree.SubElement(blip, f'{{{a_ns}}}duotone')
        srgb1 = etree.SubElement(duotone, f'{{{a_ns}}}srgbClr')
        srgb1.set('val', self._normalize_hex(spec.get("highlight", "#FFFFFF")))
        srgb2 = etree.SubElement(duotone, f'{{{a_ns}}}srgbClr')
        srgb2.set('val', self._normalize_hex(spec.get("shadow", "#000000")))

    def _apply_grayscale(self, blip):
        """灰度"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        for old in blip.findall(f'{{{a_ns}}}grayscl'):
            blip.remove(old)
        etree.SubElement(blip, f'{{{a_ns}}}grayscl')

    def _apply_bilevel(self, blip, spec: dict[str, Any]):
        """双色阶（黑白）"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        for old in blip.findall(f'{{{a_ns}}}biLevel'):
            blip.remove(old)
        bi = etree.SubElement(blip, f'{{{a_ns}}}biLevel')
        # threshold: 0-100 → PPTX 0-100000
        threshold = int(spec.get("threshold", 50) * 1000)
        bi.set('thresh', str(threshold))

    def _apply_blur(self, picture, spec: dict[str, Any]):
        """模糊（注入到 effectLst）"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        sp_pr = getattr(picture._element, 'spPr', None)
        if sp_pr is None:
            return
        effect_lst = sp_pr.find(f'{{{a_ns}}}effectLst')
        if effect_lst is None:
            effect_lst = etree.SubElement(sp_pr, f'{{{a_ns}}}effectLst')

        for old in effect_lst.findall(f'{{{a_ns}}}blur'):
            effect_lst.remove(old)
        blur = etree.SubElement(effect_lst, f'{{{a_ns}}}blur')
        # radius: 1-100 → PPTX EMU (1pt = 12700)
        radius = int(spec.get("radius", 5) * 12700)
        blur.set('rad', str(radius))
        blur.set('grow', '1' if spec.get("grow", True) else '0')

    def _apply_image_opacity(self, blip, spec: dict[str, Any]):
        """透明度"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        for old in blip.findall(f'{{{a_ns}}}alphaModFix'):
            blip.remove(old)
        alpha = etree.SubElement(blip, f'{{{a_ns}}}alphaModFix')
        # value: 0-100 → PPTX 0-100000
        amount = int(spec.get("value", 100) * 1000)
        alpha.set('amt', str(amount))

    def _apply_luminance(self, blip, spec: dict[str, Any]):
        """亮度/对比度 — 通过 <a:effectLst>/<a:lum> 实现"""
        from lxml import etree
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

        filter_type = spec.get("type", "brightness")
        value = spec.get("value", 0)

        # lum 需要嵌套在 blipFill 的 effectLst 中
        blip_fill = blip.getparent()
        if blip_fill is None:
            return

        effect_lst = blip_fill.find(f'{{{a_ns}}}effectLst')
        if effect_lst is None:
            effect_lst = etree.SubElement(blip_fill, f'{{{a_ns}}}effectLst')

        # 清理旧 lum 元素
        for old in effect_lst.findall(f'{{{a_ns}}}lum'):
            effect_lst.remove(old)

        lum = etree.SubElement(effect_lst, f'{{{a_ns}}}lum')
        # value: -100 to 100 → PPTX -100000 to 100000
        if filter_type == "brightness":
            lum.set('bright', str(int(value * 1000)))
        elif filter_type == "contrast":
            lum.set('contrast', str(int(value * 1000)))
