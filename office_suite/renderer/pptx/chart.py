"""PPTX 图表渲染 — 图表创建、数据构建、颜色应用"""

from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData

from ...ir.types import IRDocument, IRNode

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


def render_chart(renderer, slide, node: IRNode, doc: IRDocument):
    """渲染图表元素"""
    pos = node.position
    left, top, width, height = renderer._pos_to_emu(pos)

    chart_type_str = node.chart_type or node.extra.get("chart_type", "bar")
    xl_chart_type = CHART_TYPE_MAP.get(chart_type_str, XL_CHART_TYPE.BAR_CLUSTERED)

    chart_data = build_chart_data(node, doc)

    chart_frame = slide.shapes.add_chart(
        xl_chart_type, left, top, width, height, chart_data
    )
    chart = chart_frame.chart

    title = node.extra.get("title")
    if title:
        chart.has_title = True
        chart.chart_title.text_frame.paragraphs[0].text = title

    show_legend = node.extra.get("legend", True)
    chart.has_legend = show_legend
    if show_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False

    apply_chart_colors(renderer, chart, node)


def build_chart_data(node: IRNode, doc: IRDocument | None = None) -> CategoryChartData:
    """从 IRNode 构建 CategoryChartData

    数据来源（优先级从高到低）：
      - data_ref: 引用 doc.data 中的键
      - extra.categories / extra.series: 内联数据
    """
    categories: list = []
    series_list: list = []

    if node.data_ref and doc is not None and node.data_ref in doc.data:
        ref_val = doc.data[node.data_ref]
        if isinstance(ref_val, dict):
            categories = ref_val.get("categories", [])
            series_list = ref_val.get("series", [])

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


def apply_chart_colors(renderer, chart, node: IRNode):
    """为图表系列应用颜色"""
    colors = node.extra.get("colors", [
        "#2563EB", "#16A34A", "#EA580C", "#9333EA",
        "#E11D48", "#0891B2", "#CA8A04", "#4F46E5",
    ])
    for i, series in enumerate(chart.series):
        color_hex = colors[i % len(colors)]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = renderer._hex_to_rgb(color_hex)
