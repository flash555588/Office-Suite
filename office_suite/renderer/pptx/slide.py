"""PPTX 幻灯片级渲染 — 创建、背景、布局映射"""

from typing import Any

from pptx.util import Mm

from ...ir.types import IRNode, IRDocument

# 标准 16:9 幻灯片尺寸 (mm)
SLIDE_WIDTH_MM = 254.0
SLIDE_HEIGHT_MM = 142.875

# 布局名称 → python-pptx 默认模板索引
_LAYOUT_MAP = {
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


def get_layout_index(name: str) -> int:
    """布局名称 → 幻灯片布局索引"""
    return _LAYOUT_MAP.get(name, 6)


def render_slide(renderer, slide_node: IRNode, doc: IRDocument):
    """渲染单张幻灯片

    母版布局索引（python-pptx 默认模板）：
      0  = Title Slide
      1  = Title and Content
      6  = Blank
    """
    layout_name = slide_node.extra.get("layout", "blank")
    layout_idx = get_layout_index(layout_name)
    slide_layout = renderer._prs.slide_layouts[layout_idx]
    slide = renderer._prs.slides.add_slide(slide_layout)

    bg_data = slide_node.extra.get("background")
    if bg_data:
        set_background(renderer, slide, bg_data)

    for elem_node in slide_node.children:
        renderer._render_element(slide, elem_node, doc)


def set_background(renderer, slide, bg_data: dict[str, Any]):
    """设置幻灯片背景

    支持：
      - 纯色: { color: "#RRGGBB" }
      - 线性渐变: { gradient: { type: linear, angle: 135, stops: [...] } }
    """
    fill = slide.background.fill
    fill.solid()

    gradient = bg_data.get("gradient")
    if gradient:
        from .style import apply_gradient_fill
        apply_gradient_fill(fill, gradient)
    elif "color" in bg_data:
        fill.fore_color.rgb = renderer._hex_to_rgb(bg_data["color"])
