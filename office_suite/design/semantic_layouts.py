"""语义布局预设 — 将布局模式名称映射为具体布局引擎配置

包含两部分：
  1. 手写语义布局（SKILL.md 10 种，向后兼容）
  2. 参数化生成布局（1000+，由 layout_generator 自动生成）

用法：
    from office_suite.design.semantic_layouts import resolve_semantic_layout
    config = resolve_semantic_layout("card_grid_2x2")  # 手写语义名
    config = resolve_semantic_layout("g3x2g4d")         # 生成器名称

调用时机：
    renderer/layout_resolver.py::LayoutResolver.resolve_children() 在检测到
    语义布局名称时，调用本模块注入具体 grid/flex 配置。

DSL 中的 layout 字段值：
  - 绝对定位引擎名: absolute / relative
  - 布局引擎名:     grid / flex / constraint
  - 手写语义名:     card_grid_2x2 / split_50_50 / cover_center / ...
  - 生成器名称:     g3x2g4d / fd_r5050g8 / stats_4 / feature_3x2 / ...
"""

from __future__ import annotations

from typing import Any

from ..constants import SLIDE_HEIGHT_MM as _SLIDE_H

# ============================================================
# 手写语义布局（SKILL.md 原有 12 种，保持向后兼容）
# ============================================================
_TOP_MARGIN = 16.0
_BOTTOM_MARGIN = 12.0
_LEFT_MARGIN = 25.0
_RIGHT_MARGIN = 25.0
_CARD_GAP = 4.0
_DEFAULT_MARGIN = (_TOP_MARGIN, _RIGHT_MARGIN, _BOTTOM_MARGIN, _LEFT_MARGIN)


def _grid_card_height(rows: int) -> float:
    usable = _SLIDE_H - _TOP_MARGIN - _BOTTOM_MARGIN - _CARD_GAP * (rows - 1)
    return max(usable / rows, 20.0)


SEMANTIC_LAYOUTS: dict[str, dict[str, Any]] = {
    "card_grid_2x2": {"mode": "grid", "grid": {"columns": 2, "gutter": 4.0, "row_height": _grid_card_height(2), "margin": _DEFAULT_MARGIN}},
    "card_grid_3x2": {"mode": "grid", "grid": {"columns": 3, "gutter": 4.0, "row_height": _grid_card_height(2), "margin": _DEFAULT_MARGIN}},
    "card_row_4":    {"mode": "grid", "grid": {"columns": 4, "gutter": 4.0, "row_height": _grid_card_height(1), "margin": _DEFAULT_MARGIN}},
    "three_column":  {"mode": "grid", "grid": {"columns": 3, "gutter": 4.0, "row_height": _grid_card_height(1), "margin": _DEFAULT_MARGIN}},
    "timeline_h6":   {"mode": "grid", "grid": {"columns": 6, "gutter": 2.0, "row_height": _grid_card_height(2), "margin": _DEFAULT_MARGIN}},
    "split_50_50":   {"mode": "flex", "flex": {"direction": "row", "justify": "start", "align": "stretch", "gap": 8.0, "margin": _DEFAULT_MARGIN}},
    "hero_card_left":{"mode": "flex", "flex": {"direction": "row", "justify": "start", "align": "stretch", "gap": 8.0, "margin": _DEFAULT_MARGIN}},
    "panel_with_grid":{"mode": "grid", "grid": {"columns": 12, "gutter": 2.0, "row_height": _grid_card_height(1), "margin": _DEFAULT_MARGIN}},
    "title_body":    {"mode": "grid", "grid": {"columns": 1, "gutter": 4.0, "row_height": _SLIDE_H - _TOP_MARGIN - _BOTTOM_MARGIN, "margin": _DEFAULT_MARGIN}},
    "cover_center":  {"mode": "absolute"},
    "quote":         {"mode": "absolute"},
    "stats_row":     {"mode": "grid", "grid": {"columns": 3, "gutter": 4.0, "row_height": _grid_card_height(1), "margin": _DEFAULT_MARGIN}},

    # ── Bento Grid 预设 (8 种) ──────────────────────────────
    # 使用 12 列 grid，子元素通过 extra.grid 指定 column/span/row
    # 不等高不等宽的混合 cell 组合

    # hero_sidebar: 左 8 列主区 + 右 4 列侧栏（上下两行）
    # 子元素: [主区(8×2), 侧栏上(4×1), 侧栏下(4×1)]
    "hero_sidebar": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},

    # feature_showcase: 顶部标题行(全宽) + 3 个特性卡片(4列×1行)
    # 子元素: [标题(12×1), 卡片1(4×1), 卡片2(4×1), 卡片3(4×1)]
    "feature_showcase": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},

    # data_dashboard: KPI 行(3×4列) + 图表(8列×1行) + 注释(4列×1行)
    # 子元素: [KPI1(4×1), KPI2(4×1), KPI3(4×1), 图表(8×1), 注释(4×1)]
    "data_dashboard": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},

    # timeline_vertical: 纵向时间轴，2 列布局（标签列 + 内容列）
    # 子元素: 按时间顺序排列，每行占 1 行
    "timeline_vertical": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 3.0, "row_height": _grid_card_height(4),
        "margin": _DEFAULT_MARGIN,
    }},

    # comparison_table: 左右两列对比（各 6 列），带标题行
    # 子元素: [标题A(6×1), 标题B(6×1), 内容A(6×N), 内容B(6×N)]
    "comparison_table": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},

    # quote_highlight: 大引用块（居中 8 列）+ 底部署名（8 列）
    # 子元素: [引用(8×1, col=3), 署名(8×1, col=3)]
    "quote_highlight": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},

    # kpi_grid: 4 个 KPI 卡片（各 3 列×1 行），可追加 2 行
    # 子元素: [KPI1(3×1), KPI2(3×1), KPI3(3×1), KPI4(3×1)]
    "kpi_grid": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(1),
        "margin": _DEFAULT_MARGIN,
    }},

    # magazine_layout: 大图（左 8 列×2 行）+ 2 个叠放卡片（右 4 列×各 1 行）
    # 子元素: [大图(8×2), 卡片上(4×1), 卡片下(4×1)]
    "magazine_layout": {"mode": "grid", "grid": {
        "columns": 12, "gutter": 4.0, "row_height": _grid_card_height(2),
        "margin": _DEFAULT_MARGIN,
    }},
}


# ============================================================
# 查询 API
# ============================================================

def resolve_semantic_layout(name: str) -> dict[str, Any] | None:
    """将语义布局名称解析为具体的布局引擎配置

    查询顺序：
      1. 手写语义布局（SEMANTIC_LAYOUTS）
      2. 参数化生成器（layout_generator）

    Args:
        name: 布局名称

    Returns:
        包含 "mode" 键的配置字典，或 None（表示不是已知布局名称）。
    """
    if name in SEMANTIC_LAYOUTS:
        return SEMANTIC_LAYOUTS[name]

    # 查询参数化生成器（延迟导入，避免循环）
    from .layout_generator import get_layout
    return get_layout(name)


def get_all_layout_names() -> list[str]:
    """获取所有可用布局名称（手写 + 生成器）"""
    from .layout_generator import get_all_layouts
    return sorted(set(SEMANTIC_LAYOUTS.keys()) | set(get_all_layouts().keys()))


def layout_count() -> int:
    """返回总布局数量"""
    from .layout_generator import get_all_layouts
    return len(set(SEMANTIC_LAYOUTS.keys()) | set(get_all_layouts().keys()))


def search_layouts(**kwargs) -> list[str]:
    """搜索布局（代理到 layout_generator.search_layouts）"""
    from .layout_generator import search_layouts as _search
    return _search(**kwargs)
