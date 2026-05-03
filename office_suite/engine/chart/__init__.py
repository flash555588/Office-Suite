"""Chart Engine Registry — 外部图表库渲染器统一入口

数据流：IRNode → render_chart_image(node, output_dir) → PNG 路径
  ↓ PPTX 渲染器检测 extra.engine 字段，调用对应引擎渲染为图片再嵌入

引擎优先级：
  matplotlib  — Python 标准科学绘图，最易安装
  seaborn     — matplotlib 上层统计美化
  plotly      — 交互式图表导出静态图（需 kaleido）
  vega-lite   — 声明式 JSON 图表规范（需 vl-convert 或 Node CLI）
  ggplot2     — R 语言绘图系统（需 Rscript + ggplot2）
  pgfplots    — LaTeX 学术图表（需 TeX Live + pdftoppm）

不可用的引擎会抛出 RuntimeError 并附带安装提示。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData

logger = logging.getLogger(__name__)

# 引擎注册表
_REGISTRY: dict[str, BaseChartRenderer] = {}


def _register(renderer: BaseChartRenderer) -> None:
    _REGISTRY[renderer.name] = renderer


def _ensure_registered() -> None:
    if _REGISTRY:
        return
    from .matplotlib_renderer import MatplotlibRenderer
    from .plotly_renderer import PlotlyRenderer
    from .vegalite_renderer import VegaLiteRenderer
    from .ggplot2_renderer import Ggplot2Renderer
    from .pgfplots_renderer import PgfplotsRenderer

    _register(MatplotlibRenderer())
    _register(PlotlyRenderer())
    _register(VegaLiteRenderer())
    _register(Ggplot2Renderer())
    _register(PgfplotsRenderer())


def list_engines() -> list[dict[str, Any]]:
    """返回所有引擎及其可用状态"""
    _ensure_registered()
    result = []
    for name, engine in _REGISTRY.items():
        result.append({
            "name": name,
            "available": engine.is_available(),
            "install_hint": engine.install_hint,
        })
    return result


def get_engine(name: str) -> BaseChartRenderer | None:
    """按名称获取引擎（不检查可用性）"""
    _ensure_registered()
    return _REGISTRY.get(name)


def render_chart_image(
    chart_type: str,
    data: dict[str, Any],
    extra: dict[str, Any],
    output_dir: str | Path,
    width_px: int = 1920,
    height_px: int = 1080,
    dpi: int = 150,
    filename: str | None = None,
) -> Path:
    """使用指定引擎渲染图表为 PNG

    Args:
        chart_type: 图表类型 (bar/line/pie/scatter/...)
        data: 含 categories/series 的数据字典
        extra: 完整 extra 字段，必须含 engine 字段指定渲染器
        output_dir: PNG 输出目录
        width_px: 图片宽度像素（默认 1920）
        height_px: 图片高度像素（默认 1080）
        dpi: 分辨率（默认 150）
        filename: 输出文件名（默认自动生成）

    Returns:
        生成的 PNG 文件路径

    Raises:
        ValueError: 未指定 engine 或引擎名无效
        RuntimeError: 引擎不可用（附带安装提示）
    """
    _ensure_registered()

    engine_name = extra.get("engine", "matplotlib")
    renderer = _REGISTRY.get(engine_name)
    if renderer is None:
        valid = list(_REGISTRY.keys())
        raise ValueError(
            f"未知图表引擎 '{engine_name}'，可用引擎: {valid}"
        )

    if not renderer.is_available():
        raise RuntimeError(
            f"图表引擎 '{engine_name}' 不可用。"
            f"请安装: {renderer.install_hint}"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        import hashlib
        import json as _json
        h = hashlib.md5(_json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
        filename = f"chart_{engine_name}_{chart_type}_{h}.png"

    output_path = output_dir / filename

    chart_data = ChartData(extra, data)

    logger.info(f"渲染图表: engine={engine_name}, type={chart_type}, "
                f"output={output_path}")

    return renderer.render(
        chart_type=chart_type,
        data=chart_data,
        extra=extra,
        output_path=output_path,
        width_px=width_px,
        height_px=height_px,
        dpi=dpi,
    )
