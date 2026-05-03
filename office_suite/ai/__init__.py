"""AI 设计助手 — 意图解析 + 设计建议 + 质量评审

设计方案第九章：AI 辅助设计流程。

模块：
  - intent.py: 自然语言 → DesignBrief 解析
  - suggest.py: 设计建议引擎（布局/配色/排版）
  - critique.py: 设计质量评审（对比度/层次/一致性）
"""

from .intent import DesignBrief, parse_intent
from .suggest import (
    ColorScheme,
    DesignSuggestion,
    LayoutSuggestion,
    TypographySuggestion,
    suggest_color_scheme,
    suggest_design,
    suggest_layout,
)
from .critique import (
    CritiqueIssue,
    CritiqueReport,
    CritiqueSeverity,
    critique_document,
)
from .media import (
    collect_dsl_media,
    import_media,
    import_media_batch,
    update_dsl_image_paths,
)

__all__ = [
    # intent
    "DesignBrief",
    "parse_intent",
    # suggest
    "ColorScheme",
    "DesignSuggestion",
    "LayoutSuggestion",
    "TypographySuggestion",
    "suggest_color_scheme",
    "suggest_design",
    "suggest_layout",
    # critique
    "CritiqueIssue",
    "CritiqueReport",
    "CritiqueSeverity",
    "critique_document",
    # media
    "import_media",
    "import_media_batch",
    "collect_dsl_media",
    "update_dsl_image_paths",
]
