"""PPTX 形状渲染 — 形状创建、填充、边框、类型映射"""

from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from ...ir.types import IRNode, IRPosition, IRStyle


# 形状名称 → MSO_SHAPE 枚举
_SHAPE_MAP = {
    "rectangle": MSO_SHAPE.RECTANGLE,
    "rounded_rectangle": MSO_SHAPE.ROUNDED_RECTANGLE,
    "circle": MSO_SHAPE.OVAL,
    "oval": MSO_SHAPE.OVAL,
    "triangle": MSO_SHAPE.ISOSCELES_TRIANGLE,
    "diamond": MSO_SHAPE.DIAMOND,
    "arrow": MSO_SHAPE.RIGHT_ARROW,
    "star": MSO_SHAPE.STAR_5_POINT,
    "hexagon": MSO_SHAPE.HEXAGON,
    "pentagon": MSO_SHAPE.PENTAGON,
    "chevron": MSO_SHAPE.CHEVRON,
    "cross": MSO_SHAPE.CROSS,
}


def get_shape_type(name: str):
    """形状名称 → MSO_SHAPE 枚举"""
    return _SHAPE_MAP.get(name, MSO_SHAPE.RECTANGLE)


def render_shape(renderer, slide, node: IRNode, doc):
    """渲染形状元素"""
    from .animation import apply_animations

    pos = node.position or IRPosition()
    style = renderer._resolve_style(node, doc)

    left, top, width, height = renderer._pos_to_emu(pos)
    shape_type = node.extra.get("shape_type", "rectangle")
    mso_shape = get_shape_type(shape_type)

    shape = slide.shapes.add_shape(mso_shape, left, top, width, height)

    apply_shape_fill(renderer, shape, style, node)
    apply_shape_border(shape, node)

    if node.content:
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = node.content
        if style:
            renderer._apply_text_style(p, style)

    if node.animations:
        apply_animations(slide, shape, node.animations)


def apply_shape_fill(renderer, shape, style: IRStyle | None, node: IRNode):
    """应用形状填充（纯色 / 渐变 / 透明度）"""
    from .style import apply_gradient_fill, apply_shadow

    if style and style.fill_gradient:
        shape.fill.gradient()
        apply_gradient_fill(shape.fill, style.fill_gradient)
    elif style and style.fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = renderer._hex_to_rgb(style.fill_color)
        if style.fill_opacity is not None and style.fill_opacity < 1.0:
            shape.fill.fore_color.brightness = 0
    else:
        shape.fill.background()

    if style and style.shadow:
        apply_shadow(shape, style.shadow)


def apply_shape_border(shape, node: IRNode):
    """应用形状边框"""
    outline = node.extra.get("outline")
    if outline:
        shape.line.color.rgb = _hex_to_rgb(outline.get("color", "#000000"))
        shape.line.width = Pt(outline.get("width", 1))
        dash = outline.get("dash")
        if dash == "solid":
            shape.line.dash_style = 1
        elif dash == "dashed":
            shape.line.dash_style = 4
        elif dash == "dotted":
            shape.line.dash_style = 2
    else:
        shape.line.fill.background()


def _hex_to_rgb(hex_str: str) -> RGBColor:
    """HEX → RGBColor"""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 8:
        hex_str = hex_str[:6]
    if len(hex_str) != 6:
        return RGBColor(0, 0, 0)
    try:
        return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except ValueError:
        return RGBColor(0, 0, 0)
