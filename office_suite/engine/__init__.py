"""计算引擎层 — 布局 / 样式 / 文本 / 媒体 / 图表"""

from .layout import Solver, GridLayout, FlexLayout
from .style import hex_to_oklch, oklch_to_hex, TypographySpec
from .text import TextTransform, RichDocument, PathTextConfig
from .media import calculate_size, parse_svg, SVGInfo
from .chart import list_engines, render_chart_image

__all__ = [
    "Solver", "GridLayout", "FlexLayout",
    "hex_to_oklch", "oklch_to_hex", "TypographySpec",
    "TextTransform", "RichDocument", "PathTextConfig",
    "calculate_size", "parse_svg", "SVGInfo",
    "list_engines", "render_chart_image",
]
