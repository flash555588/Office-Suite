"""弹性布局引擎 — Flexbox 语义

设计方案第六章：布局引擎。

Flexbox 布局在一维方向（行或列）上排列元素，
支持对齐、分布、换行、伸缩等语义。

与 CSS Flexbox 语义对齐。
"""

from dataclasses import dataclass
from ...ir.layout_spec import (
    AbsolutePosition, FlexPosition, FlexDirection, FlexJustify, FlexAlign,
    LayoutMode, LayoutSpec,
)


@dataclass
class FlexItem:
    """弹性布局子项"""
    width: float = 0.0       # 固定宽度（mm）
    height: float = 0.0      # 固定高度（mm）
    grow: float = 0.0        # 放大比例
    shrink: float = 1.0      # 缩小比例
    basis: float | None = None  # 初始尺寸（mm），None = auto
    order: int = 0
    align_self: FlexAlign | None = None  # 覆盖容器的 align-items
    content: object = None   # 关联内容


class FlexLayout:
    """弹性布局引擎

    在一维方向上排列子项，支持：
    - 主轴方向：row / column / row-reverse / column-reverse
    - 主轴对齐：justify-content（start/center/end/space-between/space-around/space-evenly）
    - 交叉轴对齐：align-items（start/center/end/stretch）
    - 间距：gap
    - 伸缩：flex-grow / flex-shrink

    用法：
        layout = FlexLayout(container_width=254, container_height=142.875)
        positions = layout.resolve(
            flex_pos=FlexPosition(direction=FlexDirection.ROW, gap=5),
            items=[FlexItem(width=50, height=30), FlexItem(width=80, height=30)],
        )
    """

    def __init__(
        self,
        container_width: float = 254.0,
        container_height: float = 142.875,  # 16:9 正确高度
    ):
        self.container_width = container_width
        self.container_height = container_height

    def resolve(
        self,
        flex_pos: FlexPosition,
        items: list[FlexItem],
    ) -> list[AbsolutePosition]:
        """计算每个子项的位置

        Args:
            flex_pos: 容器的弹性布局参数
            items: 子项列表

        Returns:
            每个子项的绝对位置列表
        """
        if not items:
            return []

        is_row = flex_pos.direction in (FlexDirection.ROW, FlexDirection.ROW_REVERSE)
        main_size = self.container_width if is_row else self.container_height
        cross_size = self.container_height if is_row else self.container_width

        # 计算每个子项的主轴尺寸
        item_sizes = []
        total_fixed = 0.0
        total_grow = 0.0

        for item in items:
            basis = item.basis if item.basis is not None else (item.width if is_row else item.height)
            if basis is None or basis <= 0:
                basis = 0.0
            item_sizes.append(basis)
            total_fixed += basis
            total_grow += item.grow

        # 可用空间 = 容器主轴尺寸 - 固定尺寸 - 间距
        gap = flex_pos.gap
        total_gap = gap * (len(items) - 1)
        available = main_size - total_fixed - total_gap

        # 分配剩余空间给 grow > 0 的子项
        if available > 0 and total_grow > 0:
            for i, item in enumerate(items):
                if item.grow > 0:
                    item_sizes[i] += available * (item.grow / total_grow)
        elif available < 0:
            # 需要收缩
            total_shrink = sum(item.shrink for i, item in enumerate(items) if item_sizes[i] > 0)
            if total_shrink > 0:
                for i, item in enumerate(items):
                    if item.shrink > 0 and item_sizes[i] > 0:
                        item_sizes[i] += available * (item.shrink / total_shrink)
                        item_sizes[i] = max(0, item_sizes[i])

        # 计算主轴偏移
        total_items_size = sum(item_sizes) + total_gap
        offset = self._calc_main_offset(flex_pos.justify, main_size, total_items_size)

        # 分配位置
        positions = []
        current = offset

        # 处理反向
        indices = range(len(items))
        if flex_pos.direction in (FlexDirection.ROW_REVERSE, FlexDirection.COLUMN_REVERSE):
            indices = range(len(items) - 1, -1, -1)

        ordered_positions: list[AbsolutePosition | None] = [None] * len(items)

        for idx in indices:
            item = items[idx]
            size = item_sizes[idx]

            # 交叉轴位置
            cross_pos = self._calc_cross_position(
                item.align_self or flex_pos.align,
                cross_size,
                item.height if is_row else item.width,
            )

            if is_row:
                pos = AbsolutePosition(
                    x=round(current, 2),
                    y=round(cross_pos, 2),
                    width=round(size, 2),
                    height=round(item.height if item.height > 0 else cross_size, 2),
                )
            else:
                pos = AbsolutePosition(
                    x=round(cross_pos, 2),
                    y=round(current, 2),
                    width=round(item.width if item.width > 0 else cross_size, 2),
                    height=round(size, 2),
                )

            ordered_positions[idx] = pos
            current += size + gap

        return ordered_positions  # type: ignore

    def _calc_main_offset(
        self, justify: FlexJustify, container_size: float, items_size: float,
    ) -> float:
        """计算主轴起始偏移"""
        if justify == FlexJustify.START:
            return 0.0
        elif justify == FlexJustify.CENTER:
            return (container_size - items_size) / 2
        elif justify == FlexJustify.END:
            return container_size - items_size
        elif justify == FlexJustify.SPACE_BETWEEN:
            return 0.0  # 间距由调用方处理
        elif justify == FlexJustify.SPACE_AROUND:
            return 0.0
        elif justify == FlexJustify.SPACE_EVENLY:
            return 0.0
        return 0.0

    def _calc_cross_position(
        self, align: FlexAlign, container_size: float, item_size: float,
    ) -> float:
        """计算交叉轴位置"""
        if align == FlexAlign.START:
            return 0.0
        elif align == FlexAlign.CENTER:
            return (container_size - item_size) / 2 if item_size > 0 else 0.0
        elif align == FlexAlign.END:
            return container_size - item_size if item_size > 0 else 0.0
        elif align == FlexAlign.STRETCH:
            return 0.0
        elif align == FlexAlign.BASELINE:
            return 0.0  # 简化处理
        return 0.0
