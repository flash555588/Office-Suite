"""智能配色适配 — 装饰元素自动跟随 palette 调整颜色

提供统一的配色查询接口，让背景预设、装饰工具、纹理生成器
都能自动跟随用户选择的 palette 调整颜色，避免手动传入颜色值。

用法：
    from office_suite.design.auto_style import get_accent, get_subtle, get_decor
    accent = get_accent("corporate")  # → "#3B82F6"
    subtle = get_subtle("corporate")  # → "#E2E8F0"
    decor = get_decor("corporate")    # → {"accent": "#3B82F6", "subtle": "#E2E8F0", ...}
"""

from __future__ import annotations

from typing import Any

from .tokens import get_palette, get_color_zones, get_chart_palette


def get_accent(palette: str) -> str:
    """获取强调色（primary 或 accent，取更鲜艳的）

    Args:
        palette: 配色方案名
    Returns:
        强调色 HEX 值
    """
    pal = get_palette(palette)
    return pal.get("accent", pal.get("primary", "#2563EB"))


def get_subtle(palette: str) -> str:
    """获取微妙色（用于低可见度装饰：边框、纹理、点阵）

    Args:
        palette: 配色方案名
    Returns:
        微妙色 HEX 值
    """
    pal = get_palette(palette)
    return pal.get("border", pal.get("bg_alt", "#E2E8F0"))


def get_decor(palette: str) -> dict[str, str]:
    """获取完整的装饰配色方案

    Args:
        palette: 配色方案名
    Returns:
        包含多种装饰用途的配色字典
    """
    pal = get_palette(palette)
    return {
        "accent": pal.get("accent", pal.get("primary", "#2563EB")),
        "primary": pal.get("primary", "#1E40AF"),
        "secondary": pal.get("secondary", "#3B82F6"),
        "subtle": pal.get("border", "#E2E8F0"),
        "bg_alt": pal.get("bg_alt", "#F8FAFC"),
        "text": pal.get("text", "#0F172A"),
        "text_secondary": pal.get("text_secondary", "#64748B"),
    }


def resolve_color(
    palette: str,
    role: str = "accent",
    opacity: float = 1.0,
) -> str:
    """根据角色解析颜色，支持透明度后缀

    Args:
        palette: 配色方案名
        role: 颜色角色 (accent, primary, secondary, subtle, bg_alt, text, text_secondary)
        opacity: 透明度 (0.0-1.0)，低于 1.0 时追加 HEX alpha 通道
    Returns:
        HEX 颜色值（可能带 alpha 通道）
    """
    pal = get_palette(palette)
    color = pal.get(role, pal.get("accent", "#2563EB"))

    if opacity < 1.0:
        alpha = int(max(0.0, min(1.0, opacity)) * 255)
        return f"{color}{alpha:02X}"
    return color


def auto_border(palette: str, width: float = 0.5) -> dict[str, Any]:
    """自动生成边框样式

    Args:
        palette: 配色方案名
        width: 边框宽度
    Returns:
        边框样式字典
    """
    return {
        "border": {
            "color": get_subtle(palette),
            "width": width,
        },
    }


def auto_shadow(palette: str, level: str = "md") -> dict[str, Any]:
    """自动生成阴影样式

    Args:
        palette: 配色方案名
        level: 阴影级别 (sm, md, lg, xl)
    Returns:
        阴影样式字典
    """
    from .tokens import get_shadow
    return get_shadow(level)


def auto_fill(palette: str, role: str = "bg") -> dict[str, Any]:
    """自动生成填充样式

    Args:
        palette: 配色方案名
        role: 填充角色 (bg, bg_alt, primary, accent)
    Returns:
        填充样式字典
    """
    pal = get_palette(palette)
    return {"fill": {"color": pal.get(role, pal.get("bg", "#FFFFFF"))}}


def get_gradient_pair(palette: str) -> tuple[str, str]:
    """获取配色方案的渐变色对（用于渐变装饰）

    Args:
        palette: 配色方案名
    Returns:
        (起始色, 结束色) 元组
    """
    from .tokens import get_gradient
    grad = get_gradient(palette)
    stops = grad.get("stops", ["#000000", "#FFFFFF"])
    return (stops[0], stops[-1]) if len(stops) >= 2 else (stops[0], stops[0])


def get_text_style(palette: str, role: str = "heading") -> dict[str, Any]:
    """获取文本样式（自动从 palette 和 typography 组合）

    Args:
        palette: 配色方案名
        role: 文本角色 (title, heading, body, caption)
    Returns:
        文本样式字典
    """
    pal = get_palette(palette)
    from .tokens import get_font_for_palette
    font = get_font_for_palette(palette, role)

    return {
        "font": {
            "family": font.family,
            "size": font.size,
            "weight": font.weight,
            "color": pal.get("text", "#0F172A"),
        },
    }


def get_card_style(palette: str, elevated: bool = False) -> dict[str, Any]:
    """获取卡片样式（自动从 palette 组合背景、边框、阴影）

    Args:
        palette: 配色方案名
        elevated: 是否抬高（增加阴影）
    Returns:
        卡片样式字典
    """
    pal = get_palette(palette)
    from .tokens import get_shadow
    shadow = get_shadow("lg" if elevated else "card")

    return {
        "fill": {"color": pal.get("bg", "#FFFFFF")},
        "border": {"color": pal.get("border", "#E2E8F0"), "width": 0.5},
        "shadow": shadow,
    }


def get_glass_card_style(
    palette: str,
    tint: float = 0.85,
    border_width: float = 0.8,
) -> dict[str, Any]:
    """玻璃卡片样式 — 现代毛玻璃效果

    半透明白色/深色背景 + 微妙高光边框 + 柔和阴影，
    模拟 glass-morphism 效果。

    Args:
        palette: 配色方案名
        tint: 背景不透明度 (0.7-0.95)，越低越透明
        border_width: 边框宽度
    Returns:
        卡片样式字典
    """
    pal = get_palette(palette)
    from .tokens import get_shadow, OPACITY

    bg_hex = pal.get("bg", "#FFFFFF")
    # 背景色 + 透明度后缀
    alpha = int(max(0.0, min(1.0, tint)) * 255)
    glass_bg = f"{bg_hex}{alpha:02X}"

    # 边框使用略亮的白色（亮色主题）或略亮的边框色（暗色主题）
    is_dark = _is_dark_palette(pal)
    border_color = "#FFFFFF" if is_dark else pal.get("border", "#E2E8F0")

    return {
        "fill": {"color": glass_bg},
        "border": {"color": border_color, "width": border_width},
        "shadow": get_shadow("soft"),
    }


def _is_dark_palette(pal: dict[str, str]) -> bool:
    """判断配色方案是否为暗色主题"""
    bg = pal.get("bg", "#FFFFFF").lstrip("#")
    if len(bg) >= 6:
        r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
        return (r * 0.299 + g * 0.587 + b * 0.114) < 128
    return False


def get_gradient_accent(palette: str, angle: int = 0) -> dict[str, Any]:
    """获取渐变强调线样式 — 从 primary 渐变到 accent

    Args:
        palette: 配色方案名
        angle: 渐变角度 (0=从左到右)
    Returns:
        渐变 fill_gradient 字典
    """
    pal = get_palette(palette)
    return {
        "fill_gradient": {
            "type": "linear",
            "angle": angle,
            "stops": [
                pal.get("primary", "#1E40AF"),
                pal.get("accent", "#60A5FA"),
            ],
        },
    }


# ============================================================
# 3 区色彩模型查询 (Color Zone Queries)
# ============================================================

def get_zone_semantic(palette: str) -> dict[str, str]:
    """获取 Zone 1 语义色（primary/accent/highlight）

    语义色固定不可变，用于标题、关键数据、CTA 按钮。

    Args:
        palette: 配色方案名
    Returns:
        {"primary": hex, "accent": hex, "highlight": hex}
    """
    zones = get_color_zones(palette)
    return zones["semantic"]


def get_zone_chart(palette: str, index: int = 0) -> str:
    """获取 Zone 2 图表色板中的第 N 个颜色

    图表色板固定不可变，确保数据可视化的一致性和对比度。

    Args:
        palette: 配色方案名
        index: 色板索引（自动取模，支持超出范围）
    Returns:
        HEX 颜色值
    """
    chart = get_chart_palette(palette)
    return chart[index % len(chart)]


def get_zone_decorative(palette: str) -> tuple[str, str]:
    """获取 Zone 3 装饰色允许范围（lightest, darkest）

    装饰色用于背景渐变、纹理、装饰元素。
    LLM 在 [lightest, darkest] 范围内自由发挥。

    Args:
        palette: 配色方案名
    Returns:
        (lightest_hex, darkest_hex) 元组
    """
    zones = get_color_zones(palette)
    r = zones["decorative_range"]
    return (r[0], r[1])
