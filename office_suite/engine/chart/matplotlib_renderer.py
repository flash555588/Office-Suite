"""Matplotlib Chart Engine — matplotlib + seaborn 图表渲染器

支持图表类型：bar, column(→bar), line, pie, doughnut(→pie), area, scatter, heatmap, box, violin, histogram
seaborn 可通过 extra.sandbox=true 启用，自动美化配色。
"""

import importlib.util
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData

# chart_type → seaborn/matplotlib 映射
_MPL_CHART_MAP = {
    "bar": "bar",
    "column": "bar",
    "line": "line",
    "pie": "pie",
    "doughnut": "pie",
    "area": "area",
    "scatter": "scatter",
    "heatmap": "heatmap",
    "box": "box",
    "violin": "violin",
    "histogram": "histogram",
    "radar": "radar",
}


class MatplotlibRenderer(BaseChartRenderer):
    name = "matplotlib"
    install_hint = "pip install matplotlib"

    def is_available(self) -> bool:
        return importlib.util.find_spec("matplotlib") is not None

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
        import matplotlib
        matplotlib.use("Agg")  # 非交互后端
        import matplotlib.pyplot as plt

        use_seaborn = extra.get("seaborn", False)
        if use_seaborn and importlib.util.find_spec("seaborn"):
            import seaborn as sns
            sns.set_theme(style=extra.get("seaborn_style", "whitegrid"))

        colors = extra.get("colors", [
            "#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD",
            "#DC2626", "#F97316", "#10B981", "#8B5CF6",
        ])

        figsize = (width_px / dpi, height_px / dpi)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # 背景色
        bg = extra.get("background_color", extra.get("bg_color"))
        if bg:
            fig.patch.set_facecolor(bg)
            ax.set_facecolor(bg)
        else:
            fig.patch.set_facecolor("none")
            ax.set_facecolor("none")

        ct = _MPL_CHART_MAP.get(chart_type, chart_type)
        title = extra.get("title", "")
        xlabel = extra.get("xlabel", extra.get("x_label", ""))
        ylabel = extra.get("ylabel", extra.get("y_label", ""))
        show_legend = extra.get("legend", len(data.series) > 1)
        grid = extra.get("grid", True)

        try:
            if ct == "bar":
                self._draw_bar(ax, data, colors, extra)
            elif ct == "line":
                self._draw_line(ax, data, colors, extra)
            elif ct == "pie":
                self._draw_pie(fig, ax, data, colors, extra, ct)
            elif ct == "area":
                self._draw_area(ax, data, colors, extra)
            elif ct == "scatter":
                self._draw_scatter(ax, data, colors, extra)
            elif ct == "heatmap":
                self._draw_heatmap(ax, data, extra)
            elif ct == "box":
                self._draw_box(ax, data, colors, extra)
            elif ct == "violin":
                self._draw_violin(ax, data, colors, extra)
            elif ct == "histogram":
                self._draw_histogram(ax, data, colors, extra)
            elif ct == "radar":
                self._draw_radar(fig, ax, data, colors, extra)
            else:
                # 未知类型降级为柱状图
                self._draw_bar(ax, data, colors, extra)

            if title and ct not in ("pie",):
                ax.set_title(title, fontsize=extra.get("title_size", 16),
                             fontweight="bold", pad=12)
            if xlabel:
                ax.set_xlabel(xlabel, fontsize=extra.get("label_size", 12))
            if ylabel:
                ax.set_ylabel(ylabel, fontsize=extra.get("label_size", 12))
            if show_legend and ct not in ("pie", "heatmap", "box", "violin"):
                ax.legend(fontsize=extra.get("legend_size", 10),
                          loc=extra.get("legend_loc", "best"))
            if grid and ct not in ("pie", "heatmap"):
                ax.grid(grid, alpha=0.3, linestyle="--")

            fig.tight_layout()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(str(output_path), dpi=dpi, bbox_inches="tight",
                        facecolor=fig.get_facecolor(), transparent=True)
        finally:
            plt.close(fig)

        return output_path

    # ---- 绘制方法 ----

    def _draw_bar(self, ax, data: ChartData, colors, extra):
        import numpy as np
        if not data.categories:
            return
        x = np.arange(len(data.categories))
        n = len(data.series) or 1
        bar_width = extra.get("bar_width", 0.8 / n)
        horizontal = extra.get("horizontal", False)

        for i, s in enumerate(data.series):
            offset = (i - n / 2 + 0.5) * bar_width
            label = s.get("name", "")
            values = s.get("values", [])
            color = colors[i % len(colors)]
            if horizontal:
                ax.barh(x + offset, values, bar_width, label=label, color=color)
            else:
                ax.bar(x + offset, values, bar_width, label=label, color=color)

        labels = data.categories
        if horizontal:
            ax.set_yticks(x)
            ax.set_yticklabels(labels)
        else:
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=extra.get("xtick_rotation", 0))

    def _draw_line(self, ax, data: ChartData, colors, extra):
        import numpy as np
        x = np.arange(len(data.categories)) if data.categories else None
        for i, s in enumerate(data.series):
            values = s.get("values", [])
            label = s.get("name", "")
            color = colors[i % len(colors)]
            marker = extra.get("marker", "o")
            lw = extra.get("line_width", 2)
            if x is not None:
                ax.plot(x, values, marker=marker, label=label, color=color,
                        linewidth=lw, markersize=extra.get("marker_size", 6))
            else:
                ax.plot(values, marker=marker, label=label, color=color,
                        linewidth=lw)
        if x is not None and data.categories:
            ax.set_xticks(x)
            ax.set_xticklabels(data.categories,
                               rotation=extra.get("xtick_rotation", 0))

    def _draw_pie(self, fig, ax, data: ChartData, colors, extra, ct):
        values = data.series[0].get("values", []) if data.series else []
        labels = data.categories or data.series[0].get("labels", []) if data.series else []
        if not values:
            return
        pct = extra.get("autopct", "%1.1f%%")
        wedgeprops = {}
        if ct == "doughnut":
            wedgeprops = {"width": 0.4}
        ax.pie(values, labels=labels, colors=colors[:len(values)],
               autopct=pct, startangle=90, wedgeprops=wedgeprops)
        ax.axis("equal")
        title = extra.get("title", "")
        if title:
            ax.set_title(title, fontsize=extra.get("title_size", 16),
                         fontweight="bold", pad=12)

    def _draw_area(self, ax, data: ChartData, colors, extra):
        import numpy as np
        x = np.arange(len(data.categories)) if data.categories else None
        for i, s in enumerate(data.series):
            values = s.get("values", [])
            label = s.get("name", "")
            color = colors[i % len(colors)]
            alpha = extra.get("fill_alpha", 0.3)
            if x is not None:
                ax.fill_between(x, values, alpha=alpha, color=color, label=label)
                ax.plot(x, values, color=color, linewidth=2)
            else:
                ax.fill_between(range(len(values)), values,
                                alpha=alpha, color=color, label=label)
        if x is not None and data.categories:
            ax.set_xticks(x)
            ax.set_xticklabels(data.categories)

    def _draw_scatter(self, ax, data: ChartData, colors, extra):
        if data.series:
            for i, s in enumerate(data.series):
                x_vals = s.get("x", s.get("values", []))
                y_vals = s.get("y", [])
                label = s.get("name", "")
                color = colors[i % len(colors)]
                if y_vals:
                    ax.scatter(x_vals, y_vals, c=color, label=label,
                               s=extra.get("point_size", 50), alpha=0.7)
                elif len(x_vals) >= 2:
                    # 单 values 时假设是 (x,y) 对
                    ax.scatter(x_vals[::2], x_vals[1::2], c=color, label=label,
                               s=extra.get("point_size", 50), alpha=0.7)
        elif data.raw_data and isinstance(data.raw_data, dict):
            x = data.raw_data.get("x", [])
            y = data.raw_data.get("y", [])
            ax.scatter(x, y, c=colors[0], s=extra.get("point_size", 50), alpha=0.7)

    def _draw_heatmap(self, ax, data: ChartData, extra):
        import numpy as np
        matrix = data.raw_data if isinstance(data.raw_data, list) else None
        if matrix is None and data.series:
            matrix = [s.get("values", []) for s in data.series]
        if not matrix:
            return
        arr = np.array(matrix, dtype=float)
        cmap = extra.get("cmap", "YlOrRd")
        im = ax.imshow(arr, cmap=cmap, aspect="auto")
        # 标签
        xlabels = extra.get("xlabels", data.categories)
        ylabels = extra.get("ylabels", [s.get("name", "") for s in data.series])
        if xlabels:
            ax.set_xticks(range(len(xlabels)))
            ax.set_xticklabels(xlabels, fontsize=9)
        if ylabels:
            ax.set_yticks(range(len(ylabels)))
            ax.set_yticklabels(ylabels, fontsize=9)
        # 数值标注
        if extra.get("annotate", arr.size <= 100):
            for (j, k), val in np.ndenumerate(arr):
                ax.text(k, j, f"{val:.1f}", ha="center", va="center", fontsize=8)
        try:
            import matplotlib.pyplot as plt
            plt.colorbar(im, ax=ax, shrink=0.8)
        except Exception:
            pass

    def _draw_box(self, ax, data: ChartData, colors, extra):
        all_data = []
        labels = []
        for i, s in enumerate(data.series):
            vals = s.get("values", [])
            if vals:
                all_data.append(vals)
                labels.append(s.get("name", f"S{i+1}"))
        if not all_data:
            return
        bp = ax.boxplot(all_data, labels=labels, patch_artist=True)
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.6)

    def _draw_violin(self, ax, data: ChartData, colors, extra):
        all_data = []
        labels = []
        for i, s in enumerate(data.series):
            vals = s.get("values", [])
            if vals:
                all_data.append(vals)
                labels.append(s.get("name", f"S{i+1}"))
        if not all_data:
            return
        vp = ax.violinplot(all_data, showmeans=True, showmedians=True)
        for i, body in enumerate(vp["bodies"]):
            body.set_facecolor(colors[i % len(colors)])
            body.set_alpha(0.6)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels)

    def _draw_histogram(self, ax, data: ChartData, colors, extra):
        bins = extra.get("bins", 20)
        for i, s in enumerate(data.series):
            vals = s.get("values", [])
            if vals:
                ax.hist(vals, bins=bins, color=colors[i % len(colors)],
                        alpha=0.6, label=s.get("name", ""),
                        edgecolor="white", linewidth=0.5)

    def _draw_radar(self, fig, ax, data: ChartData, colors, extra):
        import numpy as np
        if not data.categories:
            return
        N = len(data.categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        ax = fig.add_subplot(111, polar=True)
        for i, s in enumerate(data.series):
            values = s.get("values", [])
            if not values:
                continue
            vals = values[:N] + values[:1]
            color = colors[i % len(colors)]
            ax.plot(angles, vals, "o-", linewidth=2, label=s.get("name", ""),
                    color=color)
            ax.fill(angles, vals, alpha=0.15, color=color)

        ax.set_thetagrids(np.degrees(angles[:-1]), data.categories)
        ax.set_theta_offset(np.pi / 2)
        ax.set_rlabel_position(30)
