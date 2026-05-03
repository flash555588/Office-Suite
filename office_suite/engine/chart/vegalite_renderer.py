"""Vega-Lite Chart Engine — 声明式 JSON 规范图表渲染器

支持两种使用方式：
1. extra.spec 传入完整 Vega-Lite JSON spec → 直接渲染
2. 通过 categories/series 数据 + chart_type → 自动生成 spec

渲染路径：优先使用 vl-convert CLI 导出 PNG，降级为 HTML 截图或 SVG。
"""

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData

# chart_type → Vega-Lite mark type
_VL_MARK_MAP = {
    "bar": "bar",
    "column": "bar",
    "line": "line",
    "pie": "arc",
    "doughnut": "arc",
    "area": "area",
    "scatter": "point",
    "heatmap": "rect",
    "box": "boxplot",
    "treemap": "rect",
    "histogram": "bar",
    "radar": "line",
}


class VegaLiteRenderer(BaseChartRenderer):
    name = "vega-lite"
    install_hint = "pip install vl-convert-python  (或 npm install -g vega-lite vega-cli)"

    def is_available(self) -> bool:
        # 检查 Python 包 或 CLI 工具
        if importlib.util.find_spec("vl_convert") is not None:
            return True
        try:
            subprocess.run(["vl2png", "--help"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        try:
            subprocess.run(["npx", "vl2png", "--help"], capture_output=True, timeout=10)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
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
        # 优先使用用户提供的完整 spec
        spec = extra.get("spec")
        if not spec:
            spec = self._build_spec(chart_type, data, extra, width_px, height_px)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 尝试 Python 包
        if importlib.util.find_spec("vl_convert") is not None:
            return self._render_with_vl_convert(spec, output_path, width_px,
                                                height_px, dpi)

        # 尝试 CLI
        return self._render_with_cli(spec, output_path, width_px, height_px, dpi)

    def _build_spec(self, chart_type: str, data: ChartData,
                    extra: dict, width: int, height: int) -> dict:
        """从数据构建 Vega-Lite spec"""
        mark_type = _VL_MARK_MAP.get(chart_type, "bar")
        title = extra.get("title", "")

        # 转换数据为 Vega-Lite inline 格式
        values = self._data_to_values(chart_type, data)

        spec: dict[str, Any] = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "width": width - 120,
            "height": height - 100,
            "data": {"values": values},
            "mark": {"type": mark_type, "tooltip": True},
        }

        if title:
            spec["title"] = title

        colors = extra.get("colors", [
            "#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD",
            "#DC2626", "#F97316", "#10B981", "#8B5CF6",
        ])

        if chart_type in ("pie", "doughnut"):
            spec["encoding"] = {
                "theta": {"field": "value", "type": "quantitative", "stack": True},
                "color": {"field": "category", "type": "nominal",
                          "scale": {"range": colors}},
            }
            if chart_type == "doughnut":
                spec["mark"] = {"type": "arc", "innerRadius": 60, "tooltip": True}
        elif chart_type in ("bar", "column", "line", "area"):
            x_enc = {"field": "category", "type": "ordinal"} if data.categories \
                else {"field": "index", "type": "quantitative"}
            spec["encoding"] = {
                "x": x_enc,
                "y": {"field": "value", "type": "quantitative"},
                "color": {"field": "series", "type": "nominal",
                          "scale": {"range": colors}},
            }
            if chart_type == "column":
                spec["encoding"]["x"]["type"] = "ordinal"
        elif chart_type == "scatter":
            spec["encoding"] = {
                "x": {"field": "x", "type": "quantitative"},
                "y": {"field": "y", "type": "quantitative"},
                "color": {"field": "series", "type": "nominal",
                          "scale": {"range": colors}},
                "size": {"field": "size", "type": "quantitative",
                         "legend": None} if any("size" in v for v in values) else {},
            }
        elif chart_type == "heatmap":
            spec["encoding"] = {
                "x": {"field": "x", "type": "ordinal"},
                "y": {"field": "y", "type": "ordinal"},
                "color": {"field": "value", "type": "quantitative",
                          "scale": {"scheme": extra.get("scheme", "yelloworangered")}},
            }
            spec["mark"] = {"type": "rect", "tooltip": True}
        elif chart_type == "box":
            spec["encoding"] = {
                "x": {"field": "series", "type": "nominal"},
                "y": {"field": "value", "type": "quantitative"},
            }
            spec["mark"] = {"type": "boxplot", "extent": 1.5}
        elif chart_type == "histogram":
            spec["encoding"] = {
                "x": {"field": "value", "type": "quantitative", "bin": True},
                "y": {"aggregate": "count"},
                "color": {"field": "series", "type": "nominal",
                          "scale": {"range": colors}},
            }
        else:
            spec["encoding"] = {
                "x": {"field": "category", "type": "ordinal"},
                "y": {"field": "value", "type": "quantitative"},
                "color": {"field": "series", "type": "nominal",
                          "scale": {"range": colors}},
            }

        # 坐标轴标签
        xlabel = extra.get("xlabel", extra.get("x_label"))
        ylabel = extra.get("ylabel", extra.get("y_label"))
        if xlabel and "encoding" in spec and "x" in spec["encoding"]:
            spec["encoding"]["x"]["axis"] = {"title": xlabel}
        if ylabel and "encoding" in spec and "y" in spec["encoding"]:
            spec["encoding"]["y"]["axis"] = {"title": ylabel}

        # 背景
        bg = extra.get("background_color", extra.get("bg_color"))
        if bg:
            spec["background"] = bg

        return spec

    def _data_to_values(self, chart_type: str, data: ChartData) -> list[dict]:
        """将 ChartData 转为 Vega-Lite values 数组"""
        values = []

        if chart_type in ("pie", "doughnut"):
            labels = data.categories or (data.series[0].get("labels", []) if data.series else [])
            vals = data.series[0].get("values", []) if data.series else []
            for i, v in enumerate(vals):
                values.append({"category": labels[i] if i < len(labels) else f"Item {i}",
                               "value": v})

        elif chart_type == "scatter":
            for s in data.series:
                x_vals = s.get("x", [])
                y_vals = s.get("y", s.get("values", []))
                name = s.get("name", "")
                for j in range(max(len(x_vals), len(y_vals))):
                    entry = {"series": name}
                    if j < len(x_vals):
                        entry["x"] = x_vals[j]
                    if j < len(y_vals):
                        entry["y"] = y_vals[j]
                    if "size" in s and j < len(s["size"]):
                        entry["size"] = s["size"][j]
                    values.append(entry)

        elif chart_type == "heatmap":
            matrix = data.raw_data if isinstance(data.raw_data, list) else None
            if matrix is None:
                matrix = [s.get("values", []) for s in data.series]
            y_labels = [s.get("name", f"Row {i}") for i, s in enumerate(data.series)]
            x_labels = data.categories or [f"Col {j}" for j in range(len(matrix[0]) if matrix else 0)]
            for i, row in enumerate(matrix):
                for j, val in enumerate(row):
                    values.append({"x": x_labels[j] if j < len(x_labels) else f"Col {j}",
                                   "y": y_labels[i],
                                   "value": val})

        elif chart_type in ("box", "histogram"):
            for s in data.series:
                name = s.get("name", "")
                for v in s.get("values", []):
                    values.append({"series": name, "value": v})

        else:
            # bar/column/line/area
            for s in data.series:
                name = s.get("name", "")
                vals = s.get("values", [])
                for j, v in enumerate(vals):
                    cat = data.categories[j] if j < len(data.categories) else j
                    values.append({"category": cat, "value": v,
                                   "series": name, "index": j})

        return values

    def _render_with_vl_convert(self, spec: dict, output_path: Path,
                                width: int, height: int, dpi: int) -> Path:
        import vl_convert as vlc
        png_bytes = vlc.vegalite_to_png(
            json.dumps(spec),
            scale=dpi / 96,
            ppi=dpi,
        )
        output_path.write_bytes(png_bytes)
        return output_path

    def _render_with_cli(self, spec: dict, output_path: Path,
                         width: int, height: int, dpi: int) -> Path:
        spec_json = json.dumps(spec)
        # 尝试 vl2png CLI
        try:
            result = subprocess.run(
                ["vl2png", "--scale", str(dpi / 96)],
                input=spec_json.encode(),
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                output_path.write_bytes(result.stdout)
                return output_path
        except FileNotFoundError:
            pass

        # 尝试 npx vl2png
        try:
            result = subprocess.run(
                ["npx", "vl2png", "--scale", str(dpi / 96)],
                input=spec_json.encode(),
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                output_path.write_bytes(result.stdout)
                return output_path
        except FileNotFoundError:
            pass

        # 最终降级：输出 SVG
        svg_path = output_path.with_suffix(".svg")
        try:
            result = subprocess.run(
                ["vl2svg"],
                input=spec_json.encode(),
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                svg_path.write_bytes(result.stdout)
                return svg_path
        except FileNotFoundError:
            pass

        raise RuntimeError(
            f"无法渲染 Vega-Lite 图表。请安装: {self.install_hint}"
        )
