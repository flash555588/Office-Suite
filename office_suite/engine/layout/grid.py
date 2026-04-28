"""栅格布局引擎 — 12/24 列栅格系统

设计方案第六章：布局引擎。

栅格系统将容器划分为等宽列（默认 12 列），
元素通过指定起始列和跨列数来定位。

与 CSS Grid / Bootstrap Grid 语义一致。
"""

from dataclasses import dataclass, field
from typing import Any
from ...ir.layout_spec import (
    AbsolutePosition, GridPosition, GridAlign, LayoutMode, LayoutSpec,
)


@dataclass
class GridCell:
    """栅格单元格"""
    column: int           # 起始列（1-based）
    row: int              # 起始行（1-based）
    column_span: int = 1
    row_span: int = 1
    content: Any = None   # 关联的内容（IRNode 等）


@dataclass
class GridTrack:
    """栅格轨道（列或行）"""
    size: float           # 尺寸（mm）
    min_size: float = 0.0
    max_size: float = float("inf")


class GridLayout:
    """栅格布局引擎

    将容器划分为指定列数的等宽栅格，
    计算每个元素的绝对位置。

    用法：
        layout = GridLayout(columns=12, container_width=254, container_height=142.875)
        pos = layout.resolve(GridPosition(column=1, column_span=6, row=1))
    """

    def __init__(
        self,
        columns: int = 12,
        container_width: float = 254.0,
        container_height: float = 142.875,
        gutter: float = 2.0,
        row_height: float | None = None,
    ):
        self.columns = columns
        self.container_width = container_width
        self.container_height = container_height
        self.gutter = gutter
        self.row_height = row_height  # None = auto

        # 计算列宽（减去 gutter 占用空间）
        total_gutter = gutter * (columns - 1)
        self.column_width = (container_width - total_gutter) / columns

    def resolve(self, grid_pos: GridPosition) -> AbsolutePosition:
        """将栅格位置解析为绝对坐标

        Args:
            grid_pos: 栅格位置规格

        Returns:
            绝对坐标（mm）
        """
        col = max(1, grid_pos.column)
        col_span = max(1, grid_pos.column_span)
        row = max(1, grid_pos.row)
        row_span = max(1, grid_pos.row_span)

        # 限制在列范围内
        col = min(col, self.columns)
        col_span = min(col_span, self.columns - col + 1)

        # 计算 x 坐标（1-based 列号 → 0-based 偏移）
        x = (col - 1) * (self.column_width + self.gutter)
        width = col_span * self.column_width + (col_span - 1) * self.gutter

        # 计算 y 坐标
        if self.row_height is not None:
            y = (row - 1) * (self.row_height + self.gutter)
            height = row_span * self.row_height + (row_span - 1) * self.gutter
        else:
            # 无固定行高时，使用均匀分布
            y = (row - 1) * (self.container_height / 12)
            height = row_span * (self.container_height / 12)

        # 对齐方式处理
        if grid_pos.align == GridAlign.CENTER:
            # 垂直居中（仅在有固定行高时有效）
            if self.row_height is not None:
                available = self.container_height - (y + height)
                if available > 0:
                    y += available / 2
        elif grid_pos.align == GridAlign.END:
            if self.row_height is not None:
                available = self.container_height - (y + height)
                if available > 0:
                    y += available

        return AbsolutePosition(
            x=round(x, 2),
            y=round(y, 2),
            width=round(width, 2),
            height=round(height, 2),
        )

    def auto_place(self, cells: list[GridCell]) -> list[tuple[GridCell, AbsolutePosition]]:
        """自动放置单元格

        按行优先顺序放置，跳过已被占用的位置。

        Args:
            cells: 待放置的单元格列表

        Returns:
            (cell, position) 列表
        """
        occupied: set[tuple[int, int]] = set()
        results = []

        for cell in cells:
            # 找到第一个可用位置
            placed = False
            for r in range(1, 100):  # 最多 100 行
                for c in range(1, self.columns + 1):
                    if self._can_place(c, r, cell.column_span, cell.row_span, occupied):
                        cell.column = c
                        cell.row = r
                        for dr in range(cell.row_span):
                            for dc in range(cell.column_span):
                                occupied.add((r + dr, c + dc))
                        pos = self.resolve(GridPosition(
                            column=c,
                            row=r,
                            column_span=cell.column_span,
                            row_span=cell.row_span,
                        ))
                        results.append((cell, pos))
                        placed = True
                        break
                if placed:
                    break

        return results

    def _can_place(
        self, col: int, row: int, col_span: int, row_span: int,
        occupied: set[tuple[int, int]],
    ) -> bool:
        """检查是否可以放置"""
        if col + col_span - 1 > self.columns:
            return False
        for dr in range(row_span):
            for dc in range(col_span):
                if (row + dr, col + dc) in occupied:
                    return False
        return True

    def get_column_edges(self) -> list[float]:
        """获取所有列的左边缘 x 坐标"""
        edges = []
        for i in range(self.columns + 1):
            edges.append(i * (self.column_width + self.gutter))
        return edges
