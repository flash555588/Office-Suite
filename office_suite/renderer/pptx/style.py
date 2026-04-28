"""PPTX 样式辅助 — 主题色解析、文本样式、阴影、渐变、文本变换"""

from dataclasses import replace as dc_replace
from typing import Any

from pptx.util import Pt
from pptx.dml.color import RGBColor

from ...ir.types import IRDocument, IRNode, IRStyle


# 内置主题色表（对应 Office 默认主题 "Office Theme"）
THEME_COLORS: dict[str, str] = {
    "dk1": "#000000", "lt1": "#FFFFFF",
    "dk2": "#1F3864", "lt2": "#E7E6E6",
    "accent1": "#4472C4", "accent2": "#ED7D31",
    "accent3": "#A9D18E", "accent4": "#FFC000",
    "accent5": "#5B9BD5", "accent6": "#70AD47",
    "hlink": "#0563C1", "folHlink": "#954F72",
    "primary": "#4472C4", "secondary": "#ED7D31",
    "success": "#70AD47", "warning": "#FFC000",
    "danger": "#FF0000", "info": "#5B9BD5",
    "light": "#E7E6E6", "dark": "#1F3864",
}

# 级联后的默认回退值
STYLE_DEFAULTS = {
    "font_family": "Microsoft YaHei UI",
    "font_size": 18,
    "font_weight": 400,
    "font_italic": False,
    "font_color": "#000000",
    "fill_opacity": 1.0,
}

# WordArt 文本变换映射
_TRANSFORM_MAP = {
    "arch": "textArchDown", "arch_up": "textArchUp",
    "wave": "textWave1", "circle": "textCircle",
    "slant_up": "textSlantUp", "slant_down": "textSlantDown",
    "triangle": "textTriangle", "chevron_up": "textChevronUp",
    "chevron_down": "textChevronDown", "button": "textButton",
    "deflate": "textDeflate", "inflate": "textInflate",
    "fade_up": "textFadeUp", "fade_down": "textFadeDown",
}


def resolve_style(renderer, node: IRNode, doc: IRDocument) -> IRStyle | None:
    """解析节点样式

    编译器已做级联，这里直接使用 node.style。
    若样式含 theme_ref，将其解析为实际颜色并回填。
    """
    style = node.style
    if style is None:
        if node.style_ref and node.style_ref in doc.styles:
            style = doc.styles[node.style_ref]
    if style is None:
        return None

    if style.theme_ref:
        resolved_color = THEME_COLORS.get(style.theme_ref)
        if resolved_color:
            style = dc_replace(
                style,
                font_color=style.font_color or resolved_color,
                fill_color=style.fill_color or resolved_color,
                theme_ref=None,
            )

    return style


def style_val(style: IRStyle, field: str):
    """获取样式字段值，None 时回退到默认"""
    val = getattr(style, field, None)
    if val is None:
        return STYLE_DEFAULTS.get(field)
    return val


def apply_text_style(paragraph, style: IRStyle):
    """应用文本样式到段落"""
    font = paragraph.font
    family = style_val(style, "font_family")
    size = style_val(style, "font_size")
    weight = style_val(style, "font_weight")
    italic = style_val(style, "font_italic")
    color = style_val(style, "font_color")

    if family:
        font.name = family
    if size:
        font.size = Pt(size)
    if weight:
        font.bold = weight >= 700
    if italic is not None:
        font.italic = italic
    if color:
        font.color.rgb = hex_to_rgb(color)


def apply_shadow(shape, shadow: dict[str, Any]):
    """通过 DrawingML XML 注入阴影效果"""
    from lxml import etree

    a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

    sp_pr = getattr(shape._element, 'spPr', None)
    if sp_pr is None:
        for ns in (
            'http://schemas.openxmlformats.org/presentationml/2006/main',
            'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
        ):
            sp_pr = shape._element.find(f'.//{{{ns}}}spPr')
            if sp_pr is not None:
                break
    if sp_pr is None:
        return

    effect_lst = sp_pr.find(f'{{{a_ns}}}effectLst')
    if effect_lst is None:
        effect_lst = etree.SubElement(sp_pr, f'{{{a_ns}}}effectLst')

    for old in effect_lst.findall(f'{{{a_ns}}}outerShdw'):
        effect_lst.remove(old)

    color_hex = shadow.get("color", "#000000").lstrip("#")
    opacity = shadow.get("opacity", 0.5)
    blur_pt = shadow.get("blur", 4)
    offset_x = shadow.get("offset_x", 3)
    offset_y = shadow.get("offset_y", 3)
    angle_deg = shadow.get("angle", 45)

    blur_emu = int(blur_pt * 12700)
    dist_emu = int((offset_x ** 2 + offset_y ** 2) ** 0.5 * 12700)
    dir_60k = int(angle_deg * 60000)
    alpha_pct = int(opacity * 100000)

    outer_shdw = etree.SubElement(effect_lst, f'{{{a_ns}}}outerShdw')
    outer_shdw.set('blurRad', str(blur_emu))
    outer_shdw.set('dist', str(dist_emu))
    outer_shdw.set('dir', str(dir_60k))
    outer_shdw.set('algn', 'tl')
    outer_shdw.set('rotWithShape', '0')

    srgb_clr = etree.SubElement(outer_shdw, f'{{{a_ns}}}srgbClr')
    srgb_clr.set('val', color_hex if len(color_hex) == 6 else '000000')
    alpha = etree.SubElement(srgb_clr, f'{{{a_ns}}}alpha')
    alpha.set('val', str(alpha_pct))


def apply_gradient_fill(fill, gradient: dict[str, Any]):
    """应用渐变填充（linear / radial）"""
    fill.gradient()
    stops = gradient.get("stops", ["#000000", "#FFFFFF"])
    angle = gradient.get("angle", 0)

    for i, color_hex in enumerate(stops):
        position = i / max(len(stops) - 1, 1)
        if i < len(fill.gradient_stops):
            fill.gradient_stops[i].color.rgb = hex_to_rgb(color_hex)
            fill.gradient_stops[i].position = position
        else:
            break

    if gradient.get("type") == "linear":
        try:
            fill.gradient_angle = angle
        except AttributeError:
            pass


def apply_text_warp(shape, text_effect: dict[str, Any]):
    """应用 WordArt 文本变换 — 通过 Oxml 注入 presetTextWarp"""
    from lxml import etree

    a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'

    tx_body = shape._element.find(f'.//{{{a_ns}}}txBody')
    if tx_body is None:
        return

    body_pr = tx_body.find(f'{{{a_ns}}}bodyPr')
    if body_pr is None:
        body_pr = etree.SubElement(tx_body, f'{{{a_ns}}}bodyPr')

    transform_type = text_effect.get("transform", text_effect.get("type", "plain"))
    preset = _TRANSFORM_MAP.get(transform_type, "textPlain")

    prst_tx_warp = etree.SubElement(body_pr, f'{{{a_ns}}}prstTxWarp')
    prst_tx_warp.set('prst', preset)

    av_lst = etree.SubElement(prst_tx_warp, f'{{{a_ns}}}avLst')

    bend = text_effect.get("bend", 0)
    if bend != 0:
        gd = etree.SubElement(av_lst, f'{{{a_ns}}}gd')
        gd.set('name', 'adj')
        gd.set('fmla', f'val {int(bend * 1000)}')


def hex_to_rgb(hex_str: str) -> RGBColor:
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
