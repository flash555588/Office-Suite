"""DSL → IR 编译器 — 将 DSL Document 编译为 IRDocument

核心职责：
1. 将 DSL 文档类型安全地转换为 IR 节点树
2. 解析坐标（mm/% → mm 绝对值）
3. 样式级联（theme → document → slide → element → inline）
4. 保留原始 DSL 路径用于调试

数据流：
  YAML 文件 → dsl/parser.py::parse_yaml() → Document 对象
  Document  → [本文件]::compile_document() → IRDocument 树
  IRDocument → renderer/pptx/deck.py::PPTXRenderer.render() → .pptx 文件

坐标映射规则（设计方案第四章）：
  mm  → PPTX: × 36000 (EMU)    DOCX: × 1440 (Twips)    PDF: 直接使用
  %   → 相对于父容器尺寸计算后再走 mm 映射
  auto → 渲染器自行计算（文本根据字号+换行，图片根据原始比例）
  center → (parent_width - self_width) / 2
"""

import logging
from typing import Any

from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM

logger = logging.getLogger(__name__)

# ============================================================
# 高度估算默认值 (mm)
# ============================================================
_DEFAULT_LINE_H = 2.0        # 水平线
_DEFAULT_SHAPE_H = 10.0      # 通用形状
_DEFAULT_TABLE_H = 60.0      # 表格
_DEFAULT_CHART_H = 80.0      # 图表
_DEFAULT_IMAGE_H = 60.0      # 图片
_DEFAULT_EMPTY_TEXT_H = 8.0  # 空文本块
_DEFAULT_FONT_SIZE = 18      # 默认字号 (pt)
_WIDTH_COEFF_CJK = 0.6       # 中文字符宽度系数 (× 字号 pt)
_WIDTH_COEFF_LATIN = 0.35    # 英文字符宽度系数 (× 字号 pt)

from ..dsl.parser import parse_style
from ..dsl.schema import (
    Document,
    Element,
    FillSpec,
    PositionSpec,
    Slide,
    StyleSpec,
)
from ..engine.style.cascade import cascade_style, cascade_style_by_name, DEFAULT_THEME_STYLES
from ..engine.style.color import OKLCH, oklch_to_hex
from .types import (
    IRAnimation,
    IRDocument,
    IRNode,
    IRPathText,
    IRPosition,
    IRStyle,
    NodeType,
    VALID_PATH_TYPES,
)


# ============================================================
# 坐标转换
# ============================================================

def _parse_length(value: str | float | None, parent_size: float = 0) -> tuple[float, bool, bool]:
    """解析长度值，返回 (mm值, is_relative, is_auto)"""
    if value is None:
        return 0.0, False, False
    if isinstance(value, (int, float)):
        return float(value), False, False
    if value == "auto":
        return 0.0, False, True
    if value == "center":
        return 0.0, False, False  # center 由 position.center 标记处理

    s = str(value).strip()
    if s.endswith("mm"):
        return float(s[:-2]), False, False
    if s.endswith("%"):
        pct = float(s[:-1]) / 100.0
        return parent_size * pct, True, False
    if s.endswith("in"):
        # 英寸 → mm (1 in = 25.4 mm)
        return float(s[:-2]) * 25.4, False, False
    if s.endswith("pt"):
        # pt → mm (1 pt = 0.3528 mm)
        return float(s[:-2]) * 0.3528, False, False
    # 默认当作 mm
    try:
        return float(s), False, False
    except ValueError:
        logger.warning("无法解析长度值 %r，回退为 0mm", s)
        return 0.0, False, False


def compile_position(pos: PositionSpec | None, parent_w: float = SLIDE_WIDTH_MM, parent_h: float = SLIDE_HEIGHT_MM) -> IRPosition | None:
    """将 DSL PositionSpec 编译为 IRPosition（mm 单位）

    默认父容器尺寸：标准 16:9 幻灯片 = 254mm x 142.875mm (10" x 5.625")
    注意：190.5mm 是 4:3 幻灯片高度（7.5"），16:9 正确高度是 142.875mm（5.625"）

    返回 None 表示元素未指定位置，由布局引擎（flex/grid/constraint）注入。
    """
    if pos is None:
        return None

    x, _, _ = _parse_length(pos.x, parent_w)
    y, _, _ = _parse_length(pos.y, parent_h)
    w, w_rel, w_auto = _parse_length(pos.width, parent_w)
    h, h_rel, h_auto = _parse_length(pos.height, parent_h)

    # bottom 定位：从底部向上计算
    if pos.bottom is not None:
        bottom_mm, _, _ = _parse_length(pos.bottom, parent_h)
        y = parent_h - bottom_mm - h

    return IRPosition(
        x_mm=x,
        y_mm=y,
        width_mm=w,
        height_mm=h,
        is_relative=w_rel or h_rel,
        is_center=pos.center,
        is_auto=w_auto or h_auto,
    )


# ============================================================
# 样式编译
# ============================================================

import re

_OKLCH_RE = re.compile(
    r"oklch\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)",
    re.IGNORECASE,
)


def _resolve_color(value: str | None) -> str | None:
    """解析颜色值，支持 HEX 和 oklch(l, c, h) 格式

    oklch 格式示例: oklch(0.7, 0.15, 30)
    l: 0-1 亮度, c: 0-0.4 饱和度, h: 0-360 色相
    """
    if not value:
        return value
    m = _OKLCH_RE.match(value.strip())
    if m:
        l, c, h = float(m.group(1)), float(m.group(2)), float(m.group(3))
        return oklch_to_hex(OKLCH(l=l, c=c, h=h))
    return value


def compile_style(style: StyleSpec | None) -> IRStyle | None:
    """将 DSL StyleSpec 编译为 IRStyle"""
    if style is None:
        return None

    ir = IRStyle()
    if style.font:
        ir.font_family = style.font.family
        ir.font_size = style.font.size
        ir.font_weight = style.font.weight
        ir.font_italic = style.font.italic
        ir.font_color = _resolve_color(style.font.color)
    if style.fill:
        ir.fill_color = _resolve_color(style.fill.color)
        ir.fill_gradient = _gradient_to_dict(style.fill.gradient) if style.fill.gradient else None
        ir.fill_opacity = style.fill.opacity
    if style.shadow:
        ir.shadow = {
            "blur": style.shadow.blur,
            "offset": style.shadow.offset,
            "color": _resolve_color(style.shadow.color),
        }
    if style.border:
        ir.border = style.border
    if style.text_effect:
        ir.text_effect = style.text_effect
    return ir


def _extract_text_effect_fields(ir: IRStyle):
    """从 text_effect dict 中提取扩展字段到 IRStyle 顶层字段"""
    if not ir.text_effect:
        return
    te = ir.text_effect
    if not isinstance(te, dict):
        return
    if ir.text_outline is None and ("stroke" in te or "outline" in te):
        ir.text_outline = te.get("stroke") or te.get("outline")
    if ir.text_reflection is None and "reflection" in te:
        ir.text_reflection = te["reflection"]
    if ir.text_bevel is None and "bevel" in te:
        ir.text_bevel = te["bevel"]
    if ir.letter_spacing is None and "letter_spacing" in te:
        ir.letter_spacing = float(te["letter_spacing"])
    if ir.word_spacing is None and "word_spacing" in te:
        ir.word_spacing = float(te["word_spacing"])


def _gradient_to_dict(grad) -> dict[str, Any]:
    return {
        "type": grad.type,
        "angle": grad.angle,
        "stops": [_resolve_color(s) for s in grad.stops],
    }


# ============================================================
# 元素编译
# ============================================================

def _parse_animations(raw: dict | None) -> list[IRAnimation]:
    """将 DSL animation 字典解析为 IRAnimation 列表

    支持格式：
      animation: { effect: fade, duration: 0.5 }
      animation:
        - { effect: fade_in, trigger: on_click }
        - { effect: pulse, trigger: after_previous }
    """
    if not raw:
        return []

    # 支持单个动画 dict 或列表
    items = raw if isinstance(raw, list) else [raw]

    animations = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # 动画类型推断
        # DSL 的 "type" 字段是效果名（fade_in / slide_up 等），不是分类
        effect = item.get("type") or item.get("effect") or item.get("animation") or "fade"

        # 根据效果名推断 anim_type 分类
        exit_effects = {"fade_out", "slide_out_up", "slide_out_down", "slide_out_left",
                        "slide_out_right", "zoom_out_exit"}
        emphasis_effects = {"pulse", "shake", "glow_pulse", "breathe", "float",
                            "spin_emphasis", "grow", "shrink"}
        if effect in exit_effects:
            anim_type = "exit"
        elif effect in emphasis_effects:
            anim_type = "emphasis"
        else:
            anim_type = "entry"

        animations.append(IRAnimation(
            anim_type=anim_type,
            effect=effect,
            trigger=item.get("trigger", "on_click"),
            duration=item.get("duration", 0.5),
            delay=item.get("delay", 0.0),
            easing=item.get("easing", "ease_out"),
            repeat=item.get("repeat", 0),
            direction=item.get("direction", ""),
            extra={k: v for k, v in item.items()
                   if k not in ("type", "effect", "animation", "trigger",
                                "duration", "delay", "easing", "repeat", "direction")},
        ))

    return animations


def _parse_path_text(raw: dict | None) -> IRPathText | None:
    """将 DSL path_text 字典解析为 IRPathText

    支持格式：
      path_text: { path_type: arc, radius: 80, start_angle: 10, end_angle: 170 }
      path_text: { path_type: wave, amplitude: 8, wavelength: 40 }
      path_text: { path_type: custom, custom_path: "M 0 0 L 100 0" }

    无效 path_type 时记录警告并返回 None（降级为普通文本）。
    """
    if not raw or not isinstance(raw, dict):
        return None

    path_type = str(raw.get("path_type", "arc"))
    if path_type not in VALID_PATH_TYPES:
        logger.warning(
            "未知 path_text.path_type: '%s'，合法类型: %s，降级为普通文本",
            path_type, sorted(VALID_PATH_TYPES),
        )
        return None

    def _float(key: str, default: float) -> float:
        val = raw.get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    return IRPathText(
        path_type=path_type,
        radius=_float("radius", 100.0),
        start_angle=_float("start_angle", 0.0),
        end_angle=_float("end_angle", 180.0),
        amplitude=_float("amplitude", 10.0),
        wavelength=_float("wavelength", 50.0),
        custom_path=str(raw.get("custom_path", "")),
        char_spacing=_float("char_spacing", 0.0),
        bend=_float("bend", 50.0),
    )


# DSL type → IR NodeType 映射
TYPE_MAP = {
    "text": NodeType.TEXT,
    "image": NodeType.IMAGE,
    "shape": NodeType.SHAPE,
    "table": NodeType.TABLE,
    "chart": NodeType.CHART,
    "group": NodeType.GROUP,
    "semantic_icon": NodeType.GROUP,
    "video": NodeType.VIDEO,
    "audio": NodeType.AUDIO,
    "diagram": NodeType.DIAGRAM,
    "code": NodeType.CODE,
    "3d_model": NodeType.MODEL_3D,
    "map": NodeType.MAP,
}


def _semantic_icon_style(color: str, *, fill_opacity: float | None = None) -> IRStyle:
    if fill_opacity is None:
        return IRStyle()
    return IRStyle(fill_color=color, fill_opacity=fill_opacity)


def _semantic_icon_shape(
    shape_type: str,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
    *,
    fill_opacity: float | None = None,
    stroke_width: float = 1.4,
) -> IRNode:
    extra = {"shape_type": shape_type}
    if stroke_width > 0:
        extra["outline"] = {"color": color, "width": stroke_width}
    return IRNode(
        node_type=NodeType.SHAPE,
        position=IRPosition(x_mm=x, y_mm=y, width_mm=w, height_mm=h),
        style=_semantic_icon_style(color, fill_opacity=fill_opacity),
        extra=extra,
    )


def _semantic_icon_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    *,
    stroke_width: float = 1.4,
) -> IRNode:
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    return IRNode(
        node_type=NodeType.SHAPE,
        position=IRPosition(x_mm=left, y_mm=top, width_mm=width, height_mm=height),
        style=IRStyle(),
        extra={
            "shape_type": "line",
            "line_points": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "outline": {"color": color, "width": stroke_width},
        },
    )


def _compile_semantic_icon(elem: Element, path: str = "") -> IRNode:
    pos = compile_position(elem.position)
    if pos is None:
        pos = IRPosition(width_mm=16, height_mm=16)

    icon = str(elem.extra.get("icon", elem.extra.get("name", "custom"))).lower()
    color = str(elem.extra.get("color", "#FACC15"))
    stroke_width = float(elem.extra.get("stroke_width", 1.4))
    x0, y0, w, h = pos.x_mm, pos.y_mm, pos.width_mm, pos.height_mm

    def sx(v: float) -> float:
        return x0 + w * v / 100

    def sy(v: float) -> float:
        return y0 + h * v / 100

    def sw(v: float) -> float:
        return w * v / 100

    def sh(v: float) -> float:
        return h * v / 100

    children = _compile_semantic_icon_primitives(
        elem.extra.get("primitives"),
        sx=sx,
        sy=sy,
        sw=sw,
        sh=sh,
        color=color,
        default_stroke_width=stroke_width,
    )

    return IRNode(
        node_type=NodeType.GROUP,
        id=elem.extra.get("id", ""),
        position=pos,
        children=children,
        extra={"semantic_icon": icon, "color": color},
        source_path=path,
    )


def _compile_semantic_icon_primitives(
    primitives: Any,
    *,
    sx,
    sy,
    sw,
    sh,
    color: str,
    default_stroke_width: float,
) -> list[IRNode]:
    """Compile AI-authored icon primitives into PPT-native shape nodes.

    Primitive coordinates are normalized to a 0-100 icon box, so the same icon
    scales cleanly with its outer `position`.
    """
    if not isinstance(primitives, list):
        return []

    shape_aliases = {
        "rect": "rectangle",
        "rectangle": "rectangle",
        "round_rect": "rounded_rectangle",
        "rounded_rectangle": "rounded_rectangle",
        "circle": "ellipse",
        "ellipse": "ellipse",
        "line": "line",
        "triangle": "triangle",
    }

    nodes: list[IRNode] = []
    for primitive in primitives:
        if not isinstance(primitive, dict):
            continue
        primitive_type = str(primitive.get("type", "shape")).lower()
        stroke_width = float(primitive.get("stroke_width", default_stroke_width))
        primitive_color = str(primitive.get("color", color))

        if primitive_type == "line":
            x1 = float(primitive.get("x1", 0))
            y1 = float(primitive.get("y1", 0))
            x2 = float(primitive.get("x2", 100))
            y2 = float(primitive.get("y2", 100))
            nodes.append(_semantic_icon_line(
                sx(x1), sy(y1), sx(x2), sy(y2), primitive_color,
                stroke_width=stroke_width,
            ))
            continue

        shape_type = shape_aliases.get(str(primitive.get("shape", primitive_type)).lower(), "rectangle")
        x = float(primitive.get("x", 0))
        y = float(primitive.get("y", 0))
        w = float(primitive.get("width", primitive.get("w", 20)))
        h = float(primitive.get("height", primitive.get("h", w)))
        # fill 可以是颜色字符串（如 "#D4AF37"）或布尔值
        # fill_opacity 是独立的透明度字段（0.0-1.0）
        raw_fill = primitive.get("fill")
        raw_fill_opacity = primitive.get("fill_opacity")
        # 判断 fill 是颜色还是透明度
        if isinstance(raw_fill, str) and raw_fill.startswith("#"):
            # fill 是颜色，覆盖 primitive_color
            primitive_color = raw_fill
            fill_opacity = 1.0 if raw_fill_opacity is None else float(raw_fill_opacity)
        elif isinstance(raw_fill, bool):
            fill_opacity = 0.18 if raw_fill else None
        elif raw_fill_opacity is not None:
            fill_opacity = float(raw_fill_opacity)
        elif raw_fill is not None:
            fill_opacity = float(raw_fill)
        else:
            fill_opacity = None
        opacity = primitive.get("opacity")
        if opacity is not None and fill_opacity is not None:
            fill_opacity = fill_opacity * float(opacity)
        elif opacity is not None:
            fill_opacity = float(opacity)
        stroke = primitive.get("stroke", True)
        actual_stroke_width = stroke_width if stroke is not False else 0
        nodes.append(_semantic_icon_shape(
            shape_type,
            sx(x),
            sy(y),
            sw(w),
            sh(h),
            primitive_color,
            fill_opacity=fill_opacity,
            stroke_width=actual_stroke_width,
        ))

    return nodes

LAYER_ORDER = {
    "background": 0,
    "illustration": 10,
    "scrim": 20,
    "content": 30,
    "foreground": 40,
    "overlay": 50,
}


def _with_layer_metadata(elem: Element, layer_name: str, order: int) -> Element:
    extra = dict(elem.extra)
    extra.setdefault("layer", layer_name)
    extra.setdefault("_layer_order", order)
    return Element(
        type=elem.type,
        content=elem.content,
        format=getattr(elem, "format", "plain"),
        source=elem.source,
        style=elem.style,
        style_ref=elem.style_ref,
        position=elem.position,
        data_ref=elem.data_ref,
        chart_type=elem.chart_type,
        query=elem.query,
        prompt=elem.prompt,
        size=elem.size,
        opacity=elem.opacity,
        filter=elem.filter,
        animation=elem.animation,
        children=elem.children,
        extra=extra,
    )


def _compile_component(
    elem: Element,
    global_styles: dict[str, StyleSpec],
    doc_styles: dict[str, IRStyle],
    theme_name: str = "default",
    parent_w: float = SLIDE_WIDTH_MM,
    parent_h: float = SLIDE_HEIGHT_MM,
    path: str = "",
) -> IRNode:
    """将 DSL 组件元素编译为 IRNode（GROUP 包裹展开后的子节点）

    DSL 格式：
        type: component
        extra:
          component: chart_card
          title: "月度营收"
          chart_type: bar
          categories: ["Q1", "Q2", "Q3", "Q4"]
          series: [{ name: "营收", values: [8000, 9500, 10500, 12000] }]
          position: { x: 25mm, y: 30mm, width: 200mm, height: 90mm }

    组件展开后生成的子 IRNode 被放入 GROUP 容器。
    """
    from ..components.registry import generate_component

    comp_name = elem.extra.get("component", "")
    if not comp_name:
        logger.warning("组件元素缺少 component 名称，降级为 shape: %s", path)
        node_type = NodeType.SHAPE
        return IRNode(
            node_type=node_type,
            position=compile_position(elem.position, parent_w, parent_h) or IRPosition(),
            style=IRStyle(),
            extra={"_warning": "missing component name"},
        )

    # 收集组件参数（排除元数据 key）
    _META_KEYS = {"component", "layer", "z_index", "layout", "spacing", "padding_top"}
    params: dict[str, Any] = {k: v for k, v in elem.extra.items() if k not in _META_KEYS}

    # 将 position 信息传给组件
    if elem.position:
        ir_pos = compile_position(elem.position, parent_w, parent_h)
        if ir_pos:
            params.setdefault("position", {
                "x": ir_pos.x_mm,
                "y": ir_pos.y_mm,
                "width": ir_pos.width_mm,
                "height": ir_pos.height_mm,
            })

    try:
        child_nodes = generate_component(comp_name, params)
    except ValueError as exc:
        logger.warning("组件 %r 展开失败，降级为 shape: %s", comp_name, exc)
        return IRNode(
            node_type=NodeType.SHAPE,
            position=compile_position(elem.position, parent_w, parent_h) or IRPosition(),
            style=IRStyle(),
            extra={"_warning": str(exc)},
        )

    # 将组件的子节点放入 GROUP 容器
    group_pos = compile_position(elem.position, parent_w, parent_h) or IRPosition()
    # 调整子节点坐标：组件内部使用相对坐标，需要加上组件的绝对位置偏移
    for child in child_nodes:
        child.position.x_mm += group_pos.x_mm
        child.position.y_mm += group_pos.y_mm

    return IRNode(
        node_type=NodeType.GROUP,
        position=group_pos,
        style=IRStyle(),
        children=child_nodes,
        extra={"component": comp_name},
    )


def _ordered_slide_elements(slide: Slide) -> list[Element]:
    """合并 slide.layers 和旧 elements，并按图层顺序稳定排序。"""
    layered: list[tuple[int, float, int, Element]] = []
    sequence = 0

    for layer_name, elements in slide.layers.items():
        layer_order = LAYER_ORDER.get(str(layer_name), 30)
        for elem in elements:
            z_index = float(elem.extra.get("z_index", 0))
            layered.append((
                layer_order,
                z_index,
                sequence,
                _with_layer_metadata(elem, str(layer_name), layer_order),
            ))
            sequence += 1

    for elem in slide.elements:
        layer_name = str(elem.extra.get("layer", "content"))
        layer_order = LAYER_ORDER.get(layer_name, 30)
        z_index = float(elem.extra.get("z_index", 0))
        layered.append((
            layer_order,
            z_index,
            sequence,
            _with_layer_metadata(elem, layer_name, layer_order),
        ))
        sequence += 1

    return [item[3] for item in sorted(layered, key=lambda item: (item[0], item[1], item[2]))]


def compile_element(
    elem: Element,
    global_styles: dict[str, StyleSpec],
    doc_styles: dict[str, IRStyle],  # 已编译的 IR 全局样式
    theme_name: str = "default",
    parent_w: float = SLIDE_WIDTH_MM,
    parent_h: float = SLIDE_HEIGHT_MM,
    path: str = "",
) -> IRNode:
    """将 DSL Element 编译为 IRNode

    样式级联：theme → doc_global → element_style_ref → element_inline
    """
    if elem.type == "semantic_icon":
        return _compile_semantic_icon(elem, path)

    if elem.type == "component":
        return _compile_component(elem, global_styles, doc_styles, theme_name, parent_w, parent_h, path)

    node_type = TYPE_MAP.get(elem.type, NodeType.SHAPE)

    # 样式：支持字符串引用或内联（dict 或 StyleSpec）
    style_ref = None
    inline_style = None

    if isinstance(elem.style_ref, str):
        style_ref = elem.style_ref
    elif isinstance(elem.style, str):
        style_ref = elem.style
    elif isinstance(elem.style, dict):
        # 原始 YAML dict → StyleSpec → IRStyle
        parsed = parse_style(elem.style)
        if parsed:
            inline_style = compile_style(parsed)
    elif isinstance(elem.style, StyleSpec):
        inline_style = compile_style(elem.style)

    # 样式级联
    theme_styles = DEFAULT_THEME_STYLES  # P0 使用内置主题
    cascaded_style = cascade_style_by_name(
        style_name=style_ref,
        theme_styles=theme_styles,
        doc_styles=doc_styles,
        slide_style=None,  # slide 级样式在后续迭代添加
        element_style=inline_style,
    )
    # 从 text_effect dict 中提取扩展字段（描边/倒影/斜面/字距）
    if cascaded_style:
        _extract_text_effect_fields(cascaded_style)

    # 位置
    ir_pos = compile_position(elem.position, parent_w, parent_h)

    # 处理 size 字段覆盖 position 的宽高
    if elem.size:
        w_raw = elem.size.get("width")
        h_raw = elem.size.get("height")
        if w_raw is not None or h_raw is not None:
            # ir_pos 为 None 时创建默认值，避免 AttributeError
            if ir_pos is None:
                ir_pos = IRPosition()
            if w_raw is not None:
                w_mm, _, _ = _parse_length(w_raw, parent_w)
                ir_pos.width_mm = w_mm
            if h_raw is not None:
                h_mm, _, _ = _parse_length(h_raw, parent_h)
                ir_pos.height_mm = h_mm

    # 图片 source 处理
    source = elem.source
    if isinstance(source, dict):
        source = source  # 保留 dict 形式

    # 子节点 — 支持 stack 布局自动排列
    children = []
    stack_layout = elem.extra.get("layout", "") == "stack"
    stack_spacing = float(elem.extra.get("spacing", 5))  # 默认 5mm 间距
    stack_cursor_y = float(elem.extra.get("padding_top", 0))  # 起始 y 偏移

    for i, child in enumerate(elem.children):
        child_path = f"{path}/{child.type}[{i}]"

        # stack 布局：自动计算子元素 y 坐标
        if stack_layout and child.position is None:
            # shape 默认高度
            default_h = None
            if child.type == "shape":
                shape_type = child.extra.get("shape_type", "rectangle")
                if shape_type == "line":
                    default_h = 2
                else:
                    default_h = 10

            # 处理 extra.center → position.center
            extra_copy = dict(child.extra)
            center_flag = extra_copy.pop("center", False)

            child_pos = PositionSpec(
                x=elem.extra.get("padding_left", 0),
                y=stack_cursor_y,
                width=elem.extra.get("content_width"),
                height=default_h,
                center=bool(center_flag),
            )
            child = Element(
                type=child.type,
                content=child.content,
                format=getattr(child, "format", "plain"),
                source=child.source,
                style=child.style,
                style_ref=child.style_ref,
                position=child_pos,
                data_ref=child.data_ref,
                chart_type=child.chart_type,
                query=child.query,
                prompt=child.prompt,
                size=child.size,
                opacity=child.opacity,
                filter=child.filter,
                animation=child.animation,
                children=child.children,
                extra=extra_copy,
            )

        ir_child = compile_element(
            child, global_styles, doc_styles, theme_name,
            ir_pos.width_mm or parent_w, ir_pos.height_mm or parent_h, child_path,
        )
        children.append(ir_child)

        # stack 布局：更新游标 y
        if stack_layout:
            child_h = ir_child.position.height_mm if ir_child.position else 0
            if child_h <= 0:
                # 根据元素类型估算高度
                if ir_child.node_type == NodeType.TEXT:
                    font_size = ir_child.style.font_size if ir_child.style else 18
                    child_h = max(font_size * 0.5, 8)
                elif ir_child.node_type == NodeType.SHAPE:
                    child_h = 2
                else:
                    child_h = 10
            stack_cursor_y += child_h + stack_spacing

    # 动画
    animations = _parse_animations(elem.animation)

    # 路径文字（从 extra 中提取，提升为 IR 顶层字段）
    path_text = _parse_path_text(elem.extra.get("path_text"))
    content = elem.content
    if isinstance(content, str):
        content = content.replace("\\n", "\n")

    return IRNode(
        node_type=node_type,
        id=elem.extra.get("id", ""),
        content=content,
        content_format=elem.format if hasattr(elem, "format") else "plain",
        source=source,
        position=ir_pos,
        style=cascaded_style,
        style_ref=style_ref,
        children=children,
        data_ref=elem.data_ref,
        chart_type=elem.chart_type,
        animations=animations,
        path_text=path_text,
        extra={k: v for k, v in elem.extra.items() if k not in ("id", "path_text")},
        source_path=path,
    )


# ============================================================
# 幻灯片编译
# ============================================================

def _estimate_element_height(elem: Element, content_width: float) -> float:
    """估算元素高度（mm）

    用于 stack 布局的高度预估和自动分页判断。
    """
    # 如果有显式 position 且有 height，直接使用
    if elem.position and elem.position.height:
        h_raw = str(elem.position.height).replace("mm", "").strip()
        try:
            return float(h_raw)
        except ValueError:
            pass

    # shape 类型
    if elem.type == "shape":
        shape_type = elem.extra.get("shape_type", "rectangle")
        if shape_type == "line":
            return _DEFAULT_LINE_H
        # 有 size.height 时使用
        if elem.size and elem.size.get("height"):
            h_raw = str(elem.size["height"]).replace("mm", "").strip()
            try:
                return float(h_raw)
            except ValueError:
                pass
        return _DEFAULT_SHAPE_H

    # table 类型
    if elem.type == "table":
        if elem.position and elem.position.height:
            h_raw = str(elem.position.height).replace("mm", "").strip()
            try:
                return float(h_raw)
            except ValueError:
                pass
        return _DEFAULT_TABLE_H

    # chart 类型
    if elem.type == "chart":
        return _DEFAULT_CHART_H

    # image 类型
    if elem.type == "image":
        return _DEFAULT_IMAGE_H

    # text 类型（核心逻辑）
    if elem.type == "text":
        content = elem.content or ""
        if not content:
            return _DEFAULT_EMPTY_TEXT_H

        # 从 style 中获取字号
        font_size = _DEFAULT_FONT_SIZE
        if isinstance(elem.style, dict):
            font_spec = elem.style.get("font", {})
            if isinstance(font_spec, dict):
                font_size = font_spec.get("size", _DEFAULT_FONT_SIZE)
        elif isinstance(elem.style, StyleSpec) and elem.style.font:
            font_size = elem.style.font.size

        # 估算文本宽度：CJK 字符宽系数 × 字号，Latin 字符窄系数 × 字号
        text_width_pt = 0
        for ch in content:
            if ord(ch) > 127:  # CJK 字符
                text_width_pt += font_size * _WIDTH_COEFF_CJK
            else:
                text_width_pt += font_size * _WIDTH_COEFF_LATIN

        # 转换为 mm (1pt ≈ 0.3528mm)
        text_width_mm = text_width_pt * 0.3528

        # 防止 content_width 为零或负数导致除零
        safe_width = max(content_width, 1.0)

        # 计算行数
        lines = max(1, int(text_width_mm / safe_width) + 1)

        # 每行高度：字号 * 1.2（行间距）* 0.3528mm/pt
        line_height_mm = font_size * 1.2 * 0.3528

        # 总高度 = 行数 * 行高 + 上下 margin
        return lines * line_height_mm + 2.54

    # group 和其他类型
    return _DEFAULT_SHAPE_H


def _is_chapter_title(elem: Element) -> bool:
    """判断元素是否是章节标题（一级标题）

    章节标题特征：
    - 样式为 heading/accent/title/subtitle
    - 或者是大字号（>= 36pt）的文本
    - 排除短数字装饰元素（如 "01", "02" 等章节编号）
    """
    if elem.type != "text":
        return False

    content = (elem.content or "").strip()

    # 排除短数字装饰元素（如 "01", "02", "06" 等章节编号）
    if content.isdigit() and len(content) <= 3:
        return False

    # 检查样式名
    if isinstance(elem.style, str) and elem.style in ("heading", "accent", "title", "subtitle"):
        return True

    # 检查字号
    if isinstance(elem.style, dict):
        font_spec = elem.style.get("font", {})
        if isinstance(font_spec, dict) and font_spec.get("size", 18) >= 36:
            return True

    # 检查 StyleSpec
    if isinstance(elem.style, StyleSpec) and elem.style.font:
        if elem.style.font.size >= 36:
            return True

    return False


def _is_list_item(elem: Element) -> bool:
    """判断元素是否是列表项（以 • 开头的文本）"""
    if elem.type != "text":
        return False
    content = elem.content or ""
    return content.startswith("•") or content.startswith("·") or content.startswith("-")


def _is_chapter_prefix(elem: Element) -> bool:
    """判断元素是否是章节标题的前缀装饰（如 "01", "02" 等数字编号）

    这类元素应与后面的章节标题归为同一组。
    """
    if elem.type != "text":
        return False
    content = (elem.content or "").strip()
    # 纯数字且长度 <= 3（如 "01", "02", "06"）
    if content.isdigit() and len(content) <= 3:
        return True
    return False


def _group_elements_by_chapter(elements: list[Element]) -> list[list[Element]]:
    """将元素按章节分组

    分组规则：
    - 章节标题（一级标题）开始一个新的分组
    - 标题前面的装饰元素（如数字编号、分隔线）归入新分组
    - 标题后面的所有内容（直到下一个标题）都属于这个分组
    - 第一个分组可以是"前言"（标题前的内容）

    Returns:
        分组后的元素列表
    """
    if not elements:
        return [[]]

    groups: list[list[Element]] = []
    current_group: list[Element] = []
    pending: list[Element] = []  # 等待归属的前缀元素

    for elem in elements:
        if _is_chapter_title(elem):
            # 章节标题：开始新分组，pending 元素归入新分组
            if current_group:
                groups.append(current_group)
            current_group = pending + [elem]
            pending = []
        elif _is_chapter_prefix(elem) and not current_group:
            # 前缀元素且当前还没有分组内容 → 暂存到 pending
            pending.append(elem)
        elif _is_chapter_prefix(elem) and current_group:
            # 前缀元素但已有分组内容 → 也暂存到 pending
            # （可能是上一章的结尾数字，但更可能是下一章的开头编号）
            pending.append(elem)
        else:
            # 普通内容元素
            if pending:
                # 有 pending 元素，先检查它们应该归哪
                # 如果当前组已有内容，pending 可能是下一章的前缀，先保留
                current_group.extend(pending)
                pending = []
            current_group.append(elem)

    # 保存最后一个分组
    if current_group or pending:
        groups.append(current_group + pending)

    return groups if groups else [[]]


def _paginate_group(
    group: list[Element],
    content_width: float,
    max_height: float,
    spacing: float,
    padding_top: float,
) -> list[list[Element]]:
    """对单个分组进行分页

    分页规则：
    - 标题和第一个内容元素尽量在一起
    - 列表项尽量在一起
    - 如果单个元素就超出页面，单独一页
    """
    if not group:
        return [[]]

    pages: list[list[Element]] = []
    current_page: list[Element] = []
    current_height = padding_top
    last_list_break = -1  # 最近的列表项结束位置

    for i, elem in enumerate(group):
        elem_height = _estimate_element_height(elem, content_width)

        # 检查加入当前元素后是否超出页面
        would_overflow = (current_height + elem_height) > max_height

        if would_overflow and current_page:
            # 需要分页
            # 如果当前元素是列表项，且前面有列表项，尝试在列表开始前分页
            if _is_list_item(elem) and last_list_break >= 0:
                # 在列表开始前分页
                split_point = last_list_break + 1
                pages.append(current_page[:split_point])
                current_page = current_page[split_point:] + [elem]
                # 重新计算高度
                current_height = padding_top
                for r in current_page[:-1]:
                    current_height += _estimate_element_height(r, content_width) + spacing
                current_height += elem_height + spacing
            else:
                # 强制在当前位置前分页
                pages.append(current_page)
                current_page = [elem]
                current_height = padding_top + elem_height + spacing
        else:
            # 不需要分页
            current_page.append(elem)
            current_height += elem_height + spacing

        # 更新列表项结束位置
        if _is_list_item(elem):
            if not (i > 0 and _is_list_item(group[i - 1])):
                # 这是列表的第一项
                last_list_break = len(current_page) - 1

    # 最后一页
    if current_page:
        pages.append(current_page)

    return pages if pages else [[]]


def _split_elements_for_pagination(
    elements: list[Element],
    content_width: float,
    max_height: float,
    spacing: float,
    padding_top: float,
) -> list[list[Element]]:
    """将元素列表按语义分页

    分页策略：
    1. 先按章节分组（一级标题 + 后续内容）
    2. 对每组内容进行分页
    3. 章节间不混排

    Args:
        elements: 原始元素列表
        content_width: 内容宽度（mm）
        max_height: 最大可用高度（mm）
        spacing: 元素间距（mm）
        padding_top: 上边距（mm）

    Returns:
        分页后的元素列表（每页一个列表）
    """
    if not elements:
        return [[]]

    # 第一步：按章节分组
    chapter_groups = _group_elements_by_chapter(elements)

    # 第二步：对每组进行分页
    pages: list[list[Element]] = []
    for group in chapter_groups:
        group_pages = _paginate_group(group, content_width, max_height, spacing, padding_top)
        pages.extend(group_pages)

    return pages if pages else [[]]


def compile_slide(
    slide: Slide,
    global_styles: dict[str, StyleSpec],
    doc_ir_styles: dict[str, IRStyle],
    theme_name: str,
    index: int,
) -> list[IRNode]:
    """将 DSL Slide 编译为 IRNode 列表 (NodeType.SLIDE)

    支持 stack 布局模式：layout: stack
    - 子元素自动从上到下排列，不需要手动指定 y 坐标
    - 支持 spacing（间距）、padding_top/left（内边距）、content_width（内容宽度）
    - 未指定 position 的元素自动进入 stack 流
    - 指定了 position 的元素不受 stack 影响（绝对定位）
    - 内容超出时自动分页，保持语义连贯

    Returns:
        IRNode 列表（可能包含多个 slide，如果发生了自动分页）
    """
    # 检测 slide 级别的 stack 布局
    slide_stack = slide.layout == "stack"
    slide_elements = _ordered_slide_elements(slide)
    slide_extra = slide.background or {}
    if isinstance(slide_extra, dict):
        stack_spacing = float(slide_extra.get("spacing", 8))  # 默认 8mm 间距
        padding_top = float(slide_extra.get("padding_top", 15))  # 默认上边距 15mm
        padding_left = float(slide_extra.get("padding_left", 30))  # 默认左边距 30mm
        content_width = float(slide_extra.get("content_width", 194))  # 默认内容宽度 194mm
    else:
        stack_spacing = 8
        padding_top = 15
        padding_left = 30
        content_width = 194

    # 自动分页：stack 布局且没有绝对定位元素时
    if slide_stack:
        # 检查是否有绝对定位元素
        has_absolute = any(e.position is not None for e in slide_elements)

        if not has_absolute:
            # 预估总高度
            total_height = padding_top
            for elem in slide_elements:
                total_height += _estimate_element_height(elem, content_width) + stack_spacing

            # 如果超出页面高度，进行分页
            if total_height > SLIDE_HEIGHT_MM:
                element_pages = _split_elements_for_pagination(
                    slide_elements, content_width, SLIDE_HEIGHT_MM, stack_spacing, padding_top
                )
            else:
                element_pages = [slide_elements]
        else:
            element_pages = [slide_elements]
    else:
        element_pages = [slide_elements]

    # 编译每一页
    slides = []
    for page_idx, page_elements in enumerate(element_pages):
        children = []
        stack_cursor_y = padding_top

        for i, elem in enumerate(page_elements):
            # stack 布局：为没有 position 的元素自动计算位置
            if slide_stack and elem.position is None:
                # 估算元素高度
                default_h = _estimate_element_height(elem, content_width)

                # 处理 extra.center → position.center
                extra_copy = dict(elem.extra)
                center_flag = extra_copy.pop("center", False)

                auto_pos = PositionSpec(
                    x=padding_left,
                    y=stack_cursor_y,
                    width=content_width,
                    height=default_h,
                    center=bool(center_flag),
                )
                elem = Element(
                    type=elem.type,
                    content=elem.content,
                    format=getattr(elem, "format", "plain"),
                    source=elem.source,
                    style=elem.style,
                    style_ref=elem.style_ref,
                    position=auto_pos,
                    data_ref=elem.data_ref,
                    chart_type=elem.chart_type,
                    query=elem.query,
                    prompt=elem.prompt,
                    size=elem.size,
                    opacity=elem.opacity,
                    filter=elem.filter,
                    animation=elem.animation,
                    children=elem.children,
                    extra=extra_copy,
                )

            ir_elem = compile_element(
                elem, global_styles, doc_ir_styles, theme_name,
                path=f"slide[{index}]/{elem.type}[{i}]",
            )
            children.append(ir_elem)

            # stack 布局：更新游标 y
            if slide_stack and ir_elem.position:
                child_h = ir_elem.position.height_mm
                if child_h <= 0:
                    child_h = _estimate_element_height(
                        page_elements[i], content_width
                    )
                stack_cursor_y += child_h + stack_spacing

        extra = {}
        if slide.background:
            extra["background"] = slide.background
        if slide.background_board:
            extra["background_board"] = slide.background_board
        if slide.layers:
            extra["layers"] = list(slide.layers.keys())
        if slide.transition:
            extra["transition"] = slide.transition
        # 布局引擎配置透传到 IR
        if slide.layout_mode:
            extra["layout_mode"] = slide.layout_mode
        elif slide.layout and slide.layout not in ("blank", "stack", "title"):
            # 语义布局名称（如 card_grid_2x2）自动作为 layout_mode 传递
            extra["layout_mode"] = slide.layout
        if slide.grid:
            extra["grid"] = slide.grid
        if slide.flex:
            extra["flex"] = slide.flex
        if slide.constraints:
            extra["constraints"] = slide.constraints
        if slide.card_container:
            extra["card_container"] = True

        slide_node = IRNode(
            node_type=NodeType.SLIDE,
            content=None,
            position=IRPosition(x_mm=0, y_mm=0, width_mm=SLIDE_WIDTH_MM, height_mm=SLIDE_HEIGHT_MM),
            children=children,
            extra=extra,
            source_path=f"slide[{index}]" + (f".{page_idx}" if page_idx > 0 else ""),
        )
        slides.append(slide_node)

    return slides


# ============================================================
# 文档编译（入口）
# ============================================================

def compile_document(doc: Document) -> IRDocument:
    """将 DSL Document 编译为 IRDocument"""
    # 处理 style_preset — 从设计令牌生成默认样式
    preset_name = doc.style_preset or ""
    preset_styles = {}
    if preset_name:
        try:
            from ..design.tokens import PALETTE, TYPOGRAPHY, get_font_family
            pal = PALETTE.get(preset_name, {})
            if pal:
                # 从预设生成基础样式（字体根据主题自动选择）
                preset_styles["title"] = IRStyle(
                    font_family=get_font_family(preset_name, "cover_title"),
                    font_size=TYPOGRAPHY["cover_title"].size,
                    font_weight=TYPOGRAPHY["cover_title"].weight,
                    font_color=pal.get("text", "#0F172A"),
                )
                preset_styles["heading"] = IRStyle(
                    font_family=get_font_family(preset_name, "heading"),
                    font_size=TYPOGRAPHY["heading"].size,
                    font_weight=TYPOGRAPHY["heading"].weight,
                    font_color=pal.get("text", "#0F172A"),
                )
                preset_styles["body"] = IRStyle(
                    font_family=get_font_family(preset_name, "body"),
                    font_size=TYPOGRAPHY["body"].size,
                    font_weight=TYPOGRAPHY["body"].weight,
                    font_color=pal.get("text", "#0F172A"),
                )
                preset_styles["caption"] = IRStyle(
                    font_family=get_font_family(preset_name, "caption"),
                    font_size=TYPOGRAPHY["caption"].size,
                    font_weight=TYPOGRAPHY["caption"].weight,
                    font_color=pal.get("text_secondary", "#64748B"),
                )
                preset_styles["accent"] = IRStyle(
                    font_family=get_font_family(preset_name, "body"),
                    font_size=TYPOGRAPHY["body"].size,
                    font_weight=600,
                    font_color=pal.get("primary", "#2563EB"),
                )
        except ImportError:
            pass  # design 模块不可用时跳过

    # 编译全局样式 → IR 样式表（预设样式作为底层，用户样式覆盖）
    doc_ir_styles = dict(preset_styles)  # 预设作为默认
    for name, style_spec in doc.styles.items():
        compiled = compile_style(style_spec)
        if compiled:
            # 用户样式覆盖预设样式（只覆盖非 None 字段）
            if name in doc_ir_styles:
                base = doc_ir_styles[name]
                doc_ir_styles[name] = _merge_styles(base, compiled)
            else:
                doc_ir_styles[name] = compiled

    # 幻灯片类型自动增强：当 auto_enhance=True 且有 style_preset 时，为无背景的幻灯片注入默认背景
    if doc.auto_enhance and preset_name:
        _auto_enhance_slides(doc.slides, preset_name)

    # 编译幻灯片
    slides = []
    for i, slide in enumerate(doc.slides):
        slide_nodes = compile_slide(slide, doc.styles, doc_ir_styles, doc.theme, i)
        slides.extend(slide_nodes)  # compile_slide 返回列表（可能分页）

    return IRDocument(
        version=doc.version,
        doc_type=doc.type.value,
        theme=doc.theme,
        title=doc.title,
        style_preset=preset_name,
        styles=doc_ir_styles,
        data={k: v for k, v in doc.data.items()},
        children=slides,
        raw_dsl=doc.raw,
    )


def _parse_mm(val) -> float:
    """将 '254mm' / '254' / 254 等转为 float"""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    if s.endswith("mm"):
        s = s[:-2]
    try:
        return float(s)
    except ValueError:
        return 0.0


def _has_fullslide_bg(slide) -> bool:
    """检查幻灯片是否已有全幅背景矩形（覆盖整个画布的 shape）"""
    for elem in slide.elements:
        if elem.type != "shape":
            continue
        pos = elem.position
        if pos is None:
            continue
        shape_type = getattr(elem, "extra", {}).get("shape_type", "rectangle")
        if shape_type not in ("rectangle", "rounded_rectangle"):
            continue
        if (_parse_mm(pos.x) <= 0 and _parse_mm(pos.y) <= 0
                and _parse_mm(pos.width) >= 250 and _parse_mm(pos.height) >= 140):
            return True
    return False


def _auto_enhance_slides(slides: list, preset_name: str) -> None:
    """幻灯片类型自动增强 — 为无背景的幻灯片注入设计预设背景

    根据幻灯片位置和内容自动匹配合适的背景：
      - 第一页（封面）：渐变或强调色背景
      - 中间页（内容）：简洁背景（纯色 + 点缀）
      - 最后一页（收尾）：呼应封面的背景

    只对没有 background/background_board 的幻灯片生效。
    """
    from ..design.background_presets import (
        business_clean, gradient_spotlight, subtle_texture, split_accent
    )
    from ..design.tokens import PALETTE

    if not slides:
        return

    # 判断幻灯片类型（封面、内容、收尾）
    total = len(slides)
    for i, slide in enumerate(slides):
        # 跳过已有背景的幻灯片（background/background_board 或全幅背景矩形）
        if slide.background or slide.background_board:
            continue
        if _has_fullslide_bg(slide):
            continue

        if total == 1:
            # 单页演示：用简洁风格
            slide.background_board = business_clean(palette=preset_name, accent_bar=True)
        elif i == 0:
            # 封面页
            if preset_name in ("tech", "creative", "sunset", "ocean", "forest"):
                slide.background_board = gradient_spotlight(palette=preset_name)
            else:
                slide.background_board = business_clean(palette=preset_name, accent_bar=True)
            _inject_freeform_decor(slide, preset_name, role="cover")
        elif i == total - 1:
            # 收尾页：与封面呼应
            if preset_name in ("tech", "creative", "sunset", "ocean", "forest"):
                slide.background_board = gradient_spotlight(palette=preset_name)
            else:
                slide.background_board = business_clean(palette=preset_name, accent_bar=True)
            _inject_freeform_decor(slide, preset_name, role="closing")
        else:
            # 内容页：极简背景，不影响内容可读性
            slide.background = {"color": PALETTE.get(preset_name, PALETTE["corporate"])["bg"]}


def _inject_freeform_decor(slide, preset_name: str, role: str = "cover") -> None:
    """为幻灯片注入自由贝塞尔装饰元素"""
    from ..design.freeform_shapes import blob_shape, ink_splash
    from ..design.tokens import get_palette

    pal = get_palette(preset_name)
    accent = pal.get("accent", pal.get("primary", "#3B82F6"))

    # 根据主题选择装饰风格
    if preset_name == "chinese_ink":
        path = ink_splash(seed=hash(preset_name) % 100, cx=80, cy=70, r=30)
        opacity = 0.08
    elif preset_name in ("tech", "creative"):
        path = blob_shape(seed=42, cx=82, cy=65, r=25, points=5, jitter=0.3)
        opacity = 0.06
    elif preset_name in ("warm", "morandi"):
        path = blob_shape(seed=7, cx=78, cy=72, r=28, points=7, jitter=0.2)
        opacity = 0.05
    else:
        path = blob_shape(seed=3, cx=85, cy=75, r=18, points=5, jitter=0.2)
        opacity = 0.04

    slide.elements.append(Element(
        type="shape",
        position=PositionSpec(x="60", y="40", width="35", height="35"),
        style=StyleSpec(fill=FillSpec(color=accent, opacity=opacity)),
        opacity=opacity,
        extra={"shape_type": "freeform", "freeform_path": path},
    ))


def _merge_styles(base: IRStyle, override: IRStyle) -> IRStyle:
    """合并两个 IRStyle，override 中非 None 字段覆盖 base"""
    from dataclasses import fields, replace as dc_replace
    merged = base
    for f in fields(IRStyle):
        val = getattr(override, f.name)
        if val is not None:
            merged = dc_replace(merged, **{f.name: val})
    return merged
