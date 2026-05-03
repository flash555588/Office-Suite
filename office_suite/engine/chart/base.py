"""Chart Engine Base — 外部图表库渲染器的统一抽象接口

数据流：IRNode(categories/series/data) → ChartEngine.render() → PNG 路径
所有外部引擎（matplotlib/seaborn/plotly/vega-lite/ggplot2/pgfplots）实现此接口。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ChartData:
    """统一图表数据结构

    从 IRNode.extra 或 data_ref 解析，供所有引擎共用。

    属性:
        categories: X 轴分类标签（柱状图/折线图等用）
        series: 数据系列列表，每项 { name, values, x?, y?, labels? }
        raw_data: 非结构化原始数据（散点图/热力图等高级图表用）
    """

    def __init__(self, extra: dict[str, Any], resolved_data: dict | None = None):
        source = resolved_data if resolved_data else extra
        self.categories: list = source.get("categories", [])
        self.series: list[dict] = source.get("series", [])
        self.raw_data: Any = source.get("data")

    @property
    def series_names(self) -> list[str]:
        return [s.get("name", "") for s in self.series]

    @property
    def series_values(self) -> list[list]:
        return [s.get("values", []) for s in self.series]


class BaseChartRenderer(ABC):
    """外部图表引擎基类"""

    name: str = ""           # 引擎标识（如 "matplotlib", "plotly"）
    install_hint: str = ""   # 安装提示（如 "pip install matplotlib"）

    @abstractmethod
    def is_available(self) -> bool:
        """检测引擎依赖是否已安装"""

    @abstractmethod
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
        """渲染图表到 PNG 文件

        Args:
            chart_type: 图表类型（bar/line/pie/scatter/area/heatmap/...）
            data: 统一图表数据
            extra: 完整 extra 字段（含 title/colors/legend 等）
            output_path: 输出 PNG 路径
            width_px: 图片宽度像素
            height_px: 图片高度像素
            dpi: 分辨率

        Returns:
            实际写入的文件路径
        """
