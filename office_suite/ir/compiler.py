"""DSL → IR 编译器 — 将 DSL Document 编译为 IRDocument

核心职责：
1. 将 DSL 文档类型安全地转换为 IR 节点树
2. 解析坐标（mm/% → mm 绝对值）
3. 样式级联（theme → document → slide → element → inline）
4. 保留原始 DSL 路径用于调试

数据流：
  YAML 文件 → dsl/parser.py::parse_yaml() → Document 对象
  Document  → [本文件]::compile_document() → IRDocument 树
  IRDocument → renderer/pptx/deck.py::PPTXRenderer.render() → .pptx 文件

坐标映射规则（设计方案第四章）：
  mm  → PPTX: × 36000 (EMU)    DOCX: × 1440 (Twips)    PDF: 直接使用
  %   → 相对于父容器尺寸计算后再走 mm 映射
  auto → 渲染器自行计算（文本根据字号+换行，图片根据原始比例）
  center → (parent_width - self_width) / 2
"""

from typing import Any

from ..dsl.parser import parse_style
from ..dsl.schema import (
    Document,
    Element,
    PositionSpec,
    Slide,
    StyleSpec,
)
from .cascade import cascade_style, cascade_style_by_name, DEFAULT_THEME_STYLES
from .types import (
    IRAnimation,
    IRDocument,
    IRNode,
    IRPosition,
    IRStyle,
    NodeType,
)


# ============================================================
# 坐标转换
# ============================================================

def _parse_length(value: str | float | None, parent_size: float = 0) -> tuple[float, bool, bool]:
    """解析长度值，返回 (mm值, is_relative, is_auto)"""
    if value is None:
        return 0.0, False, False
    if isinstance(value, (int, float)):
        return float(value), False, False
    if value == "auto":
        return 0.0, False, True
    if value == "center":
        return 0.0, False, False  # center 由 position.center 标记处理

    s = str(value).strip()
    if s.endswith("mm"):
        return float(s[:-2]), False, False
    if s.endswith("%"):
        pct = float(s[:-1]) / 100.0
        return parent_size * pct, True, False
    if s.endswith("in"):
        # 英寸 → mm (1 in = 25.4 mm)
        return float(s[:-2]) * 25.4, False, False
    if s.endswith("pt"):
        # pt → mm (1 pt = 0.3528 mm)
        return float(s[:-2]) * 0.3528, False, False
    # 默认当作 mm
    try:
        return float(s), False, False
    except ValueError:
        return 0.0, False, False


def compile_position(pos: PositionSpec | None, parent_w: float = 254.0, parent_h: float = 142.875) -> IRPosition:
    """将 DSL PositionSpec 编译为 IRPosition（mm 单位）

    默认父容器尺寸：标准 16:9 幻灯片 = 254mm x 142.875mm (10" x 5.625")
    注意：190.5mm 是 4:3 幻灯片高度（7.5"），16:9 正确高度是 142.875mm（5.625"）
    """
    if pos is None:
        return IRPosition()

    x, _, _ = _parse_length(pos.x, parent_w)
    y, _, _ = _parse_length(pos.y, parent_h)
    w, w_rel, w_auto = _parse_length(pos.width, parent_w)
    h, h_rel, h_auto = _parse_length(pos.height, parent_h)

    # bottom 定位：从底部向上计算
    if pos.bottom is not None:
        bottom_mm, _, _ = _parse_length(pos.bottom, parent_h)
        y = parent_h - bottom_mm - h

    return IRPosition(
        x_mm=x,
        y_mm=y,
        width_mm=w,
        height_mm=h,
        is_relative=w_rel or h_rel,
        is_center=pos.center,
        is_auto=w_auto or h_auto,
    )


# ============================================================
# 样式编译
# ============================================================

def compile_style(style: StyleSpec | None) -> IRStyle | None:
    """将 DSL StyleSpec 编译为 IRStyle"""
    if style is None:
        return None

    ir = IRStyle()
    if style.font:
        ir.font_family = style.font.family
        ir.font_size = style.font.size
        ir.font_weight = style.font.weight
        ir.font_italic = style.font.italic
        ir.font_color = style.font.color
    if style.fill:
        ir.fill_color = style.fill.color
        ir.fill_gradient = _gradient_to_dict(style.fill.gradient) if style.fill.gradient else None
        ir.fill_opacity = style.fill.opacity
    if style.shadow:
        ir.shadow = {
            "blur": style.shadow.blur,
            "offset": style.shadow.offset,
            "color": style.shadow.color,
        }
    if style.border:
        ir.border = style.border
    if style.text_effect:
        ir.text_effect = style.text_effect
    return ir


def _gradient_to_dict(grad) -> dict[str, Any]:
    return {
        "type": grad.type,
        "angle": grad.angle,
        "stops": grad.stops,
    }


# ============================================================
# 元素编译
# ============================================================

def _parse_animations(raw: dict | None) -> list[IRAnimation]:
    """将 DSL animation 字典解析为 IRAnimation 列表

    支持格式：
      animation: { effect: fade, duration: 0.5 }
      animation:
        - { effect: fade_in, trigger: on_click }
        - { effect: pulse, trigger: after_previous }
    """
    if not raw:
        return []

    # 支持单个动画 dict 或列表
    items = raw if isinstance(raw, list) else [raw]

    animations = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # 动画类型推断
        anim_type = item.get("type", "entry")
        effect = item.get("effect", item.get("animation", "fade"))

        # 强调动画自动设置 anim_type
        emphasis_effects = {"pulse", "shake", "glow_pulse", "breathe", "float",
                            "spin_emphasis", "grow", "shrink"}
        if effect in emphasis_effects:
            anim_type = "emphasis"

        # 退出动画
        exit_effects = {"fade_out", "slide_out_up", "slide_out_down", "slide_out_left",
                        "slide_out_right", "zoom_out_exit"}
        if effect in exit_effects:
            anim_type = "exit"

        animations.append(IRAnimation(
            anim_type=anim_type,
            effect=effect,
            trigger=item.get("trigger", "on_click"),
            duration=item.get("duration", 0.5),
            delay=item.get("delay", 0.0),
            easing=item.get("easing", "ease_out"),
            repeat=item.get("repeat", 0),
            direction=item.get("direction", ""),
            extra={k: v for k, v in item.items()
                   if k not in ("type", "effect", "animation", "trigger",
                                "duration", "delay", "easing", "repeat", "direction")},
        ))

    return animations


# DSL type → IR NodeType 映射
TYPE_MAP = {
    "text": NodeType.TEXT,
    "image": NodeType.IMAGE,
    "shape": NodeType.SHAPE,
    "table": NodeType.TABLE,
    "chart": NodeType.CHART,
    "group": NodeType.GROUP,
    "video": NodeType.VIDEO,
    "audio": NodeType.AUDIO,
    "diagram": NodeType.DIAGRAM,
    "code": NodeType.CODE,
}


def compile_element(
    elem: Element,
    global_styles: dict[str, StyleSpec],
    doc_styles: dict[str, IRStyle],  # 已编译的 IR 全局样式
    theme_name: str = "default",
    parent_w: float = 254.0,
    parent_h: float = 142.875,
    path: str = "",
) -> IRNode:
    """将 DSL Element 编译为 IRNode

    样式级联：theme → doc_global → element_style_ref → element_inline
    """
    node_type = TYPE_MAP.get(elem.type, NodeType.SHAPE)

    # 样式：支持字符串引用或内联（dict 或 StyleSpec）
    style_ref = None
    inline_style = None

    if isinstance(elem.style, str):
        style_ref = elem.style
    elif isinstance(elem.style, dict):
        # 原始 YAML dict → StyleSpec → IRStyle
        parsed = parse_style(elem.style)
        if parsed:
            inline_style = compile_style(parsed)
    elif isinstance(elem.style, StyleSpec):
        inline_style = compile_style(elem.style)

    # 样式级联
    theme_styles = DEFAULT_THEME_STYLES  # P0 使用内置主题
    cascaded_style = cascade_style_by_name(
        style_name=style_ref,
        theme_styles=theme_styles,
        doc_styles=doc_styles,
        slide_style=None,  # slide 级样式在后续迭代添加
        element_style=inline_style,
    )

    # 位置
    ir_pos = compile_position(elem.position, parent_w, parent_h)

    # 处理 size 字段覆盖 position 的宽高
    if elem.size:
        w_raw = elem.size.get("width")
        h_raw = elem.size.get("height")
        if w_raw is not None:
            w_mm, _, _ = _parse_length(w_raw, parent_w)
            ir_pos.width_mm = w_mm
        if h_raw is not None:
            h_mm, _, _ = _parse_length(h_raw, parent_h)
            ir_pos.height_mm = h_mm

    # 图片 source 处理
    source = elem.source
    if isinstance(source, dict):
        source = source  # 保留 dict 形式

    # 子节点 — 支持 stack 布局自动排列
    children = []
    stack_layout = elem.extra.get("layout", "") == "stack"
    stack_spacing = float(elem.extra.get("spacing", 5))  # 默认 5mm 间距
    stack_cursor_y = float(elem.extra.get("padding_top", 0))  # 起始 y 偏移

    for i, child in enumerate(elem.children):
        child_path = f"{path}/{child.type}[{i}]"

        # stack 布局：自动计算子元素 y 坐标
        if stack_layout and child.position is None:
            # shape 默认高度
            default_h = None
            if child.type == "shape":
                shape_type = child.extra.get("shape_type", "rectangle")
                if shape_type == "line":
                    default_h = 2
                else:
                    default_h = 10

            # 处理 extra.center → position.center
            extra_copy = dict(child.extra)
            center_flag = extra_copy.pop("center", False)

            child_pos = PositionSpec(
                x=elem.extra.get("padding_left", 0),
                y=stack_cursor_y,
                width=elem.extra.get("content_width"),
                height=default_h,
                center=bool(center_flag),
            )
            child = Element(
                type=child.type,
                content=child.content,
                source=child.source,
                style=child.style,
                position=child_pos,
                data_ref=child.data_ref,
                chart_type=child.chart_type,
                query=child.query,
                prompt=child.prompt,
                size=child.size,
                opacity=child.opacity,
                filter=child.filter,
                animation=child.animation,
                children=child.children,
                extra=extra_copy,
            )

        ir_child = compile_element(
            child, global_styles, doc_styles, theme_name,
            ir_pos.width_mm or parent_w, ir_pos.height_mm or parent_h, child_path,
        )
        children.append(ir_child)

        # stack 布局：更新游标 y
        if stack_layout:
            child_h = ir_child.position.height_mm if ir_child.position else 0
            if child_h <= 0:
                # 根据元素类型估算高度
                if ir_child.node_type == NodeType.TEXT:
                    font_size = ir_child.style.font_size if ir_child.style else 18
                    child_h = max(font_size * 0.5, 8)
                elif ir_child.node_type == NodeType.SHAPE:
                    child_h = 2
                else:
                    child_h = 10
            stack_cursor_y += child_h + stack_spacing

    # 动画
    animations = _parse_animations(elem.animation)

    return IRNode(
        node_type=node_type,
        id=elem.extra.get("id", ""),
        content=elem.content,
        source=source,
        position=ir_pos,
        style=cascaded_style,
        style_ref=style_ref,
        children=children,
        data_ref=elem.data_ref,
        chart_type=elem.chart_type,
        animations=animations,
        extra={k: v for k, v in elem.extra.items() if k != "id"},
        source_path=path,
    )


# ============================================================
# 幻灯片编译
# ============================================================

def _estimate_element_height(elem: Element, content_width: float) -> float:
    """估算元素高度（mm）

    用于 stack 布局的高度预估和自动分页判断。
    """
    # 如果有显式 position 且有 height，直接使用
    if elem.position and elem.position.height:
        h_raw = str(elem.position.height).replace("mm", "").strip()
        try:
            return float(h_raw)
        except ValueError:
            pass

    # shape 类型
    if elem.type == "shape":
        shape_type = elem.extra.get("shape_type", "rectangle")
        if shape_type == "line":
            return 2
        # 有 size.height 时使用
        if elem.size and elem.size.get("height"):
            h_raw = str(elem.size["height"]).replace("mm", "").strip()
            try:
                return float(h_raw)
            except ValueError:
                pass
        return 10  # 默认 shape 高度

    # table 类型
    if elem.type == "table":
        if elem.position and elem.position.height:
            h_raw = str(elem.position.height).replace("mm", "").strip()
            try:
                return float(h_raw)
            except ValueError:
                pass
        return 60  # 默认表格高度

    # chart 类型
    if elem.type == "chart":
        return 80  # 默认图表高度

    # image 类型
    if elem.type == "image":
        return 60  # 默认图片高度

    # text 类型（核心逻辑）
    if elem.type == "text":
        content = elem.content or ""
        if not content:
            return 8  # 空文本

        # 从 style 中获取字号
        font_size = 18  # 默认字号
        if isinstance(elem.style, dict):
            font_spec = elem.style.get("font", {})
            if isinstance(font_spec, dict):
                font_size = font_spec.get("size", 18)
        elif isinstance(elem.style, StyleSpec) and elem.style.font:
            font_size = elem.style.font.size

        # 估算文本宽度：中文字符约 0.6 * 字号，英文约 0.35 * 字号
        text_width_pt = 0
        for ch in content:
            if ord(ch) > 127:  # 中文字符
                text_width_pt += font_size * 0.6
            else:
                text_width_pt += font_size * 0.35

        # 转换为 mm (1pt ≈ 0.3528mm)
        text_width_mm = text_width_pt * 0.3528

        # 防止 content_width 为零或负数导致除零
        safe_width = max(content_width, 1.0)

        # 计算行数
        lines = max(1, int(text_width_mm / safe_width) + 1)

        # 每行高度：字号 * 1.2（行间距）* 0.3528mm/pt
        line_height_mm = font_size * 1.2 * 0.3528

        # 总高度 = 行数 * 行高 + 上下 margin
        return lines * line_height_mm + 2.54

    # group 和其他类型
    return 10


def _is_chapter_title(elem: Element) -> bool:
    """判断元素是否是章节标题（一级标题）

    章节标题特征：
    - 样式为 heading/accent/title/subtitle
    - 或者是大字号（>= 36pt）的文本
    - 排除短数字装饰元素（如 "01", "02" 等章节编号）
    """
    if elem.type != "text":
        return False

    content = (elem.content or "").strip()

    # 排除短数字装饰元素（如 "01", "02", "06" 等章节编号）
    if content.isdigit() and len(content) <= 3:
        return False

    # 检查样式名
    if isinstance(elem.style, str) and elem.style in ("heading", "accent", "title", "subtitle"):
        return True

    # 检查字号
    if isinstance(elem.style, dict):
        font_spec = elem.style.get("font", {})
        if isinstance(font_spec, dict) and font_spec.get("size", 18) >= 36:
            return True

    # 检查 StyleSpec
    if isinstance(elem.style, StyleSpec) and elem.style.font:
        if elem.style.font.size >= 36:
            return True

    return False


def _is_list_item(elem: Element) -> bool:
    """判断元素是否是列表项（以 • 开头的文本）"""
    if elem.type != "text":
        return False
    content = elem.content or ""
    return content.startswith("•") or content.startswith("·") or content.startswith("-")


def _is_chapter_prefix(elem: Element) -> bool:
    """判断元素是否是章节标题的前缀装饰（如 "01", "02" 等数字编号）

    这类元素应与后面的章节标题归为同一组。
    """
    if elem.type != "text":
        return False
    content = (elem.content or "").strip()
    # 纯数字且长度 <= 3（如 "01", "02", "06"）
    if content.isdigit() and len(content) <= 3:
        return True
    return False


def _group_elements_by_chapter(elements: list[Element]) -> list[list[Element]]:
    """将元素按章节分组

    分组规则：
    - 章节标题（一级标题）开始一个新的分组
    - 标题前面的装饰元素（如数字编号、分隔线）归入新分组
    - 标题后面的所有内容（直到下一个标题）都属于这个分组
    - 第一个分组可以是"前言"（标题前的内容）

    Returns:
        分组后的元素列表
    """
    if not elements:
        return [[]]

    groups: list[list[Element]] = []
    current_group: list[Element] = []
    pending: list[Element] = []  # 等待归属的前缀元素

    for elem in elements:
        if _is_chapter_title(elem):
            # 章节标题：开始新分组，pending 元素归入新分组
            if current_group:
                groups.append(current_group)
            current_group = pending + [elem]
            pending = []
        elif _is_chapter_prefix(elem) and not current_group:
            # 前缀元素且当前还没有分组内容 → 暂存到 pending
            pending.append(elem)
        elif _is_chapter_prefix(elem) and current_group:
            # 前缀元素但已有分组内容 → 也暂存到 pending
            # （可能是上一章的结尾数字，但更可能是下一章的开头编号）
            pending.append(elem)
        else:
            # 普通内容元素
            if pending:
                # 有 pending 元素，先检查它们应该归哪
                # 如果当前组已有内容，pending 可能是下一章的前缀，先保留
                current_group.extend(pending)
                pending = []
            current_group.append(elem)

    # 保存最后一个分组
    if current_group or pending:
        groups.append(current_group + pending)

    return groups if groups else [[]]


def _paginate_group(
    group: list[Element],
    content_width: float,
    max_height: float,
    spacing: float,
    padding_top: float,
) -> list[list[Element]]:
    """对单个分组进行分页

    分页规则：
    - 标题和第一个内容元素尽量在一起
    - 列表项尽量在一起
    - 如果单个元素就超出页面，单独一页
    """
    if not group:
        return [[]]

    pages: list[list[Element]] = []
    current_page: list[Element] = []
    current_height = padding_top
    last_list_break = -1  # 最近的列表项结束位置

    for i, elem in enumerate(group):
        elem_height = _estimate_element_height(elem, content_width)

        # 检查加入当前元素后是否超出页面
        would_overflow = (current_height + elem_height) > max_height

        if would_overflow and current_page:
            # 需要分页
            # 如果当前元素是列表项，且前面有列表项，尝试在列表开始前分页
            if _is_list_item(elem) and last_list_break >= 0:
                # 在列表开始前分页
                split_point = last_list_break + 1
                pages.append(current_page[:split_point])
                current_page = current_page[split_point:] + [elem]
                # 重新计算高度
                current_height = padding_top
                for r in current_page[:-1]:
                    current_height += _estimate_element_height(r, content_width) + spacing
                current_height += elem_height + spacing
            else:
                # 强制在当前位置前分页
                pages.append(current_page)
                current_page = [elem]
                current_height = padding_top + elem_height + spacing
        else:
            # 不需要分页
            current_page.append(elem)
            current_height += elem_height + spacing

        # 更新列表项结束位置
        if _is_list_item(elem):
            if not (i > 0 and _is_list_item(group[i - 1])):
                # 这是列表的第一项
                last_list_break = len(current_page) - 1

    # 最后一页
    if current_page:
        pages.append(current_page)

    return pages if pages else [[]]


def _split_elements_for_pagination(
    elements: list[Element],
    content_width: float,
    max_height: float,
    spacing: float,
    padding_top: float,
) -> list[list[Element]]:
    """将元素列表按语义分页

    分页策略：
    1. 先按章节分组（一级标题 + 后续内容）
    2. 对每组内容进行分页
    3. 章节间不混排

    Args:
        elements: 原始元素列表
        content_width: 内容宽度（mm）
        max_height: 最大可用高度（mm）
        spacing: 元素间距（mm）
        padding_top: 上边距（mm）

    Returns:
        分页后的元素列表（每页一个列表）
    """
    if not elements:
        return [[]]

    # 第一步：按章节分组
    chapter_groups = _group_elements_by_chapter(elements)

    # 第二步：对每组进行分页
    pages: list[list[Element]] = []
    for group in chapter_groups:
        group_pages = _paginate_group(group, content_width, max_height, spacing, padding_top)
        pages.extend(group_pages)

    return pages if pages else [[]]


def compile_slide(
    slide: Slide,
    global_styles: dict[str, StyleSpec],
    doc_ir_styles: dict[str, IRStyle],
    theme_name: str,
    index: int,
) -> list[IRNode]:
    """将 DSL Slide 编译为 IRNode 列表 (NodeType.SLIDE)

    支持 stack 布局模式：layout: stack
    - 子元素自动从上到下排列，不需要手动指定 y 坐标
    - 支持 spacing（间距）、padding_top/left（内边距）、content_width（内容宽度）
    - 未指定 position 的元素自动进入 stack 流
    - 指定了 position 的元素不受 stack 影响（绝对定位）
    - 内容超出时自动分页，保持语义连贯

    Returns:
        IRNode 列表（可能包含多个 slide，如果发生了自动分页）
    """
    # 检测 slide 级别的 stack 布局
    slide_stack = slide.layout == "stack"
    slide_extra = slide.background or {}
    if isinstance(slide_extra, dict):
        stack_spacing = float(slide_extra.get("spacing", 8))  # 默认 8mm 间距
        padding_top = float(slide_extra.get("padding_top", 15))  # 默认上边距 15mm
        padding_left = float(slide_extra.get("padding_left", 30))  # 默认左边距 30mm
        content_width = float(slide_extra.get("content_width", 194))  # 默认内容宽度 194mm
    else:
        stack_spacing = 8
        padding_top = 15
        padding_left = 30
        content_width = 194

    # 自动分页：stack 布局且没有绝对定位元素时
    if slide_stack:
        # 检查是否有绝对定位元素
        has_absolute = any(e.position is not None for e in slide.elements)

        if not has_absolute:
            # 预估总高度
            total_height = padding_top
            for elem in slide.elements:
                total_height += _estimate_element_height(elem, content_width) + stack_spacing

            # 如果超出页面高度，进行分页
            if total_height > 142.875:
                element_pages = _split_elements_for_pagination(
                    slide.elements, content_width, 142.875, stack_spacing, padding_top
                )
            else:
                element_pages = [slide.elements]
        else:
            element_pages = [slide.elements]
    else:
        element_pages = [slide.elements]

    # 编译每一页
    slides = []
    for page_idx, page_elements in enumerate(element_pages):
        children = []
        stack_cursor_y = padding_top

        for i, elem in enumerate(page_elements):
            # stack 布局：为没有 position 的元素自动计算位置
            if slide_stack and elem.position is None:
                # 估算元素高度
                default_h = _estimate_element_height(elem, content_width)

                # 处理 extra.center → position.center
                extra_copy = dict(elem.extra)
                center_flag = extra_copy.pop("center", False)

                auto_pos = PositionSpec(
                    x=padding_left,
                    y=stack_cursor_y,
                    width=content_width,
                    height=default_h,
                    center=bool(center_flag),
                )
                elem = Element(
                    type=elem.type,
                    content=elem.content,
                    source=elem.source,
                    style=elem.style,
                    position=auto_pos,
                    data_ref=elem.data_ref,
                    chart_type=elem.chart_type,
                    query=elem.query,
                    prompt=elem.prompt,
                    size=elem.size,
                    opacity=elem.opacity,
                    filter=elem.filter,
                    animation=elem.animation,
                    children=elem.children,
                    extra=extra_copy,
                )

            ir_elem = compile_element(
                elem, global_styles, doc_ir_styles, theme_name,
                path=f"slide[{index}]/{elem.type}[{i}]",
            )
            children.append(ir_elem)

            # stack 布局：更新游标 y
            if slide_stack and ir_elem.position:
                child_h = ir_elem.position.height_mm
                if child_h <= 0:
                    child_h = _estimate_element_height(
                        page_elements[i], content_width
                    )
                stack_cursor_y += child_h + stack_spacing

        extra = {}
        if slide.background:
            extra["background"] = slide.background
        if slide.transition:
            extra["transition"] = slide.transition

        slide_node = IRNode(
            node_type=NodeType.SLIDE,
            content=None,
            position=IRPosition(x_mm=0, y_mm=0, width_mm=254, height_mm=142.875),
            children=children,
            extra=extra,
            source_path=f"slide[{index}]" + (f".{page_idx}" if page_idx > 0 else ""),
        )
        slides.append(slide_node)

    return slides


# ============================================================
# 文档编译（入口）
# ============================================================

def compile_document(doc: Document) -> IRDocument:
    """将 DSL Document 编译为 IRDocument"""
    # 编译全局样式 → IR 样式表
    doc_ir_styles = {}
    for name, style_spec in doc.styles.items():
        doc_ir_styles[name] = compile_style(style_spec) or IRStyle()

    # 编译幻灯片
    slides = []
    for i, slide in enumerate(doc.slides):
        slide_nodes = compile_slide(slide, doc.styles, doc_ir_styles, doc.theme, i)
        slides.extend(slide_nodes)  # compile_slide 返回列表（可能分页）

    # 提取 data binding 的 inline 数据
    resolved_data = {}
    for key, binding in doc.data.items():
        if hasattr(binding, 'inline') and binding.inline is not None:
            resolved_data[key] = binding.inline
        elif hasattr(binding, 'source') and binding.source:
            resolved_data[key] = binding.source  # 外部源引用

    return IRDocument(
        version=doc.version,
        doc_type=doc.type.value,
        theme=doc.theme,
        title=doc.title,
        styles=doc_ir_styles,
        data=resolved_data,
        children=slides,
        raw_dsl=doc.raw,
    )
