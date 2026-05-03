"""设计令牌 — Office Suite 自有的文档/PPT 设计系统

不引用 Material / Fluent / Ant Design 等 UI 设计语言。
只包含文档渲染真正需要的：配色、字体、间距、布局。

用法：
    from office_suite.design.tokens import PALETTE, TYPOGRAPHY, SPACING, GRID
    color = PALETTE["corporate"]["primary"]  # "#1E40AF"
"""

from dataclasses import dataclass, field


# ============================================================
# 配色方案
# ============================================================

PALETTE: dict[str, dict[str, str]] = {
    "corporate": {
        "primary": "#1E40AF",
        "secondary": "#3B82F6",
        "accent": "#60A5FA",
        "bg": "#FFFFFF",
        "bg_alt": "#F8FAFC",
        "text": "#0F172A",
        "text_secondary": "#64748B",
        "border": "#E2E8F0",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    "editorial": {
        "primary": "#0F172A",
        "secondary": "#1E293B",
        "accent": "#2563EB",
        "bg": "#FFFFFF",
        "bg_alt": "#F1F5F9",
        "text": "#0F172A",
        "text_secondary": "#94A3B8",
        "border": "#CBD5E1",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    "creative": {
        "primary": "#E11D48",
        "secondary": "#F43F5E",
        "accent": "#FB7185",
        "bg": "#18181B",
        "bg_alt": "#27272A",
        "text": "#FFFFFF",
        "text_secondary": "#A1A1AA",
        "border": "#3F3F46",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },
    "minimal": {
        "primary": "#2563EB",
        "secondary": "#3B82F6",
        "accent": "#60A5FA",
        "bg": "#FFFFFF",
        "bg_alt": "#F8FAFC",
        "text": "#0F172A",
        "text_secondary": "#64748B",
        "border": "#E2E8F0",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    "tech": {
        "primary": "#8B5CF6",
        "secondary": "#A78BFA",
        "accent": "#06B6D4",
        "bg": "#0B0F19",
        "bg_alt": "#111827",
        "text": "#FFFFFF",
        "text_secondary": "#94A3B8",
        "border": "#1E293B",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },
    "elegant": {
        "primary": "#064E3B",
        "secondary": "#065F46",
        "accent": "#D4AF37",
        "bg": "#FFFFFF",
        "bg_alt": "#F0FDF4",
        "text": "#064E3B",
        "text_secondary": "#6B7280",
        "border": "#D1FAE5",
        "success": "#059669",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    "flat": {
        "primary": "#0EA5E9",
        "secondary": "#38BDF8",
        "accent": "#7DD3FC",
        "bg": "#F0F9FF",
        "bg_alt": "#E0F2FE",
        "text": "#0C4A6E",
        "text_secondary": "#0369A1",
        "border": "#BAE6FD",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },
    "chinese": {
        "primary": "#DC2626",
        "secondary": "#EF4444",
        "accent": "#D4AF37",
        "bg": "#7F1D1D",
        "bg_alt": "#991B1B",
        "text": "#FEE2E2",
        "text_secondary": "#FCA5A5",
        "border": "#B91C1C",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#F87171",
    },
    "warm": {
        "primary": "#D97706",
        "secondary": "#F59E0B",
        "accent": "#FBBF24",
        "bg": "#FFFBEB",
        "bg_alt": "#FEF3C7",
        "text": "#1C1917",
        "text_secondary": "#78716C",
        "border": "#FDE68A",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
    },
    # 莫兰迪色系（低饱和度、高级感）
    "morandi": {
        "primary": "#8B7E74",
        "secondary": "#A69B8E",
        "accent": "#C4B5A6",
        "bg": "#F5F0EB",
        "bg_alt": "#EDE7E0",
        "text": "#4A4A4A",
        "text_secondary": "#8B8B8B",
        "border": "#D4CFC9",
        "success": "#7D8B6A",
        "warning": "#C4A35A",
        "danger": "#B85C5C",
    },
    # 极简黑白灰
    "minimal_bw": {
        "primary": "#000000",
        "secondary": "#333333",
        "accent": "#666666",
        "bg": "#FFFFFF",
        "bg_alt": "#F5F5F5",
        "text": "#000000",
        "text_secondary": "#666666",
        "border": "#E0E0E0",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "danger": "#F44336",
    },
    # 中国风（水墨山水）
    "chinese_ink": {
        "primary": "#2C3E50",
        "secondary": "#34495E",
        "accent": "#1ABC9C",
        "bg": "#F8F6F0",
        "bg_alt": "#EDE9E0",
        "text": "#2C3E50",
        "text_secondary": "#7F8C8D",
        "border": "#D5D0C8",
        "success": "#27AE60",
        "warning": "#E67E22",
        "danger": "#C0392B",
    },
    # 莫兰迪蓝
    "morandi_blue": {
        "primary": "#6B8FAD",
        "secondary": "#8BA8C4",
        "accent": "#A7C7E7",
        "bg": "#F0F4F8",
        "bg_alt": "#E3EAF0",
        "text": "#3D5A73",
        "text_secondary": "#7D9AB5",
        "border": "#C5D5E4",
        "success": "#7BAE7F",
        "warning": "#D4A574",
        "danger": "#C47C7C",
    },
    # 莫兰迪粉
    "morandi_pink": {
        "primary": "#C4A4A4",
        "secondary": "#D4B4B4",
        "accent": "#E8CCCC",
        "bg": "#FBF5F5",
        "bg_alt": "#F5EDED",
        "text": "#6B4F4F",
        "text_secondary": "#A08080",
        "border": "#E0D0D0",
        "success": "#8FAE8B",
        "warning": "#D4B896",
        "danger": "#C48B8B",
    },
    # 莫兰迪绿
    "morandi_green": {
        "primary": "#7D8B6A",
        "secondary": "#95A882",
        "accent": "#B8C9A3",
        "bg": "#F5F8F2",
        "bg_alt": "#EBF0E5",
        "text": "#4A5A3D",
        "text_secondary": "#7D8B6A",
        "border": "#C5D1B8",
        "success": "#7D8B6A",
        "warning": "#C4B07A",
        "danger": "#B87A7A",
    },
}


# ============================================================
# 字体规范
# ============================================================

@dataclass(frozen=True)
class FontSpec:
    """字体规格"""
    family: str = "Microsoft YaHei UI"
    size: int = 18
    weight: int = 400
    line_height: float = 1.4


# Major Second 模块化音阶 (ratio=1.25)，body 12pt 为基准
# 7 → 9 → 12 → 15 → 19 → 24 → 31 → 39
# 大字号用 tighter leading，小字号用 looser leading
TYPOGRAPHY: dict[str, FontSpec] = {
    "cover_title": FontSpec(size=35, weight=700, line_height=1.15),
    "cover_subtitle": FontSpec(size=15, weight=400, line_height=1.4),
    "section_title": FontSpec(size=27, weight=700, line_height=1.2),
    "heading": FontSpec(size=19, weight=700, line_height=1.25),
    "subheading": FontSpec(size=15, weight=600, line_height=1.3),
    "body": FontSpec(size=12, weight=400, line_height=1.5),
    "body_small": FontSpec(size=10, weight=400, line_height=1.55),
    "caption": FontSpec(size=9, weight=400, line_height=1.6),
    "annotation": FontSpec(size=7, weight=400, line_height=1.6),
    "data_large": FontSpec(size=35, weight=700, line_height=1.1),
    "data_value": FontSpec(size=24, weight=700, line_height=1.2),
    "data_label": FontSpec(size=10, weight=400, line_height=1.4),
    "table_header": FontSpec(size=9, weight=600, line_height=1.4),
    "table_body": FontSpec(size=8, weight=400, line_height=1.5),
    "chart_title": FontSpec(size=10, weight=600, line_height=1.4),
    "chart_label": FontSpec(size=7, weight=400, line_height=1.5),
}


# ============================================================
# 间距规范 (mm)
# ============================================================

@dataclass(frozen=True)
class SpacingSpec:
    """间距规格"""
    unit: float = 4.0
    page_margin_x: float = 25.0
    page_margin_y: float = 20.0
    element_gap: float = 8.0
    section_gap: float = 12.0
    paragraph_gap: float = 6.0
    inline_gap: float = 2.0
    container_padding: float = 4.0


SPACING = SpacingSpec()


# ============================================================
# 布局网格 (mm)
# ============================================================

from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM


@dataclass(frozen=True)
class SlideGrid:
    """幻灯片网格"""
    width: float = SLIDE_WIDTH_MM
    height: float = SLIDE_HEIGHT_MM
    columns: int = 12
    gutter: float = 2.0


GRID = SlideGrid()


@dataclass(frozen=True)
class LayoutZone:
    """布局区域"""
    x: float
    y: float
    width: float
    height: float


# 预定义布局区域
LAYOUTS: dict[str, dict[str, LayoutZone]] = {
    "full": {
        "content": LayoutZone(25, 20, 204, 102.875),
    },
    "title_content": {
        "title": LayoutZone(25, 15, 204, 15),
        "content": LayoutZone(25, 38, 204, 84.875),
    },
    "two_column": {
        "title": LayoutZone(25, 15, 204, 12),
        "left": LayoutZone(25, 35, 98, 87.875),
        "right": LayoutZone(131, 35, 98, 87.875),
    },
    "three_column": {
        "title": LayoutZone(25, 15, 204, 12),
        "left": LayoutZone(25, 35, 62, 87.875),
        "center": LayoutZone(93, 35, 62, 87.875),
        "right": LayoutZone(161, 35, 62, 87.875),
    },
    "image_text": {
        "image": LayoutZone(25, 20, 105, 102.875),
        "text": LayoutZone(140, 20, 89, 102.875),
    },
    "text_image": {
        "text": LayoutZone(25, 20, 105, 102.875),
        "image": LayoutZone(140, 20, 89, 102.875),
    },
    "hero": {
        "title": LayoutZone(30, 40, 194, 28),
        "subtitle": LayoutZone(30, 72, 194, 10),
        "footer": LayoutZone(30, 120, 194, 10),
    },
    "stats_row": {
        "title": LayoutZone(20, 10, 214, 12),
        "stat_1": LayoutZone(20, 30, 68, 50),
        "stat_2": LayoutZone(93, 30, 68, 50),
        "stat_3": LayoutZone(166, 30, 68, 50),
    },
    "quote": {
        "quote": LayoutZone(40, 35, 174, 50),
        "attribution": LayoutZone(40, 90, 174, 10),
    },
}


# ============================================================
# 阴影预设
# ============================================================

SHADOWS: dict[str, dict] = {
    "none": {},
    "sm": {"color": "#000000", "opacity": 0.05, "blur": 2, "offset": [0, 1]},
    "md": {"color": "#000000", "opacity": 0.08, "blur": 4, "offset": [0, 2]},
    "lg": {"color": "#000000", "opacity": 0.1, "blur": 8, "offset": [0, 4]},
    "xl": {"color": "#000000", "opacity": 0.12, "blur": 16, "offset": [0, 8]},
    "card": {"color": "#000000", "opacity": 0.06, "blur": 6, "offset": [0, 2]},
    "elevated": {"color": "#000000", "opacity": 0.1, "blur": 12, "offset": [0, 6]},
    # 现代风格阴影 — 更大扩散、更柔和
    "soft": {"color": "#000000", "opacity": 0.04, "blur": 24, "offset": [0, 8]},
    "glow": {"color": "#000000", "opacity": 0.06, "blur": 32, "offset": [0, 12]},
}


# ============================================================
# 圆角预设 (mm)
# ============================================================

RADII: dict[str, float] = {
    "none": 0,
    "sm": 1,
    "md": 2,
    "lg": 4,
    "xl": 8,
    "2xl": 12,
    "3xl": 16,
    "pill": 999,
    "full": 999,
}


# ============================================================
# 渐变预设
# ============================================================

GRADIENTS: dict[str, dict] = {
    "corporate": {"type": "linear", "angle": 135, "stops": ["#1E40AF", "#3B82F6"]},
    "editorial": {"type": "linear", "angle": 180, "stops": ["#0F172A", "#1E293B"]},
    "creative": {"type": "linear", "angle": 135, "stops": ["#E11D48", "#F43F5E"]},
    "tech": {"type": "linear", "angle": 135, "stops": ["#8B5CF6", "#06B6D4"]},
    "elegant": {"type": "linear", "angle": 180, "stops": ["#064E3B", "#065F46"]},
    "sunset": {"type": "linear", "angle": 135, "stops": ["#F97316", "#EC4899"]},
    "ocean": {"type": "linear", "angle": 135, "stops": ["#0EA5E9", "#8B5CF6"]},
    "forest": {"type": "linear", "angle": 135, "stops": ["#059669", "#0D9488"]},
}


# ============================================================
# 透明度阶梯 — 标准化半透明效果
# ============================================================

OPACITY: dict[str, float] = {
    "transparent": 0.0,
    "subtle": 0.05,
    "faint": 0.10,
    "medium": 0.20,
    "strong": 0.40,
    "intense": 0.60,
    "opaque": 1.0,
}


# ============================================================
# 主题字体映射 — 每种风格配匹配气质的字体
# ============================================================

FONT_MAP: dict[str, dict[str, str]] = {
    # body: 正文/通用字体  display: 标题/强调字体
    "corporate":      {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "editorial":      {"body": "DengXian",           "display": "DengXian"},
    "creative":       {"body": "Microsoft YaHei",    "display": "Microsoft YaHei"},
    "minimal":        {"body": "DengXian",           "display": "DengXian"},
    "tech":           {"body": "Cascadia Code",      "display": "Cascadia Code"},
    "elegant":        {"body": "DengXian",           "display": "DengXian"},
    "flat":           {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "chinese":        {"body": "SimSun",             "display": "KaiTi"},
    "warm":           {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "morandi":        {"body": "DengXian",           "display": "DengXian"},
    "minimal_bw":     {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "chinese_ink":    {"body": "FangSong",           "display": "SimSun"},
    "morandi_blue":   {"body": "DengXian",           "display": "DengXian"},
    "morandi_pink":   {"body": "DengXian",           "display": "DengXian"},
    "morandi_green":  {"body": "DengXian",           "display": "DengXian"},
}

# 哪些角色使用 display 字体（大号标题类）
_DISPLAY_ROLES: frozenset[str] = frozenset({
    "cover_title",
    "section_title",
    "data_large",
    "chapter_num",
    "chapter_title",
})


# ============================================================
# 工具函数
# ============================================================

def get_palette(name: str) -> dict[str, str]:
    """获取配色方案，不存在时回退到 corporate"""
    return PALETTE.get(name, PALETTE["corporate"])


def get_font(role: str) -> FontSpec:
    """获取字体规格，不存在时回退到 body"""
    return TYPOGRAPHY.get(role, TYPOGRAPHY["body"])


def get_font_family(palette: str, role: str) -> str:
    """根据主题和角色获取字体家族名

    display 类角色（cover_title, section_title, data_large 等）使用 display 字体，
    其余角色使用 body 字体。palette 不存在时回退到 Microsoft YaHei UI。

    Args:
        palette: 配色方案名
        role: 字体角色
    Returns:
        字体家族名
    """
    theme = FONT_MAP.get(palette, FONT_MAP.get("corporate", {}))
    if role in _DISPLAY_ROLES:
        return theme.get("display", "Microsoft YaHei UI")
    return theme.get("body", "Microsoft YaHei UI")


def get_font_for_palette(palette: str, role: str) -> FontSpec:
    """获取带主题字体的 FontSpec — 尺寸来自 TYPOGRAPHY，字体来自 FONT_MAP

    Args:
        palette: 配色方案名
        role: 字体角色
    Returns:
        FontSpec，family 已替换为该主题对应的字体
    """
    base = get_font(role)
    family = get_font_family(palette, role)
    return FontSpec(
        family=family,
        size=base.size,
        weight=base.weight,
        line_height=base.line_height,
    )


def get_layout(name: str) -> dict[str, LayoutZone]:
    """获取布局区域，不存在时回退到 full"""
    return LAYOUTS.get(name, LAYOUTS["full"])


def get_shadow(name: str) -> dict:
    """获取阴影预设"""
    return SHADOWS.get(name, SHADOWS["none"])


def get_gradient(name: str) -> dict:
    """获取渐变预设"""
    return GRADIENTS.get(name, GRADIENTS["corporate"])


def colored_shadow(palette: str, level: str = "md") -> dict:
    """生成彩色阴影 — 使用主题 primary 色而非纯黑

    Args:
        palette: 配色方案名
        level: 阴影级别 (sm/md/lg/soft/glow)
    Returns:
        阴影字典 {"color": hex, "opacity": float, "blur": int, "offset": [x,y]}
    """
    base = SHADOWS.get(level, SHADOWS["md"])
    pal = get_palette(palette)
    return {
        "color": pal.get("primary", "#000000"),
        "opacity": base["opacity"],
        "blur": base["blur"],
        "offset": base["offset"],
    }


def palette_to_style(palette_name: str, role: str = "body") -> dict:
    """将配色方案转为 IRStyle 可用的样式 dict

    Args:
        palette_name: 配色方案名 (corporate/editorial/...)
        role: 字体角色 (heading/body/caption/...)

    Returns:
        包含 font 和 fill 的样式 dict
    """
    pal = get_palette(palette_name)
    font_spec = get_font_for_palette(palette_name, role)
    return {
        "font": {
            "family": font_spec.family,
            "size": font_spec.size,
            "weight": font_spec.weight,
            "color": pal["text"],
        },
        "fill": {"color": pal["bg"]},
    }


# ============================================================
# 导出
# ============================================================

__all__ = [
    "PALETTE",
    "TYPOGRAPHY",
    "FONT_MAP",
    "OPACITY",
    "SPACING",
    "GRID",
    "LAYOUTS",
    "SHADOWS",
    "RADII",
    "GRADIENTS",
    "get_palette",
    "get_font",
    "get_font_family",
    "get_font_for_palette",
    "get_layout",
    "get_shadow",
    "get_gradient",
    "colored_shadow",
    "palette_to_style",
]
