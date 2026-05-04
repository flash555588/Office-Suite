"""设计令牌 — Office Suite 自有的文档/PPT 设计系统

不引用 Material / Fluent / Ant Design 等 UI 设计语言。
只包含文档渲染真正需要的：配色、字体、间距、布局。

用法：
    from office_suite.design.tokens import PALETTE, TYPOGRAPHY, SPACING, GRID
    color = PALETTE["corporate"]["primary"]  # "#1E40AF"
"""

from dataclasses import dataclass, field
from typing import Any


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
    # ── ppt-agent 扩展风格 ──────────────────────────────────────
    # 工程蓝图风（深蓝底白线）
    "blueprint": {
        "primary": "#1E3A8A",
        "secondary": "#3B82F6",
        "accent": "#38BDF8",
        "bg": "#0C1D3A",
        "bg_alt": "#0F2647",
        "text": "#E0F2FE",
        "text_secondary": "#7DD3FC",
        "border": "#1E40AF",
        "success": "#22D3EE",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },
    # 大胆社论风（黑白撞色 + 鲜红点缀）
    "bold_editorial": {
        "primary": "#111111",
        "secondary": "#333333",
        "accent": "#E63946",
        "bg": "#FAFAFA",
        "bg_alt": "#F0F0F0",
        "text": "#111111",
        "text_secondary": "#555555",
        "border": "#DDDDDD",
        "success": "#2D6A4F",
        "warning": "#E9C46A",
        "danger": "#E63946",
    },
    # 黑板粉笔风
    "chalkboard": {
        "primary": "#F5F5DC",
        "secondary": "#FFFFCC",
        "accent": "#FFD700",
        "bg": "#2E4033",
        "bg_alt": "#3A5141",
        "text": "#F5F5DC",
        "text_secondary": "#C8D8C0",
        "border": "#4A6B52",
        "success": "#90EE90",
        "warning": "#FFD700",
        "danger": "#FF6B6B",
    },
    # 社论信息图风（数据驱动、强层次）
    "editorial_infographic": {
        "primary": "#1B2838",
        "secondary": "#2A4060",
        "accent": "#FF6B35",
        "bg": "#FFFFFF",
        "bg_alt": "#F5F7FA",
        "text": "#1B2838",
        "text_secondary": "#5A6E82",
        "border": "#D0D8E0",
        "success": "#2ECC71",
        "warning": "#F1C40F",
        "danger": "#E74C3C",
    },
    # 奇幻动画风（高饱和暖色渐变）
    "fantasy_animation": {
        "primary": "#7C3AED",
        "secondary": "#A855F7",
        "accent": "#F97316",
        "bg": "#1A0533",
        "bg_alt": "#2D1654",
        "text": "#FAF5FF",
        "text_secondary": "#C4B5FD",
        "border": "#6D28D9",
        "success": "#22C55E",
        "warning": "#FBBF24",
        "danger": "#EF4444",
    },
    # 直觉机器风（温暖创意、复古未来感）
    "intuition_machine": {
        "primary": "#B45309",
        "secondary": "#D97706",
        "accent": "#FB923C",
        "bg": "#FFFBEB",
        "bg_alt": "#FEF3C7",
        "text": "#292524",
        "text_secondary": "#78716C",
        "border": "#FDE68A",
        "success": "#15803D",
        "warning": "#D97706",
        "danger": "#B91C1C",
    },
    # Notion 极简风（干净留白、低对比）
    "notion": {
        "primary": "#37352F",
        "secondary": "#555555",
        "accent": "#2EAADC",
        "bg": "#FFFFFF",
        "bg_alt": "#F7F6F3",
        "text": "#37352F",
        "text_secondary": "#9B9A97",
        "border": "#E8E7E4",
        "success": "#0F7B6C",
        "warning": "#DFAB01",
        "danger": "#EB5757",
    },
    # 像素艺术风（复古电子游戏配色）
    "pixel_art": {
        "primary": "#2D6A4F",
        "secondary": "#40916C",
        "accent": "#F72585",
        "bg": "#1A1A2E",
        "bg_alt": "#232344",
        "text": "#E0E0E0",
        "text_secondary": "#A0A0B0",
        "border": "#3A3A5C",
        "success": "#52B788",
        "warning": "#FCA311",
        "danger": "#F72585",
    },
    # 速写笔记风（手绘涂鸦感）
    "sketch_notes": {
        "primary": "#3D3D3D",
        "secondary": "#5C5C5C",
        "accent": "#FF6F61",
        "bg": "#FFF8F0",
        "bg_alt": "#FFF0E0",
        "text": "#3D3D3D",
        "text_secondary": "#888888",
        "border": "#D4C8BC",
        "success": "#66CDAA",
        "warning": "#FFB347",
        "danger": "#FF6F61",
    },
    # 矢量插画风（干净几何、高饱和色块）
    "vector_illustration": {
        "primary": "#1D3557",
        "secondary": "#457B9D",
        "accent": "#E63946",
        "bg": "#F1FAEE",
        "bg_alt": "#E8F4E0",
        "text": "#1D3557",
        "text_secondary": "#6B8BA4",
        "border": "#A8DADC",
        "success": "#2A9D8F",
        "warning": "#E9C46A",
        "danger": "#E63946",
    },
    # 复古风（怀旧色调、复古海报感）
    "vintage": {
        "primary": "#6B3A2A",
        "secondary": "#8B5E3C",
        "accent": "#C4864C",
        "bg": "#FDF6EC",
        "bg_alt": "#F5EAD8",
        "text": "#3E2723",
        "text_secondary": "#8D6E63",
        "border": "#D7C4A5",
        "success": "#7D8B6A",
        "warning": "#C4864C",
        "danger": "#A0522D",
    },
    # 水彩风（柔和渐变、低饱和梦幻色调）
    "watercolor": {
        "primary": "#5B8BA0",
        "secondary": "#8BB8CC",
        "accent": "#E8A0BF",
        "bg": "#FAF5F0",
        "bg_alt": "#F0EBE5",
        "text": "#3A4A5A",
        "text_secondary": "#7A8A9A",
        "border": "#D0D8DD",
        "success": "#8FC1A9",
        "warning": "#E8C170",
        "danger": "#D4817A",
    },
}


# ============================================================
# 3 区色彩模型 (Color Zone Model)
# ============================================================
#
# Zone 1 — 语义色 (Semantic): 标题、关键数据、CTA
#   固定来自主题 primary/accent，LLM 不可修改。
#
# Zone 2 — 图表色板 (Chart): 数据可视化 8-12 色序列
#   固定来自主题，确保无障碍对比度。
#
# Zone 3 — 装饰色 (Decorative): 背景渐变、装饰元素、纹理
#   只约束范围（明度/饱和度边界），LLM 在范围内自由发挥。
#   range 字段: [lightest, darkest] 界定允许的明度区间。

from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM  # noqa: E402

COLOR_ZONES: dict[str, dict[str, Any]] = {
    "corporate": {
        "semantic": {"primary": "#1E40AF", "accent": "#60A5FA", "highlight": "#F59E0B"},
        "chart": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899",
                   "#06B6D4", "#84CC16", "#F97316", "#6366F1"],
        "decorative_range": ["#DBEAFE", "#1E3A5F"],
    },
    "editorial": {
        "semantic": {"primary": "#0F172A", "accent": "#2563EB", "highlight": "#D97706"},
        "chart": ["#2563EB", "#10B981", "#D97706", "#DC2626", "#7C3AED", "#DB2777",
                   "#0891B2", "#65A30D", "#EA580C", "#4F46E5"],
        "decorative_range": ["#F1F5F9", "#1E293B"],
    },
    "creative": {
        "semantic": {"primary": "#E11D48", "accent": "#FB7185", "highlight": "#FBBF24"},
        "chart": ["#F43F5E", "#8B5CF6", "#06B6D4", "#F59E0B", "#10B981", "#EC4899",
                   "#6366F1", "#14B8A6", "#F97316", "#A855F7"],
        "decorative_range": ["#3F3F46", "#18181B"],
    },
    "minimal": {
        "semantic": {"primary": "#2563EB", "accent": "#60A5FA", "highlight": "#F59E0B"},
        "chart": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899",
                   "#06B6D4", "#84CC16", "#F97316", "#6366F1"],
        "decorative_range": ["#DBEAFE", "#1E3A5F"],
    },
    "tech": {
        "semantic": {"primary": "#8B5CF6", "accent": "#06B6D4", "highlight": "#22D3EE"},
        "chart": ["#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#EC4899",
                   "#6366F1", "#14B8A6", "#F97316", "#A855F7"],
        "decorative_range": ["#1E293B", "#0B0F19"],
    },
    "elegant": {
        "semantic": {"primary": "#064E3B", "accent": "#D4AF37", "highlight": "#059669"},
        "chart": ["#059669", "#D4AF37", "#064E3B", "#B45309", "#92400E", "#065F46",
                   "#9A3412", "#047857", "#78350F", "#10B981"],
        "decorative_range": ["#F0FDF4", "#022C22"],
    },
    "flat": {
        "semantic": {"primary": "#0EA5E9", "accent": "#7DD3FC", "highlight": "#F59E0B"},
        "chart": ["#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899",
                   "#14B8A6", "#84CC16", "#F97316", "#6366F1"],
        "decorative_range": ["#E0F2FE", "#0C4A6E"],
    },
    "chinese": {
        "semantic": {"primary": "#DC2626", "accent": "#D4AF37", "highlight": "#FBBF24"},
        "chart": ["#DC2626", "#D4AF37", "#B91C1C", "#F59E0B", "#991B1B", "#FBBF24",
                   "#7F1D1D", "#D97706", "#EF4444", "#B45309"],
        "decorative_range": ["#991B1B", "#7F1D1D"],
    },
    "warm": {
        "semantic": {"primary": "#D97706", "accent": "#FBBF24", "highlight": "#FBBF24"},
        "chart": ["#D97706", "#10B981", "#DC2626", "#8B5CF6", "#06B6D4", "#EC4899",
                   "#F97316", "#84CC16", "#6366F1", "#14B8A6"],
        "decorative_range": ["#FEF3C7", "#78350F"],
    },
    "morandi": {
        "semantic": {"primary": "#8B7E74", "accent": "#C4B5A6", "highlight": "#A69B8E"},
        "chart": ["#8B7E74", "#A69B8E", "#C4B5A6", "#7D8B6A", "#B85C5C", "#6B8FAD",
                   "#C4A35A", "#9B7E6B", "#8FAE8B", "#A08080"],
        "decorative_range": ["#EDE7E0", "#4A4A4A"],
    },
    "minimal_bw": {
        "semantic": {"primary": "#000000", "accent": "#666666", "highlight": "#999999"},
        "chart": ["#000000", "#333333", "#666666", "#999999", "#444444", "#777777",
                   "#222223", "#555556", "#888888", "#AAAAAA"],
        "decorative_range": ["#F5F5F5", "#333333"],
    },
    "chinese_ink": {
        "semantic": {"primary": "#2C3E50", "accent": "#1ABC9C", "highlight": "#E74C3C"},
        "chart": ["#2C3E50", "#1ABC9C", "#E74C3C", "#3498DB", "#9B59B6", "#F39C12",
                   "#16A085", "#D35400", "#2980B9", "#8E44AD"],
        "decorative_range": ["#EDE9E0", "#2C3E50"],
    },
    "morandi_blue": {
        "semantic": {"primary": "#6B8FAD", "accent": "#A7C7E7", "highlight": "#8BA8C4"},
        "chart": ["#6B8FAD", "#8BA8C4", "#A7C7E7", "#7BAE7F", "#D4A574", "#C47C7C",
                   "#8FAABD", "#9FC5D8", "#B5D1E0", "#7D9AB5"],
        "decorative_range": ["#E3EAF0", "#3D5A73"],
    },
    "morandi_pink": {
        "semantic": {"primary": "#C4A4A4", "accent": "#E8CCCC", "highlight": "#D4B4B4"},
        "chart": ["#C4A4A4", "#D4B4B4", "#E8CCCC", "#8FAE8B", "#D4B896", "#A08080",
                   "#B59090", "#C9B0B0", "#DDC8C8", "#9B7E7E"],
        "decorative_range": ["#F5EDED", "#6B4F4F"],
    },
    "morandi_green": {
        "semantic": {"primary": "#7D8B6A", "accent": "#B8C9A3", "highlight": "#95A882"},
        "chart": ["#7D8B6A", "#95A882", "#B8C9A3", "#C4B07A", "#B87A7A", "#6B8FAD",
                   "#8FAE8B", "#A0A88B", "#C5D1B8", "#5A6A4D"],
        "decorative_range": ["#EBF0E5", "#4A5A3D"],
    },
    # ── ppt-agent 扩展风格 COLOR_ZONES ─────────────────────────
    "blueprint": {
        "semantic": {"primary": "#1E3A8A", "accent": "#38BDF8", "highlight": "#22D3EE"},
        "chart": ["#3B82F6", "#38BDF8", "#22D3EE", "#F59E0B", "#22C55E", "#EF4444",
                   "#A78BFA", "#F472B6", "#10B981", "#6366F1"],
        "decorative_range": ["#1E3A5F", "#0C1D3A"],
    },
    "bold_editorial": {
        "semantic": {"primary": "#111111", "accent": "#E63946", "highlight": "#E9C46A"},
        "chart": ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261", "#264653",
                   "#6D6875", "#B5838D", "#FFB4A2", "#3D405B"],
        "decorative_range": ["#F0F0F0", "#333333"],
    },
    "chalkboard": {
        "semantic": {"primary": "#F5F5DC", "accent": "#FFD700", "highlight": "#90EE90"},
        "chart": ["#F5F5DC", "#FFD700", "#90EE90", "#FF6B6B", "#87CEEB", "#DDA0DD",
                   "#F0E68C", "#FFA07A", "#98FB98", "#ADD8E6"],
        "decorative_range": ["#4A6B52", "#2E4033"],
    },
    "editorial_infographic": {
        "semantic": {"primary": "#1B2838", "accent": "#FF6B35", "highlight": "#2ECC71"},
        "chart": ["#3498DB", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C",
                   "#E67E22", "#2980B9", "#C0392B", "#16A085"],
        "decorative_range": ["#F5F7FA", "#1B2838"],
    },
    "fantasy_animation": {
        "semantic": {"primary": "#7C3AED", "accent": "#F97316", "highlight": "#FBBF24"},
        "chart": ["#7C3AED", "#F97316", "#22C55E", "#EC4899", "#06B6D4", "#FBBF24",
                   "#EF4444", "#8B5CF6", "#14B8A6", "#F472B6"],
        "decorative_range": ["#2D1654", "#1A0533"],
    },
    "intuition_machine": {
        "semantic": {"primary": "#B45309", "accent": "#FB923C", "highlight": "#F59E0B"},
        "chart": ["#D97706", "#15803D", "#B91C1C", "#7C3AED", "#0369A1", "#EC4899",
                   "#EA580C", "#059669", "#DC2626", "#6D28D9"],
        "decorative_range": ["#FEF3C7", "#78350F"],
    },
    "notion": {
        "semantic": {"primary": "#37352F", "accent": "#2EAADC", "highlight": "#0F7B6C"},
        "chart": ["#2EAADC", "#EB5757", "#0F7B6C", "#DFAB01", "#9B59B6", "#E07C24",
                   "#6C5CE7", "#00B894", "#D63031", "#636E72"],
        "decorative_range": ["#F7F6F3", "#E8E7E4"],
    },
    "pixel_art": {
        "semantic": {"primary": "#2D6A4F", "accent": "#F72585", "highlight": "#FCA311"},
        "chart": ["#52B788", "#F72585", "#FCA311", "#4CC9F0", "#7209B7", "#4895EF",
                   "#FF6B6B", "#FFD166", "#06D6A0", "#118AB2"],
        "decorative_range": ["#232344", "#1A1A2E"],
    },
    "sketch_notes": {
        "semantic": {"primary": "#3D3D3D", "accent": "#FF6F61", "highlight": "#FFB347"},
        "chart": ["#FF6F61", "#66CDAA", "#FFB347", "#87CEEB", "#DDA0DD", "#98D8C8",
                   "#F7DC6F", "#AED6F1", "#F5B7B1", "#A3E4D7"],
        "decorative_range": ["#FFF0E0", "#FFF8F0"],
    },
    "vector_illustration": {
        "semantic": {"primary": "#1D3557", "accent": "#E63946", "highlight": "#E9C46A"},
        "chart": ["#457B9D", "#E63946", "#2A9D8F", "#E9C46A", "#F4A261", "#264653",
                   "#A8DADC", "#2B9348", "#80CED7", "#EF476F"],
        "decorative_range": ["#E8F4E0", "#1D3557"],
    },
    "vintage": {
        "semantic": {"primary": "#6B3A2A", "accent": "#C4864C", "highlight": "#8B5E3C"},
        "chart": ["#C4864C", "#8B5E3C", "#A0522D", "#7D8B6A", "#B5651D", "#6B3A2A",
                   "#D4A574", "#CD853F", "#8B7355", "#D2B48C"],
        "decorative_range": ["#F5EAD8", "#3E2723"],
    },
    "watercolor": {
        "semantic": {"primary": "#5B8BA0", "accent": "#E8A0BF", "highlight": "#8FC1A9"},
        "chart": ["#5B8BA0", "#E8A0BF", "#8FC1A9", "#E8C170", "#B4A7D6", "#85C1E9",
                   "#F0B27A", "#AED6F1", "#D2B4DE", "#A3E4D7"],
        "decorative_range": ["#F0EBE5", "#3A4A5A"],
    },
}


def get_color_zones(palette: str) -> dict[str, Any]:
    """获取配色方案的 3 区色彩模型

    Zone 1 (semantic): 语义色 — primary/accent/highlight，固定不可变
    Zone 2 (chart): 图表色板 — 8-12 色序列，固定不可变
    Zone 3 (decorative): 装饰色范围 — [lightest, darkest] 边界

    Args:
        palette: 配色方案名
    Returns:
        {"semantic": {...}, "chart": [...], "decorative_range": [...]}
    """
    return COLOR_ZONES.get(palette, COLOR_ZONES["corporate"])


def get_chart_palette(palette: str) -> list[str]:
    """获取图表色板（Zone 2）

    Args:
        palette: 配色方案名
    Returns:
        10 色 HEX 列表
    """
    zones = get_color_zones(palette)
    return zones.get("chart", COLOR_ZONES["corporate"]["chart"])


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
    "minimal": {"type": "linear", "angle": 180, "stops": ["#2563EB", "#60A5FA"]},
    "tech": {"type": "linear", "angle": 135, "stops": ["#8B5CF6", "#06B6D4"]},
    "elegant": {"type": "linear", "angle": 180, "stops": ["#064E3B", "#065F46"]},
    "flat": {"type": "linear", "angle": 180, "stops": ["#0EA5E9", "#7DD3FC"]},
    "chinese": {"type": "linear", "angle": 135, "stops": ["#DC2626", "#D4AF37"]},
    "warm": {"type": "linear", "angle": 135, "stops": ["#D97706", "#FBBF24"]},
    "morandi": {"type": "linear", "angle": 180, "stops": ["#8B7E74", "#C4B5A6"]},
    "minimal_bw": {"type": "linear", "angle": 180, "stops": ["#000000", "#666666"]},
    "chinese_ink": {"type": "linear", "angle": 180, "stops": ["#2C3E50", "#1ABC9C"]},
    "morandi_blue": {"type": "linear", "angle": 180, "stops": ["#6B8FAD", "#A7C7E7"]},
    "morandi_pink": {"type": "linear", "angle": 180, "stops": ["#C4A4A4", "#E8CCCC"]},
    "morandi_green": {"type": "linear", "angle": 180, "stops": ["#7D8B6A", "#B8C9A3"]},
    "sunset": {"type": "linear", "angle": 135, "stops": ["#F97316", "#EC4899"]},
    "ocean": {"type": "linear", "angle": 135, "stops": ["#0EA5E9", "#8B5CF6"]},
    "forest": {"type": "linear", "angle": 135, "stops": ["#059669", "#0D9488"]},
    # ppt-agent 扩展风格渐变
    "blueprint": {"type": "linear", "angle": 180, "stops": ["#1E3A8A", "#0C1D3A"]},
    "bold_editorial": {"type": "linear", "angle": 135, "stops": ["#111111", "#333333"]},
    "chalkboard": {"type": "linear", "angle": 180, "stops": ["#3A5141", "#2E4033"]},
    "editorial_infographic": {"type": "linear", "angle": 135, "stops": ["#1B2838", "#2A4060"]},
    "fantasy_animation": {"type": "linear", "angle": 135, "stops": ["#7C3AED", "#F97316"]},
    "intuition_machine": {"type": "linear", "angle": 135, "stops": ["#B45309", "#F59E0B"]},
    "notion": {"type": "linear", "angle": 180, "stops": ["#FFFFFF", "#F7F6F3"]},
    "pixel_art": {"type": "linear", "angle": 180, "stops": ["#1A1A2E", "#232344"]},
    "sketch_notes": {"type": "linear", "angle": 180, "stops": ["#FFF8F0", "#FFF0E0"]},
    "vector_illustration": {"type": "linear", "angle": 135, "stops": ["#1D3557", "#457B9D"]},
    "vintage": {"type": "linear", "angle": 180, "stops": ["#6B3A2A", "#8B5E3C"]},
    "watercolor": {"type": "linear", "angle": 135, "stops": ["#5B8BA0", "#E8A0BF"]},
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
    # ppt-agent 扩展风格字体映射
    "blueprint":              {"body": "Cascadia Code",      "display": "Cascadia Code"},
    "bold_editorial":         {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "chalkboard":             {"body": "KaiTi",              "display": "KaiTi"},
    "editorial_infographic":  {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "fantasy_animation":      {"body": "Microsoft YaHei",    "display": "Microsoft YaHei"},
    "intuition_machine":      {"body": "DengXian",           "display": "DengXian"},
    "notion":                 {"body": "DengXian",           "display": "DengXian"},
    "pixel_art":              {"body": "Consolas",           "display": "Consolas"},
    "sketch_notes":           {"body": "KaiTi",              "display": "KaiTi"},
    "vector_illustration":    {"body": "Microsoft YaHei UI", "display": "Microsoft YaHei UI"},
    "vintage":                {"body": "SimSun",             "display": "KaiTi"},
    "watercolor":             {"body": "DengXian",           "display": "KaiTi"},
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
    "COLOR_ZONES",
    "get_palette",
    "get_font",
    "get_font_family",
    "get_font_for_palette",
    "get_layout",
    "get_shadow",
    "get_gradient",
    "colored_shadow",
    "palette_to_style",
    "get_color_zones",
    "get_chart_palette",
]
