"""Plotly Chart Engine — plotly 交互式图表渲染器

将 plotly 图表导出为静态 PNG（需 kaleido 包），或降级为 SVG/PDF。
支持图表类型：bar, line, pie, doughnut, scatter, area, heatmap, box, violin, sunburst, treemap, funnel
"""

import importlib.util
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData


class PlotlyRenderer(BaseChartRenderer):
    name = "plotly"
    install_hint = "pip install plotly kaleido"

    def is_available(self) -> bool:
        return importlib.util.find_spec("plotly") is not None

    def render(
        self,
        chart_type: str,
        data: ChartData,
        extra: dict[str, Any],
        output_path: Path,
        width_px: int = 1920,
        height_px: int = 1080,
        dpi: int = 150,
    ) -> Path:
        import plotly.graph_objects as go
        import plotly.express as px

        colors = extra.get("colors", [
            "#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD",
            "#DC2626", "#F97316", "#10B981", "#8B5CF6",
        ])
        title = extra.get("title", "")
        template = extra.get("template", "plotly_white")

        fig = self._build_figure(chart_type, data, extra, colors)

        if title:
            fig.update_layout(title=dict(text=title, x=0.5))

        fig.update_layout(
            width=width_px,
            height=height_px,
            template=template,
            font=dict(family=extra.get("font_family", "Microsoft YaHei UI"),
                      size=extra.get("font_size", 14)),
            showlegend=extra.get("legend", len(data.series) > 1),
            margin=dict(l=60, r=40, t=60 if title else 20, b=60),
            paper_bgcolor=extra.get("bg_color", "rgba(0,0,0,0)"),
            plot_bgcolor=extra.get("plot_bg_color", "rgba(0,0,0,0)"),
        )

        # 导出为 PNG
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 优先尝试 kaleido
        has_kaleido = importlib.util.find_spec("kaleido") is not None
        if has_kaleido:
            fig.write_image(str(output_path), width=width_px, height=height_px,
                            scale=dpi / 96)
        else:
            # 降级：写 HTML + 提示安装 kaleido
            html_path = output_path.with_suffix(".html")
            fig.write_html(str(html_path), include_plotlyjs="cdn")
            # 尝试用 Selenium/截图
            try:
                fig.write_image(str(output_path), width=width_px,
                                height=height_px, engine="auto")
            except Exception:
                # 最终降级：生成 SVG 作为 fallback
                svg_path = output_path.with_suffix(".svg")
                fig.write_image(str(svg_path), width=width_px, height=height_px)
                return svg_path

        return output_path

    def _build_figure(self, chart_type: str, data: ChartData,
                      extra: dict, colors: list[str]):
        """构建 Plotly Figure 对象"""
        import plotly.graph_objects as go

        fig = go.Figure()

        if chart_type in ("bar", "column"):
            self._add_bar_traces(fig, data, extra, colors)
        elif chart_type == "line":
            self._add_line_traces(fig, data, extra, colors)
        elif chart_type in ("pie", "doughnut"):
            self._add_pie_trace(fig, data, extra, colors, chart_type)
        elif chart_type == "scatter":
            self._add_scatter_traces(fig, data, extra, colors)
        elif chart_type == "area":
            self._add_area_traces(fig, data, extra, colors)
        elif chart_type == "heatmap":
            self._add_heatmap_trace(fig, data, extra, colors)
        elif chart_type == "box":
            self._add_box_traces(fig, data, extra, colors)
        elif chart_type == "violin":
            self._add_violin_traces(fig, data, extra, colors)
        elif chart_type == "funnel":
            self._add_funnel_trace(fig, data, extra, colors)
        elif chart_type == "sunburst":
            self._add_sunburst_trace(fig, data, extra, colors)
        elif chart_type == "treemap":
            self._add_treemap_trace(fig, data, extra, colors)
        else:
            self._add_bar_traces(fig, data, extra, colors)

        # 坐标轴标签
        xlabel = extra.get("xlabel", extra.get("x_label", ""))
        ylabel = extra.get("ylabel", extra.get("y_label", ""))
        if xlabel:
            fig.update_xaxes(title_text=xlabel)
        if ylabel:
            fig.update_yaxes(title_text=ylabel)

        return fig

    def _add_bar_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        orientation = extra.get("orientation", "vertical")
        for i, s in enumerate(data.series):
            kw = dict(
                x=data.categories or list(range(len(s.get("values", [])))),
                y=s.get("values", []),
                name=s.get("name", ""),
                marker_color=colors[i % len(colors)],
            )
            if orientation == "horizontal":
                kw["orientation"] = "h"
                kw["x"], kw["y"] = kw["y"], kw["x"]
            fig.add_trace(go.Bar(**kw))
        if data.categories:
            fig.update_xaxes(categoryorder="array", categoryarray=data.categories)

    def _add_line_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        for i, s in enumerate(data.series):
            fig.add_trace(go.Scatter(
                x=data.categories or list(range(len(s.get("values", [])))),
                y=s.get("values", []),
                name=s.get("name", ""),
                mode=extra.get("mode", "lines+markers"),
                line=dict(color=colors[i % len(colors)],
                          width=extra.get("line_width", 2)),
            ))

    def _add_pie_trace(self, fig, data, extra, colors, chart_type):
        import plotly.graph_objects as go
        values = data.series[0].get("values", []) if data.series else []
        labels = data.categories or (data.series[0].get("labels", []) if data.series else [])
        hole = 0.4 if chart_type == "doughnut" else 0
        fig.add_trace(go.Pie(
            values=values,
            labels=labels,
            hole=hole,
            marker=dict(colors=colors[:len(values)]),
            textinfo=extra.get("textinfo", "percent+label"),
        ))

    def _add_scatter_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        for i, s in enumerate(data.series):
            x_vals = s.get("x", data.categories or [])
            y_vals = s.get("y", s.get("values", []))
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode=extra.get("mode", "markers"),
                name=s.get("name", ""),
                marker=dict(color=colors[i % len(colors)],
                            size=extra.get("marker_size", 10)),
            ))

    def _add_area_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        stackgroup = extra.get("stackgroup", None)
        for i, s in enumerate(data.series):
            fig.add_trace(go.Scatter(
                x=data.categories or list(range(len(s.get("values", [])))),
                y=s.get("values", []),
                name=s.get("name", ""),
                fill=extra.get("fill", "tozeroy"),
                stackgroup=stackgroup,
                line=dict(color=colors[i % len(colors)], width=1),
            ))

    def _add_heatmap_trace(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        matrix = data.raw_data if isinstance(data.raw_data, list) else None
        if matrix is None and data.series:
            matrix = [s.get("values", []) for s in data.series]
        if not matrix:
            return
        fig.add_trace(go.Heatmap(
            z=matrix,
            x=data.categories,
            y=[s.get("name", "") for s in data.series],
            colorscale=extra.get("colorscale", "YlOrRd"),
            text=[[f"{v:.1f}" for v in row] for row in matrix] if extra.get("annotate", True) else None,
            texttemplate="%{text}" if extra.get("annotate", True) else None,
        ))

    def _add_box_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        for i, s in enumerate(data.series):
            fig.add_trace(go.Box(
                y=s.get("values", []),
                name=s.get("name", ""),
                marker_color=colors[i % len(colors)],
                boxmean=extra.get("boxmean", "sd"),
            ))

    def _add_violin_traces(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        for i, s in enumerate(data.series):
            fig.add_trace(go.Violin(
                y=s.get("values", []),
                name=s.get("name", ""),
                line_color=colors[i % len(colors)],
                meanline_visible=True,
            ))

    def _add_funnel_trace(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        if not data.series:
            return
        s = data.series[0]
        fig.add_trace(go.Funnel(
            y=data.categories or s.get("labels", []),
            x=s.get("values", []),
            marker=dict(colors=colors[:len(s.get("values", []))]),
            textinfo=extra.get("textinfo", "value+percent initial"),
        ))

    def _add_sunburst_trace(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        labels = extra.get("labels", data.categories or [])
        parents = extra.get("parents", [])
        values = extra.get("values", [])
        if data.series:
            values = data.series[0].get("values", values)
        fig.add_trace(go.Sunburst(
            labels=labels, parents=parents, values=values,
            branchvalues=extra.get("branchvalues", "total"),
            marker=dict(colors=colors),
        ))

    def _add_treemap_trace(self, fig, data, extra, colors):
        import plotly.graph_objects as go
        labels = extra.get("labels", data.categories or [])
        parents = extra.get("parents", [])
        values = extra.get("values", [])
        if data.series:
            values = data.series[0].get("values", values)
        fig.add_trace(go.Treemap(
            labels=labels, parents=parents, values=values,
            branchvalues=extra.get("branchvalues", "total"),
            marker=dict(colors=colors),
        ))
