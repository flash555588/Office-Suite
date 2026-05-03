"""渲染器能力映射表 — IR 特性 → 渲染器能力

设计方案第八章：渲染器能力声明。

每个渲染器声明自己支持的 IR 特性，不支持的特性自动降级。
本模块汇总所有渲染器的能力，提供统一查询接口。

能力分类：
  - 节点类型：text, image, shape, chart, table, group, video, diagram
  - 布局模式：absolute, relative, grid, flex
  - 文本变换：arch, wave, circle, slant_up, etc.
  - 动画效果：fade_in, slide_up, zoom_in, etc.
  - 视觉效果：shadow, glow, gradient_fill, duotone
"""

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# 渲染器能力定义
# ============================================================

PPTX_CAPABILITIES = {
    "node_types": {"text", "image", "shape", "chart", "table", "group",
                   "component", "semantic_icon", "video", "diagram"},
    "layout_modes": {"absolute", "relative"},
    "content_formats": {"plain", "markdown", "latex", "rich"},
    "text_transforms": {
        "arch", "arch_up", "arch_down", "wave", "wave_2", "circle",
        "slant_up", "slant_down", "triangle", "chevron_up", "chevron_down",
        "button", "deflate", "inflate", "fade_up", "fade_down", "plain",
    },
    "animations": {
        "fade_in", "fade_out", "slide_up", "slide_down", "slide_left", "slide_right",
        "zoom_in", "zoom_out", "fly_in", "wipe", "blinds", "wheel", "spin",
        "pulse", "shake", "glow_pulse", "breathe", "float",
    },
    "effects": {"shadow", "glow", "gradient_fill", "reflection", "soft_edge"},
    "chart_types": {
        # 原生 python-pptx 图表
        "bar", "bar_stacked", "column", "column_stacked",
        "line", "line_marked", "pie", "area", "scatter",
        "doughnut", "radar", "bubble", "stock", "surface",
        # 外部引擎图表（渲染为 PNG 嵌入）
        "heatmap", "box", "violin", "histogram", "density",
        "funnel", "sunburst", "treemap",
    },
    "chart_engines": {"native", "matplotlib", "plotly", "vega-lite", "ggplot2", "pgfplots"},
    "fallbacks": {
        "video": "image",       # 视频 → 图片占位
        "diagram": "image",     # 图表 → 图片
        "audio": "text",        # 音频 → 文字描述
        "code": "text",         # 代码 → 文本
        "3d_model": "text",     # 3D 模型 → 文字描述
        "map": "text",          # 地图 → 文字描述
        "arch": "plain",        # 艺术字 → 普通文本
    },
}

DOCX_CAPABILITIES = {
    "node_types": {"text", "image", "table", "shape", "component", "semantic_icon"},
    "layout_modes": {"absolute", "relative"},
    "content_formats": {"plain", "markdown", "rich"},
    "text_transforms": set(),   # 不支持艺术字
    "animations": set(),        # 不支持动画
    "effects": {"shadow"},
    "chart_types": set(),       # 不直接支持图表
    "fallbacks": {
        "chart": "table",       # 图表 → 表格
        "shape": "text",        # 形状 → 文本
        "video": "text",        # 视频 → 文字描述
        "diagram": "text",      # 图表 → 文字描述
    },
}

XLSX_CAPABILITIES = {
    "node_types": {"table", "chart", "text", "component"},
    "layout_modes": {"absolute"},
    "content_formats": {"plain"},
    "text_transforms": set(),
    "animations": set(),
    "effects": set(),
    "chart_types": {"bar", "column", "line", "pie", "scatter", "doughnut", "radar"},
    "fallbacks": {
        "shape": "text",
        "image": "text",
        "video": "text",
    },
}

PDF_CAPABILITIES = {
    "node_types": {"text", "image", "shape", "table", "chart", "component"},
    "layout_modes": {"absolute", "relative"},
    "content_formats": {"plain", "markdown", "latex"},
    "text_transforms": set(),
    "animations": set(),
    "effects": {"shadow"},
    "chart_types": {"bar", "column", "line", "pie", "area", "scatter", "doughnut"},
    "fallbacks": {
        "video": "image",
        "diagram": "image",
    },
}

HTML_CAPABILITIES = {
    "node_types": {"text", "image", "shape", "table", "chart", "group",
                   "component", "semantic_icon", "video", "diagram"},
    "layout_modes": {"absolute", "relative", "flex", "grid"},
    "content_formats": {"plain", "markdown", "latex", "rich"},
    "text_transforms": {"arch", "wave", "slant_up", "slant_down"},
    "animations": {
        "fade_in", "fade_out", "slide_up", "slide_down", "slide_left", "slide_right",
        "zoom_in", "zoom_out", "pulse", "shake",
    },
    "effects": {"shadow", "glow", "gradient_fill", "blur"},
    "chart_types": {"bar", "column", "line", "pie", "area", "scatter", "doughnut", "radar"},
    "fallbacks": {
        "video": "image",
    },
}


# ============================================================
# 统一查询
# ============================================================

RENDERER_CAPABILITIES: dict[str, dict[str, set[str]]] = {
    "pptx": PPTX_CAPABILITIES,
    "docx": DOCX_CAPABILITIES,
    "xlsx": XLSX_CAPABILITIES,
    "pdf": PDF_CAPABILITIES,
    "html": HTML_CAPABILITIES,
}


def get_capabilities(renderer: str) -> dict[str, set[str]]:
    """获取渲染器的全部能力

    Args:
        renderer: 渲染器名称

    Returns:
        能力字典
    """
    return RENDERER_CAPABILITIES.get(renderer, {})


def supports(renderer: str, category: str, feature: str) -> bool:
    """检查渲染器是否支持某特性

    Args:
        renderer: 渲染器名称
        category: 能力类别（node_types, animations, effects 等）
        feature: 特性名

    Returns:
        是否支持
    """
    caps = RENDERER_CAPABILITIES.get(renderer, {})
    features = caps.get(category, set())
    return feature in features


def get_fallback(renderer: str, feature: str) -> str | None:
    """获取特性的降级方案

    Args:
        renderer: 渲染器名称
        feature: 不支持的特性

    Returns:
        降级特性名，或 None（无法降级）
    """
    caps = RENDERER_CAPABILITIES.get(renderer, {})
    fallbacks = caps.get("fallbacks", {})
    return fallbacks.get(feature)


def get_renderer_for_feature(category: str, feature: str) -> list[str]:
    """查找支持某特性的所有渲染器

    Args:
        category: 能力类别
        feature: 特性名

    Returns:
        支持该特性的渲染器列表
    """
    result = []
    for renderer, caps in RENDERER_CAPABILITIES.items():
        if feature in caps.get(category, set()):
            result.append(renderer)
    return result


def compare_renderers(renderer1: str, renderer2: str) -> dict[str, dict[str, set[str]]]:
    """比较两个渲染器的能力差异

    Returns:
        {"only_in_1": {...}, "only_in_2": {...}, "common": {...}}
    """
    caps1 = RENDERER_CAPABILITIES.get(renderer1, {})
    caps2 = RENDERER_CAPABILITIES.get(renderer2, {})

    all_categories = set(list(caps1.keys()) + list(caps2.keys()))

    only_in_1: dict[str, set[str]] = {}
    only_in_2: dict[str, set[str]] = {}
    common: dict[str, set[str]] = {}

    for cat in all_categories:
        f1 = caps1.get(cat, set())
        f2 = caps2.get(cat, set())
        only_in_1[cat] = f1 - f2
        only_in_2[cat] = f2 - f1
        common[cat] = f1 & f2

    return {"only_in_1": only_in_1, "only_in_2": only_in_2, "common": common}
