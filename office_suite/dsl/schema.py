"""DSL Schema 定义 — 声明式文档描述语言的类型约束

设计方案第三章：声明式 YAML 定义文档，而非命令式代码。

数据类层次：
  Document (顶层)
    ├── data: dict[str, DataBinding]   — 数据源绑定
    ├── styles: dict[str, StyleSpec]   — 全局样式表
    └── slides: list[Slide]            — 幻灯片列表
         └── elements: list[Element]   — 元素列表
              ├── type: str            — text/image/shape/table/chart/group
              ├── position: PositionSpec — 位置（mm/%/center/auto）
              ├── style: str | StyleSpec — 样式引用或内联
              └── children: list[Element] — 子元素（GROUP 用）

特性分级（P0/P1/P2/P3）见 ElementPriority 枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DocType(Enum):
    """文档类型"""
    PRESENTATION = "presentation"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"


class ElementPriority(Enum):
    """DSL 特性分级"""
    P0 = "P0"  # MVP 必须
    P1 = "P1"  # 第二批
    P2 = "P2"  # 后期
    P3 = "P3"  # 远期


# P0 支持的元素类型
P0_ELEMENT_TYPES = {
    "text", "image", "shape", "table", "chart", "group", "semantic_icon", "component"
}

# P1 支持的元素类型
P1_ELEMENT_TYPES = {
    "video", "audio", "diagram", "code"
}

# P2/P3 支持的元素类型
P2_ELEMENT_TYPES = {"3d_model", "map"}


@dataclass(frozen=True)
class PositionSpec:
    """位置规格"""
    x: str | float | None = None  # "20mm" | "10%" | "center" | 数值
    y: str | float | None = None
    width: str | float | None = None  # "80mm" | "60%" | "auto"
    height: str | float | None = None
    bottom: str | float | None = None  # 从底部定位
    center: bool = False  # 水平居中


@dataclass(frozen=True)
class FontSpec:
    """字体规格"""
    family: str = "Microsoft YaHei UI"
    size: int = 18  # pt
    weight: int = 400  # 100-900
    italic: bool = False
    color: str = "#000000"


@dataclass(frozen=True)
class GradientStop:
    """渐变停止点"""
    color: str
    position: float = 0.0  # 0.0 - 1.0


@dataclass(frozen=True)
class GradientSpec:
    """渐变规格"""
    type: str = "linear"  # linear | radial
    angle: int = 0  # 度数，linear 专用
    stops: list[str] = field(default_factory=lambda: ["#000000", "#FFFFFF"])


@dataclass(frozen=True)
class ShadowSpec:
    """阴影规格"""
    blur: int = 0
    offset: list[int] = field(default_factory=lambda: [0, 0])
    color: str = "#00000040"


@dataclass(frozen=True)
class FillSpec:
    """填充规格"""
    color: str | None = None
    gradient: GradientSpec | None = None
    opacity: float = 1.0


@dataclass(frozen=True)
class StyleSpec:
    """样式规格"""
    font: FontSpec | None = None
    fill: FillSpec | None = None
    shadow: ShadowSpec | None = None
    border: dict[str, Any] | None = None
    text_effect: dict[str, Any] | None = None


@dataclass
class Element:
    """DSL 元素节点"""
    type: str
    content: str | None = None
    format: str = "plain"  # plain | markdown | latex | rich
    source: str | dict | None = None
    style: str | StyleSpec | None = None
    style_ref: str | None = None
    position: PositionSpec | None = None
    data_ref: str | None = None
    chart_type: str | None = None
    query: str | None = None
    prompt: str | None = None
    size: dict[str, Any] | None = None
    opacity: float = 1.0
    filter: str | None = None
    animation: dict[str, Any] | None = None
    children: list["Element"] = field(default_factory=list)
    # catalog 引用
    catalog_ref: str | None = None       # catalog 条目 ID
    catalog_params: dict[str, Any] | None = None  # 传给 catalog 的参数
    # 透传属性
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Slide:
    """幻灯片 / 节"""
    layout: str = "blank"
    layout_mode: str = ""            # 布局引擎模式：absolute / relative / grid / flex / constraint
    grid: dict[str, Any] | None = None      # 栅格配置：{ columns, gutter, row_height }
    flex: dict[str, Any] | None = None      # 弹性布局配置：{ direction, justify, align, gap, wrap }
    constraints: list[dict[str, Any]] | None = None  # 约束列表（constraint 模式）
    card_container: bool = False     # 子元素自动应用卡片样式（圆角 + 阴影 + 背景）
    background: dict[str, Any] | None = None
    background_board: dict[str, Any] | None = None
    layers: dict[str, list[Element]] = field(default_factory=dict)
    elements: list[Element] = field(default_factory=list)
    transition: dict[str, Any] | None = None


@dataclass
class DataBinding:
    """数据源绑定"""
    source: str | None = None
    columns: list[str] = field(default_factory=list)
    formula: str | None = None
    inline: Any = None  # 内联后备数据


@dataclass
class Document:
    """顶层文档 DSL"""
    version: str = "4.0"
    type: DocType = DocType.PRESENTATION
    theme: str = "default"
    title: str = ""
    style_preset: str = ""  # 设计令牌预设：corporate/editorial/creative/minimal/tech/elegant/flat/chinese/warm
    design_manifest: str = ""  # AI 自主设计宣言：描述本 deck 的视觉概念
    auto_enhance: bool = False  # 是否启用编译器自动增强（背景注入/装饰注入），默认关闭
    data: dict[str, DataBinding] = field(default_factory=dict)
    styles: dict[str, StyleSpec] = field(default_factory=dict)
    slides: list[Slide] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    # 原始 YAML 保留
    raw: dict[str, Any] = field(default_factory=dict)
