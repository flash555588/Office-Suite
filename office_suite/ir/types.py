"""IR 节点类型系统 — 核心中间表示层

类比 LLVM IR：所有设计意图最终编译为 IR 节点，再由渲染器后端输出。

架构位置：dsl/parser.py → ir/compiler.py → [本文件] → renderer/*/deck.py
数据流：YAML DSL → Document 对象 → IRDocument 树 → 各格式渲染器

核心设计决策：
- NodeType 枚举定义了所有合法节点，分为容器节点和叶子节点
- CONTAINMENT_RULES 定义父子包含关系，渲染前校验防止非法嵌套
- IRStyle 所有字段 Optional(None)，级联时只覆盖非 None 字段
- IRNode.source_path 保留 DSL 原始路径，便于调试和错误定位
"""

import json
from dataclasses import dataclass, field, fields, asdict
from enum import Enum
from typing import Any, Optional


class NodeType(Enum):
    """IR 节点类型枚举"""
    # 容器节点
    DOCUMENT = "document"
    SLIDE = "slide"
    SECTION = "section"
    GROUP = "group"

    # 内容节点（P0）
    TEXT = "text"
    IMAGE = "image"
    SHAPE = "shape"
    TABLE = "table"
    CHART = "chart"

    # 内容节点（P1+）
    VIDEO = "video"
    AUDIO = "audio"
    DIAGRAM = "diagram"
    CODE = "code"

    # 内容节点（P2/P3）
    MODEL_3D = "3d_model"
    MAP = "map"


# 包含约束：哪些节点可以包含哪些子节点
# 设计意图：在 IR 层面就拦截非法嵌套（如 TEXT 内包含 SLIDE），
# 而不是等到渲染器报错。这和 TypeScript 的类型系统思路一致。
CONTAINMENT_RULES: dict[NodeType, set[NodeType]] = {
    NodeType.DOCUMENT: {NodeType.SLIDE, NodeType.SECTION},
    NodeType.SECTION: {NodeType.SLIDE},
    NodeType.SLIDE: {
        NodeType.SHAPE, NodeType.TEXT, NodeType.IMAGE,
        NodeType.CHART, NodeType.TABLE, NodeType.GROUP,
        NodeType.VIDEO, NodeType.DIAGRAM, NodeType.CODE,
    },
    NodeType.GROUP: {
        NodeType.SHAPE, NodeType.TEXT, NodeType.IMAGE,
        NodeType.CHART, NodeType.TABLE, NodeType.DIAGRAM,
    },
}

# 叶子节点：不可包含子节点
LEAF_NODES = {
    NodeType.TEXT, NodeType.IMAGE, NodeType.SHAPE,
    NodeType.TABLE, NodeType.CHART, NodeType.VIDEO,
    NodeType.AUDIO, NodeType.DIAGRAM, NodeType.CODE,
    NodeType.MODEL_3D, NodeType.MAP,
}

# 必需属性约束
REQUIRED_PROPS: dict[NodeType, list[str]] = {
    NodeType.TEXT: ["content"],
    NodeType.IMAGE: ["source"],
    NodeType.CHART: ["chart_type"],
    NodeType.TABLE: [],  # data_ref 或 inline data 均可
    NodeType.SLIDE: ["layout"],
}


class ValidationError(Exception):
    """IR 校验错误"""
    pass


def validate_containment(parent_type: NodeType, child_type: NodeType) -> bool:
    """校验父子节点的包含关系是否合法"""
    allowed = CONTAINMENT_RULES.get(parent_type)
    if allowed is None:
        return False  # 该节点类型不可包含任何子节点
    return child_type in allowed


def validate_node_type(node_type_str: str) -> NodeType:
    """将字符串转换为 NodeType，无效则抛出 ValidationError"""
    try:
        return NodeType(node_type_str)
    except ValueError:
        valid = [e.value for e in NodeType]
        raise ValidationError(
            f"未知节点类型 '{node_type_str}'，合法类型: {valid}"
        )


# ============================================================
# IR 节点数据结构
# ============================================================


@dataclass
class IRPosition:
    """IR 位置 — 绝对坐标（mm）"""
    x_mm: float = 0.0
    y_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0
    # 标记
    is_relative: bool = False  # 原始值是否为百分比
    is_center: bool = False
    is_auto: bool = False  # 尺寸自动计算


@dataclass
class IRStyle:
    """IR 样式 — 渲染器无关的样式描述

    所有字段默认 None 表示"未设置"，级联时只覆盖非 None 字段。
    最终渲染前需由渲染器或级联引擎填入实际值。
    """
    font_family: str | None = None
    font_size: int | None = None  # pt
    font_weight: int | None = None
    font_italic: bool | None = None
    font_color: str | None = None
    fill_color: str | None = None
    fill_gradient: dict[str, Any] | None = None
    fill_opacity: float | None = None
    shadow: dict[str, Any] | None = None
    border: dict[str, Any] | None = None
    text_effect: dict[str, Any] | None = None
    # 文本效果扩展
    text_outline: dict[str, Any] | None = None      # 描边 {color, width, dash}
    text_reflection: dict[str, Any] | None = None    # 倒影 {opacity, distance, blur, direction}
    text_bevel: dict[str, Any] | None = None         # 斜面浮雕 {type, width, height, material}
    letter_spacing: float | None = None              # 字距（pt）
    word_spacing: float | None = None                # 词距（pt）
    # 主题引用
    theme_ref: str | None = None


@dataclass
class IRPathText:
    """IR 路径文字 — 渲染器无关的路径文字描述

    路径文字将文本沿曲线排列。渲染器根据 path_type 选择实现方式：
      - arc / wave / circle 等预设：PPTX 用 presetTextWarp（单 shape）
      - custom（任意 SVG 路径）：PPTX 逐字符旋转文本框
      - HTML：原生 SVG <textPath>
      - PDF / DOCX：降级为水平文本

    路径类型：
      - arc: 弧线（需 radius, start_angle, end_angle）
      - wave: 波浪（需 amplitude, wavelength）
      - custom: 自定义 SVG 路径（需 custom_path）

    降级策略由 renderer/capability_map.py 中的 fallback_map 控制。
    """
    path_type: str = "arc"          # 预设或 custom
    radius: float = 100.0           # 弧线半径（mm）
    start_angle: float = 0.0        # 起始角度（度）
    end_angle: float = 180.0        # 结束角度（度）
    amplitude: float = 10.0         # 波浪振幅（mm）
    wavelength: float = 50.0        # 波长（mm）
    custom_path: str = ""           # SVG 路径数据（M x y C ...）
    char_spacing: float = 0.0       # 额外字符间距（mm）
    bend: float = 50.0              # 弯曲程度 0-100（presetTextWarp 用）


# 合法路径类型
VALID_PATH_TYPES = {
    "arc", "arch_up", "wave", "circle",
    "button", "chevron", "slant_up", "slant_down",
    "triangle", "inflate", "deflate", "custom",
}


@dataclass
class IRAnimation:
    """IR 动画 — 渲染器无关的动画描述

    PPTX 是唯一支持动画的格式，其他渲染器忽略或降级。

    动画类型：
      - entry: 入场动画（元素从无到有）
      - exit: 退出动画（元素从有到无）
      - emphasis: 强调动画（元素在原位变化）
      - motion_path: 路径动画（元素沿路径移动）

    缓动函数控制动画速度曲线：
      - linear: 匀速
      - ease_in: 加速
      - ease_out: 减速
      - ease_in_out: 先加速后减速
      - bounce: 弹跳
      - elastic: 弹性

    PPTX 映射约束：
      - 物理动画（弹簧/重力）预计算为关键帧
      - 并行动画最多 4 层
      - infinite → repeatUntilNextClick
    """
    anim_type: str = "entry"        # entry / exit / emphasis / motion_path
    effect: str = "fade"            # 动画效果名
    trigger: str = "on_click"       # on_click / with_previous / after_previous
    duration: float = 0.5           # 持续时间（秒）
    delay: float = 0.0              # 延迟时间（秒）
    easing: str = "ease_out"        # 缓动函数
    repeat: int = 0                 # 重复次数 (0=不重复, -1=无限)
    direction: str = ""             # 方向 (up/down/left/right)
    # 路径动画坐标点 (motion_path 用)
    path_points: list[tuple[float, float]] = field(default_factory=list)
    # 原始参数
    extra: dict[str, Any] = field(default_factory=dict)


# 入场动画预设（对应 EFFECT_MAP 中 transition="in" 的条目）
ENTRY_ANIMATIONS = {
    "fade", "fade_in",
    "wipe_up", "wipe_down", "wipe_left", "wipe_right",
    "slide_up", "slide_down", "slide_left", "slide_right",
    "fly_in", "zoom_in", "zoom_out_in",
    "blinds_h", "blinds_v",
    "checkerboard", "checkerboard_v",
    "box_in", "box_out",
    "diamond", "plus",
    "wheel", "wheel_1", "wheel_2", "wheel_3", "wheel_4", "wheel_8",
    "random_bars_h", "random_bars_v",
    "circle", "shape_diamond", "shape_plus",
    "cut_in", "faded_swivel",
    "strips_upleft", "strips_upright", "strips_downleft", "strips_downright",
}

# 退出动画预设（对应 EFFECT_MAP 中 transition="out" 的条目）
EXIT_ANIMATIONS = {
    "fade_out",
    "wipe_out_up", "wipe_out_down", "wipe_out_left", "wipe_out_right",
    "slide_out_up", "slide_out_down", "slide_out_left", "slide_out_right",
    "fly_out", "zoom_out", "zoom_out_exit",
    "blinds_out_h", "blinds_out_v",
    "checkerboard_out", "box_out_exit",
    "diamond_out", "circle_out",
    "random_bars_out_h", "random_bars_out_v",
    "strips_out_upleft", "strips_out_upright",
    "strips_out_downleft", "strips_out_downright",
}

# 强调动画预设（缩放 / 旋转 / 变色）
EMPHASIS_ANIMATIONS = {
    "pulse", "grow", "shrink", "grow_s", "shrink_s",
    "spin_cw", "spin_ccw", "spin_half_cw", "spin_half_ccw", "spin_emphasis",
    "color_pulse", "color_grow", "color_warn", "color_flash",
}

# 路径动画预设（直线 / 弧线 / 预设形状）
MOTION_PATH_PRESETS = {
    "path_right", "path_left", "path_up", "path_down",
    "path_up_right", "path_down_right", "path_up_left", "path_down_left",
    "path_arc_right", "path_arc_left", "path_loop",
    "path_diamond", "path_triangle", "path_hexagon", "path_figure_8",
}

# 缓动函数
EASING_FUNCTIONS = {
    "linear", "ease_in", "ease_out", "ease_in_out",
    "bounce", "elastic", "back",
}

# PPTX 动画降级映射
ANIMATION_FALLBACK = {
    "spring": "ease_out",
    "bounce": "ease_out",
    "orbit": "custom_path",
    "infinite": "repeat_until_next_click",
}


@dataclass
class IRNode:
    """IR 基础节点"""
    node_type: NodeType
    id: str = ""
    # 内容
    content: str | None = None
    content_format: str = "plain"  # plain | markdown | latex | rich
    source: str | dict | None = None
    # 布局
    position: IRPosition | None = None
    # 样式
    style: IRStyle | None = None
    style_ref: str | None = None  # 引用全局样式名
    # 子节点
    children: list["IRNode"] = field(default_factory=list)
    # 数据绑定
    data_ref: str | None = None
    chart_type: str | None = None
    # 动画列表
    animations: list["IRAnimation"] = field(default_factory=list)
    # 路径文字
    path_text: IRPathText | None = None
    # 额外属性
    extra: dict[str, Any] = field(default_factory=dict)
    # 原始 DSL 路径（调试用）
    source_path: str = ""


@dataclass
class IRDocument:
    """IR 文档根节点"""
    version: str = "4.0"
    doc_type: str = "presentation"
    theme: str = "default"
    title: str = ""
    style_preset: str = ""  # 设计令牌预设：corporate/editorial/creative/minimal/tech/elegant/flat/chinese/warm
    # 全局样式表
    styles: dict[str, IRStyle] = field(default_factory=dict)
    # 全局数据
    data: dict[str, Any] = field(default_factory=dict)
    # 子节点（slides / sections）
    children: list[IRNode] = field(default_factory=list)
    # 原始 DSL
    raw_dsl: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """序列化为可 JSON 编码的字典（含 raw_dsl 保留）"""
        return _ir_to_dict(self)


def _ir_to_dict(obj: Any) -> Any:
    """递归将 IR 树序列化为 dict，处理 Enum / dataclass / 嵌套"""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_ir_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _ir_to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for f in fields(obj):
            val = getattr(obj, f.name)
            result[f.name] = _ir_to_dict(val)
        return result
    return str(obj)


def dump_ir_json(doc: IRDocument, pretty: bool = True) -> str:
    """将 IRDocument 序列化为 JSON 字符串

    Args:
        doc: IR 文档
        pretty: 是否美化输出（缩进 2 格）

    Returns:
        JSON 字符串
    """
    data = doc.to_dict()
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def validate_ir(doc: IRDocument) -> list[str]:
    """校验 IR 文档，返回警告列表（空表示无问题）"""
    warnings = []

    def _validate_node(node: IRNode, parent_type: NodeType | None, path: str):
        # 校验包含约束
        if parent_type is not None:
            if not validate_containment(parent_type, node.node_type):
                warnings.append(
                    f"{path}: {parent_type.value} 不可包含 {node.node_type.value}"
                )
        # 校验必需属性
        required = REQUIRED_PROPS.get(node.node_type, [])
        for prop in required:
            if prop == "content" and not node.content:
                warnings.append(f"{path}: {node.node_type.value} 缺少必需属性 'content'")
            elif prop == "source" and not node.source:
                warnings.append(f"{path}: {node.node_type.value} 缺少必需属性 'source'")
            elif prop == "chart_type" and not node.chart_type:
                warnings.append(f"{path}: {node.node_type.value} 缺少必需属性 'chart_type'")
        # 递归子节点
        for i, child in enumerate(node.children):
            _validate_node(child, node.node_type, f"{path}/{child.node_type.value}[{i}]")

    for i, slide in enumerate(doc.children):
        _validate_node(slide, NodeType.DOCUMENT, f"slide[{i}]")

    return warnings
