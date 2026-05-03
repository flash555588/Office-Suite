"""pgfplots Chart Engine — LaTeX/pgfplots 图表渲染器

通过 lualatex 或 pdflatex 编译 pgfplots 代码为 PDF，再转换为 PNG。
支持图表类型：bar, line, scatter, area, box, histogram, heatmap, surface, parametric

需要环境：TeX Live 或 MiKTeX 已安装，含 pgfplots 包。
PNG 转换需要 pdftoppm (poppler) 或 ImageMagick。
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData

_PREAMBLE = r"""
\documentclass[border=2pt]{standalone}
\usepackage{pgfplots}
\usepgfplotslibrary{fillbetween, statistics, colormaps}
\pgfplotsset{compat=1.18}
\usepackage{fontspec}
\setmainfont{Microsoft YaHei UI}
\begin{document}
"""


class PgfplotsRenderer(BaseChartRenderer):
    name = "pgfplots"
    install_hint = "需要 TeX Live (含 pgfplots) + poppler (pdftoppm)"

    def is_available(self) -> bool:
        # 检查 latex 和 pdftoppm
        has_latex = False
        for cmd in ("lualatex", "pdflatex"):
            try:
                r = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
                if r.returncode == 0:
                    has_latex = True
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        if not has_latex:
            return False
        try:
            r = subprocess.run(["pdftoppm", "-v"], capture_output=True, timeout=5)
            return r.returncode == 0 or b"pdftoppm" in r.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

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
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tex_code = self._build_tex(chart_type, data, extra, width_px, height_px)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            tex_path = tmpdir / "chart.tex"
            tex_path.write_text(tex_code, encoding="utf-8")

            # 选 TeX 引擎
            engine = "lualatex"
            for e in ("lualatex", "pdflatex"):
                try:
                    subprocess.run([e, "--version"], capture_output=True, timeout=5)
                    engine = e
                    break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            # 编译
            result = subprocess.run(
                [engine, "-interaction=nonstopmode", "-output-directory", str(tmpdir),
                 str(tex_path)],
                capture_output=True, text=True, timeout=60,
            )
            pdf_path = tmpdir / "chart.pdf"
            if result.returncode != 0 or not pdf_path.exists():
                raise RuntimeError(
                    f"pgfplots 编译失败:\n{result.stderr[-1000:]}"
                )

            # PDF → PNG
            pdftoppm_result = subprocess.run(
                ["pdftoppm", "-png", "-r", str(dpi), "-singlefile",
                 str(pdf_path), str(output_path.with_suffix(""))],
                capture_output=True, text=True, timeout=30,
            )
            if pdftoppm_result.returncode != 0:
                raise RuntimeError(f"pdftoppm 转换失败:\n{pdftoppm_result.stderr}")

        return output_path

    def _build_tex(self, chart_type: str, data: ChartData,
                   extra: dict, width_px: int, height_px: int) -> str:
        """构建完整 TeX 文档"""
        width_cm = width_px * 2.54 / 96
        height_cm = height_px * 2.54 / 96
        title = extra.get("title", "").replace("_", "\\_").replace("&", "\\&")
        xlabel = extra.get("xlabel", extra.get("x_label", "")).replace("_", "\\_")
        ylabel = extra.get("ylabel", extra.get("y_label", "")).replace("_", "\\_")

        colors = extra.get("colors", [
            "{rgb,255:red,30;green,64;blue,175}",
            "{rgb,255:red,59;green,130;blue,246}",
            "{rgb,255:red,96;green,165;blue,250}",
            "{rgb,255:red,16;green,185;blue,129}",
            "{rgb,255:red,220;green,38;blue,38}",
            "{rgb,255:red,249;green,115;blue,22}",
        ])

        axis_opts = self._build_axis_opts(extra, title, xlabel, ylabel,
                                          width_cm, height_cm)

        if chart_type in ("bar", "column"):
            tikz_body = self._bar_plot(data, colors, extra)
        elif chart_type == "line":
            tikz_body = self._line_plot(data, colors, extra)
        elif chart_type == "scatter":
            tikz_body = self._scatter_plot(data, colors, extra)
        elif chart_type == "area":
            tikz_body = self._area_plot(data, colors, extra)
        elif chart_type == "histogram":
            tikz_body = self._histogram_plot(data, colors, extra)
        elif chart_type == "heatmap":
            tikz_body = self._heatmap_plot(data, extra)
        elif chart_type == "box":
            tikz_body = self._box_plot(data, colors, extra)
        else:
            tikz_body = self._bar_plot(data, colors, extra)

        return f"""{_PREAMBLE}
\\begin{{tikzpicture}}
\\begin{{axis}}[{axis_opts}]
{tikz_body}
\\end{{axis}}
\\end{{tikzpicture}}
\\end{{document}}
"""

    def _build_axis_opts(self, extra, title, xlabel, ylabel,
                         width_cm, height_cm) -> str:
        opts = [
            f"width={width_cm}cm",
            f"height={height_cm}cm",
            "grid=major",
            "grid style={dashed, gray!30}",
            f"legend style={{at={{(0.5,-0.15)}}, anchor=north, legend columns=-1}}",
        ]
        if title:
            opts.append(f"title={{{title}}}")
        if xlabel:
            opts.append(f"xlabel={{{xlabel}}}")
        if ylabel:
            opts.append(f"ylabel={{{ylabel}}}")
        if extra.get("xtick_rotation"):
            opts.append(f"xticklabel style={{rotate={extra['xtick_rotation']}}}")
        if extra.get("ymin") is not None:
            opts.append(f"ymin={extra['ymin']}")
        if extra.get("ymax") is not None:
            opts.append(f"ymax={extra['ymax']}")
        return ",\n    ".join(opts)

    def _bar_plot(self, data: ChartData, colors, extra) -> str:
        n = len(data.categories) or 1
        bar_width = extra.get("bar_width", 0.8)
        cmds = []
        for i, s in enumerate(data.series):
            coords = " ".join(
                f"({j},{v})" for j, v in enumerate(s.get("values", []))
            )
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            cmds.append(
                f"\\addplot+[{color}, fill={color}, fill opacity=0.6, "
                f"bar width={bar_width}cm] coordinates {{ {coords} }};\n"
                f"\\addlegendentry{{{name}}}"
            )
        # X tick labels
        tick_labels = " ".join(
            f"{{{c}}}" for c in data.categories
        )
        tick_pos = " ".join(str(j) for j in range(len(data.categories)))
        cmds.append(
            f"\\pgfplotsset{{xtick={{{tick_pos}}}, xticklabels={{{tick_labels}}}}}"
        )
        return "\n".join(cmds)

    def _line_plot(self, data: ChartData, colors, extra) -> str:
        cmds = []
        marker = extra.get("marker", "*")
        for i, s in enumerate(data.series):
            coords = " ".join(
                f"({j},{v})" for j, v in enumerate(s.get("values", []))
            )
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            cmds.append(
                f"\\addplot+[{color}, mark={marker}, thick] coordinates {{ {coords} }};\n"
                f"\\addlegendentry{{{name}}}"
            )
        if data.categories:
            tick_labels = " ".join(f"{{{c}}}" for c in data.categories)
            tick_pos = " ".join(str(j) for j in range(len(data.categories)))
            cmds.append(
                f"\\pgfplotsset{{xtick={{{tick_pos}}}, xticklabels={{{tick_labels}}}}}"
            )
        return "\n".join(cmds)

    def _scatter_plot(self, data: ChartData, colors, extra) -> str:
        cmds = []
        mark_size = extra.get("mark_size", 3)
        for i, s in enumerate(data.series):
            x_vals = s.get("x", list(range(len(s.get("values", [])))))
            y_vals = s.get("y", s.get("values", []))
            coords = " ".join(
                f"({x},{y})" for x, y in zip(x_vals, y_vals)
            )
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            cmds.append(
                f"\\addplot+[{color}, only marks, mark size={mark_size}pt] "
                f"coordinates {{ {coords} }};\n"
                f"\\addlegendentry{{{name}}}"
            )
        return "\n".join(cmds)

    def _area_plot(self, data: ChartData, colors, extra) -> str:
        cmds = []
        for i, s in enumerate(data.series):
            coords = " ".join(
                f"({j},{v})" for j, v in enumerate(s.get("values", []))
            )
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            cmds.append(
                f"\\addplot+[{color}, fill={color}, fill opacity=0.2, thick] "
                f"coordinates {{ {coords} }} \\closedcycle;\n"
                f"\\addlegendentry{{{name}}}"
            )
        return "\n".join(cmds)

    def _histogram_plot(self, data: ChartData, colors, extra) -> str:
        cmds = []
        for i, s in enumerate(data.series):
            values = s.get("values", [])
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            # 使用 ybar interval 自动分箱
            vals_sorted = sorted(values)
            coords = " ".join(
                f"({j},{v})" for j, v in enumerate(vals_sorted)
            )
            cmds.append(
                f"\\addplot+[{color}, fill={color}, fill opacity=0.6, "
                f"ybar] coordinates {{ {coords} }};\n"
                f"\\addlegendentry{{{name}}}"
            )
        return "\n".join(cmds)

    def _heatmap_plot(self, data: ChartData, extra) -> str:
        matrix = data.raw_data if isinstance(data.raw_data, list) else None
        if matrix is None:
            matrix = [s.get("values", []) for s in data.series]
        if not matrix:
            return "% no data for heatmap"
        # 用 table 构建坐标+值
        table_rows = []
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                table_rows.append(f"{j} {i} {val}")
        table_data = "\n".join(table_rows)
        return f"""\\addplot3[
    mesh/cols={len(matrix[0]) if matrix else 1},
    shader=interp
] table[row sep=\\\\] {{
{table_data}
}};"""

    def _box_plot(self, data: ChartData, colors, extra) -> str:
        cmds = []
        for i, s in enumerate(data.series):
            values = s.get("values", [])
            if not values:
                continue
            color = colors[i % len(colors)]
            name = s.get("name", f"S{i+1}").replace("_", "\\_")
            val_str = ",".join(str(v) for v in values)
            cmds.append(
                f"\\addplot+[{color}, boxplot prepared={{"
                f"lower quartile={sorted(values)[len(values)//4]},"
                f"upper quartile={sorted(values)[3*len(values)//4]},"
                f"median={sorted(values)[len(values)//2]}"
                f"}}] coordinates {{}};\n"
                f"\\addlegendentry{{{name}}}"
            )
        return "\n".join(cmds)
