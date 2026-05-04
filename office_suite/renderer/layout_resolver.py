"""布局解析器 — 桥接 engine/layout 引擎与 IRPosition

设计方案第六章：布局引擎集成层。

当 DSL 元素使用 grid/flex/constraint 布局模式时，
本模块调用对应的 engine/layout 引擎计算绝对坐标，
返回 IRPosition 供渲染器直接使用。

数据流：
  IRNode (含 layout_mode + grid/flex 元数据)
    → LayoutResolver.resolve()
      → engine/layout/{GridLayout,FlexLayout,Solver}
        → IRPosition (mm 绝对坐标)

用法：
    resolver = LayoutResolver(container_width=254.0, container_height=142.875)
    positions = resolver.resolve_children(slide_node)
    # positions: dict[child_id, IRPosition]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM
from ..ir.types import IRNode, IRPosition, NodeType
from ..ir.layout_spec import (
    AbsolutePosition,
    FlexDirection,
    FlexJustify,
    FlexAlign,
    FlexPosition,
    FlexWrap,
    GridPosition,
    GridAlign,
)
from ..engine.layout.grid import GridLayout, GridCell
from ..engine.layout.flex import FlexLayout, FlexItem
from ..engine.layout.constraint import (
    Solver, Variable, eq, le, ge, Constraint, Priority,
    make_expression, Expression, Term,
)
from ..design.semantic_layouts import resolve_semantic_layout


# ============================================================
# 布局模式检测
# ============================================================

def detect_layout_mode(node: IRNode) -> str:
    """检测节点使用的布局模式

    优先级：
      1. node.extra["layout_mode"] — 显式声明（含语义布局名称）
      2. node.extra 中有 grid/flex 属性 → 推断
      3. 默认 "absolute"

    语义布局名称（如 card_grid_2x2）由 resolve_semantic_layout 解析为
    具体的 grid/flex 配置后注入 node.extra。
    """
    mode = node.extra.get("layout_mode")
    if mode:
        return mode

    # 推断：有 grid 属性 → grid，有 flex 属性 → flex
    if "grid" in node.extra:
        return "grid"
    if "flex" in node.extra:
        return "flex"
    if "constraints" in node.extra:
        return "constraint"

    return "absolute"


# ============================================================
# 布局解析器
# ============================================================

class LayoutResolver:
    """布局解析器 — 将容器子元素的布局规格解析为绝对坐标

    支持的布局模式：
      - absolute: 直接使用 IRPosition（默认）
      - relative: 百分比 → mm
      - grid: 栅格布局（12/24 列）
      - flex: 弹性布局（Flexbox 语义）
      - constraint: 约束求解（Cassowary 简化版）

    用法：
        resolver = LayoutResolver(SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM)
        positions = resolver.resolve_children(slide_node)
    """

    def __init__(
        self,
        container_width: float = SLIDE_WIDTH_MM,
        container_height: float = SLIDE_HEIGHT_MM,
    ):
        self.container_width = container_width
        self.container_height = container_height

    def resolve_children(
        self, container: IRNode,
    ) -> dict[str, IRPosition]:
        """解析容器所有子元素的位置

        Args:
            container: 容器节点（SLIDE 或 GROUP）

        Returns:
            {child.id 或 child索引: IRPosition}
        """
        # 语义布局名称解析：将 card_grid_2x2 等预设转为具体 grid/flex 配置
        mode = detect_layout_mode(container)
        resolved = resolve_semantic_layout(mode)
        if resolved is not None:
            mode = resolved["mode"]
            container.extra["layout_mode"] = mode
            if "grid" in resolved:
                container.extra.setdefault("grid", resolved["grid"])
            if "flex" in resolved:
                container.extra.setdefault("flex", resolved["flex"])

        if mode == "grid":
            return self._resolve_grid(container)
        elif mode == "flex":
            return self._resolve_flex(container)
        elif mode == "constraint":
            return self._resolve_constraint(container)
        else:
            # absolute / relative: 直接使用已有 IRPosition
            return self._resolve_absolute(container)

    def _resolve_absolute(self, container: IRNode) -> dict[str, IRPosition]:
        """绝对/相对布局 — 直接使用 IRPosition"""
        result = {}
        for i, child in enumerate(container.children):
            key = child.id or str(i)
            pos = child.position or IRPosition()
            # 相对坐标 → 绝对坐标
            if pos.is_relative:
                pos = IRPosition(
                    x_mm=pos.x_mm / 100 * self.container_width,
                    y_mm=pos.y_mm / 100 * self.container_height,
                    width_mm=pos.width_mm / 100 * self.container_width,
                    height_mm=pos.height_mm / 100 * self.container_height,
                    is_center=pos.is_center,
                    is_auto=pos.is_auto,
                )
            result[key] = pos
        return result

    def _resolve_grid(self, container: IRNode) -> dict[str, IRPosition]:
        """栅格布局 — 使用 engine/layout/grid.py

        子元素有两种放置方式：
          1. 显式 grid 元数据（column/row/span）→ 精确放置
          2. 无 grid 元数据 → 自动按顺序填充（auto-flow: row）
        """
        grid_cfg = container.extra.get("grid", {})
        columns = grid_cfg.get("columns", 12)
        gutter = grid_cfg.get("gutter", 2.0)
        row_height = grid_cfg.get("row_height")

        # 页边距（来自语义布局配置或显式声明）
        margin = grid_cfg.get("margin", (0.0, 0.0, 0.0, 0.0))
        if isinstance(margin, (int, float)):
            margin = (float(margin), float(margin), float(margin), float(margin))
        padding = grid_cfg.get("padding", 0.0)

        layout = GridLayout(
            columns=columns,
            container_width=self.container_width,
            container_height=self.container_height,
            gutter=gutter,
            row_height=row_height,
            margin=margin,
            padding=padding,
        )

        result = {}
        # 自动放置游标：row 从 1 开始，col 从 1 开始
        auto_row = 1
        auto_col = 1

        for i, child in enumerate(container.children):
            key = child.id or str(i)

            # 已有绝对坐标的子元素直接保留，不参与网格计算
            if self._has_explicit_position(child):
                result[key] = child.position
                continue

            grid_meta = child.extra.get("grid", {})

            if grid_meta:
                # 显式放置
                col = grid_meta.get("column", 1)
                col_span = grid_meta.get("span", grid_meta.get("column_span", 1))
                row = grid_meta.get("row", 1)
                row_span = grid_meta.get("row_span", 1)
            else:
                # 自动放置：按顺序从左到右、从上到下填充
                col = auto_col
                col_span = 1
                row = auto_row
                row_span = 1

            grid_pos = GridPosition(
                column=col,
                column_span=col_span,
                row=row,
                row_span=row_span,
                columns=columns,
                align=GridAlign(grid_meta.get("align", "stretch") if grid_meta else "stretch"),
            )
            abs_pos = layout.resolve(grid_pos)
            result[key] = IRPosition(
                x_mm=abs_pos.x,
                y_mm=abs_pos.y,
                width_mm=abs_pos.width,
                height_mm=abs_pos.height,
            )

            # 更新自动放置游标
            next_col = col + col_span
            if next_col > columns:
                auto_row = row + row_span
                auto_col = 1
            else:
                auto_row = row
                auto_col = next_col

        return result

    def _resolve_flex(self, container: IRNode) -> dict[str, IRPosition]:
        """弹性布局 — 使用 engine/layout/flex.py"""
        flex_cfg = container.extra.get("flex", {})
        direction = FlexDirection(flex_cfg.get("direction", "row"))
        justify = FlexJustify(flex_cfg.get("justify", "start"))
        align = FlexAlign(flex_cfg.get("align", "start"))
        wrap = FlexWrap(flex_cfg.get("wrap", "nowrap"))
        align_content = FlexAlign(flex_cfg.get("align_content", "start"))
        gap = flex_cfg.get("gap", 0.0)
        row_gap = flex_cfg.get("row_gap", 0.0)

        # 页边距
        margin = flex_cfg.get("margin", (0.0, 0.0, 0.0, 0.0))
        if isinstance(margin, (int, float)):
            margin = (float(margin), float(margin), float(margin), float(margin))

        layout = FlexLayout(
            container_width=self.container_width,
            container_height=self.container_height,
            margin=margin,
        )

        flex_pos = FlexPosition(
            direction=direction,
            justify=justify,
            align=align,
            wrap=wrap,
            align_content=align_content,
            gap=gap,
            row_gap=row_gap,
        )

        items = []
        explicit_positions: dict[int, IRPosition] = {}
        for i, child in enumerate(container.children):
            if self._has_explicit_position(child):
                explicit_positions[i] = child.position
                continue
            flex_meta = child.extra.get("flex", {})
            pos = child.position or IRPosition()
            items.append(FlexItem(
                width=pos.width_mm,
                height=pos.height_mm,
                grow=flex_meta.get("grow", 0.0),
                shrink=flex_meta.get("shrink", 1.0),
                basis=flex_meta.get("basis"),
                order=flex_meta.get("order", 0),
                align_self=FlexAlign(flex_meta["align_self"])
                           if "align_self" in flex_meta else None,
            ))

        abs_positions = layout.resolve(flex_pos, items)

        result = {}
        flex_idx = 0
        for i, child in enumerate(container.children):
            key = child.id or str(i)
            if i in explicit_positions:
                result[key] = explicit_positions[i]
            elif flex_idx < len(abs_positions) and abs_positions[flex_idx] is not None:
                ap = abs_positions[flex_idx]
                result[key] = IRPosition(
                    x_mm=ap.x,
                    y_mm=ap.y,
                    width_mm=ap.width,
                    height_mm=ap.height,
                )
                flex_idx += 1
            else:
                result[key] = child.position or IRPosition()
                flex_idx += 1

        return result

    @staticmethod
    def _has_explicit_position(child: IRNode) -> bool:
        """判断子元素是否已有显式绝对坐标（非默认零值）

        仅当 x 或 y 坐标非零时才视为"已定位"。
        仅有 width/height 不算——这些是尺寸提示，不是位置。
        """
        pos = child.position
        if pos is None:
            return False
        return (pos.x_mm != 0.0 or pos.y_mm != 0.0)

    def _resolve_constraint(self, container: IRNode) -> dict[str, IRPosition]:
        """约束布局 — 使用 engine/layout/constraint.py

        每个子元素在 extra.constraints 中声明约束条件，
        求解器计算所有变量的最终值。

        约束声明格式：
          constraints:
            - type: eq
              lhs: { var: "self.x", coeff: 1 }
              rhs: { value: 10 }
            - type: le
              lhs: { var: "self.right" }
              rhs: { var: "parent.width" }
        """
        solver = Solver()

        # 添加容器变量
        parent_w_var = solver.add_variable("parent.width", self.container_width)
        parent_h_var = solver.add_variable("parent.height", self.container_height)
        parent_vars = {"width": parent_w_var, "height": parent_h_var}

        # 为每个子元素创建变量
        child_vars: dict[int, dict[str, Variable]] = {}
        for i, child in enumerate(container.children):
            prefix = f"child_{i}"
            vars_dict = {
                "x": solver.add_variable(f"{prefix}.x", 0.0),
                "y": solver.add_variable(f"{prefix}.y", 0.0),
                "width": solver.add_variable(f"{prefix}.width", 0.0),
                "height": solver.add_variable(f"{prefix}.height", 0.0),
                "right": solver.add_variable(f"{prefix}.right", 0.0),
                "bottom": solver.add_variable(f"{prefix}.bottom", 0.0),
                "center_x": solver.add_variable(f"{prefix}.center_x", 0.0),
                "center_y": solver.add_variable(f"{prefix}.center_y", 0.0),
            }
            child_vars[i] = vars_dict

            # 默认约束：right = x + width, bottom = y + height
            solver.add_constraint(eq(
                make_expression(vars_dict["right"]),
                make_expression(vars_dict["x"]) + make_expression(vars_dict["width"]),
            ))
            solver.add_constraint(eq(
                make_expression(vars_dict["bottom"]),
                make_expression(vars_dict["y"]) + make_expression(vars_dict["height"]),
            ))
            solver.add_constraint(eq(
                make_expression(vars_dict["center_x"]),
                make_expression(vars_dict["x"]) + make_expression(vars_dict["width"], 0.5),
            ))
            solver.add_constraint(eq(
                make_expression(vars_dict["center_y"]),
                make_expression(vars_dict["y"]) + make_expression(vars_dict["height"], 0.5),
            ))

            # 使用已有位置作为初始值提示
            pos = child.position or IRPosition()
            if pos.width_mm > 0:
                vars_dict["width"].value = pos.width_mm
            if pos.height_mm > 0:
                vars_dict["height"].value = pos.height_mm
            vars_dict["x"].value = pos.x_mm
            vars_dict["y"].value = pos.y_mm

        # 添加用户自定义约束
        for i, child in enumerate(container.children):
            constraints = child.extra.get("constraints", [])
            for c_def in constraints:
                self._add_user_constraint(solver, c_def, child_vars[i], parent_vars)

        # 求解
        solver.solve()

        # 收集结果
        result = {}
        for i, child in enumerate(container.children):
            key = child.id or str(i)
            v = child_vars[i]
            result[key] = IRPosition(
                x_mm=round(v["x"].value, 2),
                y_mm=round(v["y"].value, 2),
                width_mm=round(v["width"].value, 2),
                height_mm=round(v["height"].value, 2),
            )

        return result

    def _add_user_constraint(
        self,
        solver: Solver,
        c_def: dict[str, Any],
        child_vars: dict[str, Variable],
        parent_vars: dict[str, Variable],
    ) -> None:
        """解析用户约束定义并添加到求解器"""
        c_type = c_def.get("type", "eq")

        lhs = self._parse_expression(c_def.get("lhs", {}), child_vars, parent_vars)
        rhs = self._parse_expression(c_def.get("rhs", {}), child_vars, parent_vars)

        if lhs is None or rhs is None:
            return

        priority_str = c_def.get("priority", "required")
        priority = {
            "required": Priority.REQUIRED,
            "high": Priority.HIGH,
            "strong": Priority.STRONG,
            "medium": Priority.MEDIUM,
            "low": Priority.WEAK,
            "weak": Priority.WEAK,
        }.get(priority_str, Priority.REQUIRED)

        if c_type == "eq":
            solver.add_constraint(eq(lhs, rhs, priority))
        elif c_type == "le":
            solver.add_constraint(le(lhs, rhs, priority))
        elif c_type == "ge":
            solver.add_constraint(ge(lhs, rhs, priority))

    def _parse_expression(
        self,
        spec: dict[str, Any],
        child_vars: dict[str, Variable],
        parent_vars: dict[str, Variable] | None = None,
    ) -> Expression | Variable | float | None:
        """解析表达式规格

        格式：
          { var: "self.x" }           → 子元素变量
          { var: "self.x", coeff: 2 } → 带系数的子元素变量
          { var: "parent.width" }     → 容器变量
          { value: 10 }              → 常量
        """
        if "value" in spec:
            return float(spec["value"])

        if "var" in spec:
            var_name = spec["var"]
            coeff = spec.get("coeff", 1.0)

            # self.* → child_vars
            if var_name.startswith("self."):
                key = var_name[5:]
                if key in child_vars:
                    return make_expression(child_vars[key], coeff)
            # parent.* → parent_vars
            elif var_name.startswith("parent.") and parent_vars:
                key = var_name[7:]
                if key in parent_vars:
                    return make_expression(parent_vars[key], coeff)

        return None
