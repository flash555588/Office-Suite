"""Markdown → RichDocument 解析器

支持的 Markdown 语法：
  **bold**          → 加粗
  *italic*          → 斜体
  ***bold italic*** → 加粗+斜体
  ~~strikethrough~~ → 删除线
  `code`            → 等宽字体
  __underline__     → 下划线
  \n\n              → 分段
  - item / * item   → 无序列表
  1. item           → 有序列表
  # heading         → 标题（字号递增）
  > quote           → 引用（缩进+斜体）
  ---               → 水平线分隔

不支持：链接、图片、表格、代码块、HTML 标签。
这些超出 PPT 文本框的合理需求，如有需要请使用手写元素组合。
"""

from __future__ import annotations

import re
from .rich_text import RichDocument, RichParagraph, TextRun

# 内联样式正则（按优先级排列）
_INLINE_PATTERNS = [
    # ***bold italic*** — 必须在 ** 和 * 之前匹配
    (re.compile(r"\*\*\*(.+?)\*\*\*"), {"bold": True, "italic": True}),
    # **bold**
    (re.compile(r"\*\*(.+?)\*\*"), {"bold": True}),
    # *italic*
    (re.compile(r"\*(.+?)\*"), {"italic": True}),
    # __underline__
    (re.compile(r"__(.+?)__"), {"underline": True}),
    # ~~strikethrough~~
    (re.compile(r"~~(.+?)~~"), {"strikethrough": True}),
    # `code`
    (re.compile(r"`(.+?)`"), {"font_family": "Consolas", "bg_color": "#F1F5F9"}),
]

# 块级语法检测
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.+)$")
_ORDERED_RE = re.compile(r"^(\s*)\d+\.\s+(.+)$")
_QUOTE_RE = re.compile(r"^>\s*(.*)$")
_HR_RE = re.compile(r"^[-*_]{3,}\s*$")

# 标题字号映射（pt）
_HEADING_SIZES = {
    1: 28,
    2: 24,
    3: 20,
    4: 18,
    5: 16,
    6: 14,
}


def parse_markdown(text: str) -> RichDocument:
    """将 Markdown 文本解析为 RichDocument

    Args:
        text: Markdown 格式文本

    Returns:
        RichDocument 实例
    """
    doc = RichDocument()
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # 空行 → 分段标记
        if not line.strip():
            # 连续空行不产生多余段落
            i += 1
            continue

        # 水平线
        if _HR_RE.match(line.strip()):
            para = doc.add_paragraph()
            para.add_run("─" * 40, color="#CBD5E1")
            i += 1
            continue

        # 标题
        m = _HEADING_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            content = m.group(2)
            para = doc.add_paragraph()
            para.add_run(
                content,
                bold=True,
                font_size=_HEADING_SIZES.get(level, 16),
                color="#0F172A",
            )
            i += 1
            continue

        # 引用
        m = _QUOTE_RE.match(line.strip())
        if m:
            content = m.group(1)
            para = doc.add_paragraph()
            para.add_run("│ ", color="#94A3B8")
            _add_inline_runs(para, content, default_italic=True, default_color="#475569")
            i += 1
            continue

        # 无序列表
        m = _BULLET_RE.match(line)
        if m:
            indent = len(m.group(1))
            content = m.group(2)
            para = doc.add_paragraph()
            bullet = "  " * (indent // 2) + "• "
            para.add_run(bullet, color="#64748B")
            _add_inline_runs(para, content)
            i += 1
            continue

        # 有序列表
        m = _ORDERED_RE.match(line)
        if m:
            indent = len(m.group(1))
            content = m.group(2)
            # 提取序号
            num_match = re.match(r"(\s*)\d+\.", line)
            num = num_match.group(0).strip() if num_match else "1."
            para = doc.add_paragraph()
            para.add_run("  " * (indent // 2) + num + " ", color="#64748B")
            _add_inline_runs(para, content)
            i += 1
            continue

        # 普通段落（合并连续非空行）
        para = doc.add_paragraph()
        _add_inline_runs(para, line.strip())
        i += 1

        # 合并后续非空行到同一段落（Markdown 的软换行）
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i]):
            para.add_run(" ")
            _add_inline_runs(para, lines[i].strip())
            i += 1

    return doc


def _is_block_start(line: str) -> bool:
    """判断是否为块级元素的起始行"""
    stripped = line.strip()
    if not stripped:
        return True
    if _HEADING_RE.match(stripped):
        return True
    if _BULLET_RE.match(line):
        return True
    if _ORDERED_RE.match(line):
        return True
    if _QUOTE_RE.match(stripped):
        return True
    if _HR_RE.match(stripped):
        return True
    return False


def _add_inline_runs(
    para: RichParagraph,
    text: str,
    default_bold: bool = False,
    default_italic: bool = False,
    default_color: str | None = None,
) -> None:
    """解析内联样式并添加到段落

    使用贪心匹配策略：从左到右扫描，找到第一个匹配就处理。
    """
    if not text:
        return

    remaining = text
    while remaining:
        earliest_pos = len(remaining)
        earliest_match = None
        earliest_styles = None

        # 找到最早出现的内联样式
        for pattern, styles in _INLINE_PATTERNS:
            m = pattern.search(remaining)
            if m and m.start() < earliest_pos:
                earliest_pos = m.start()
                earliest_match = m
                earliest_styles = styles

        if earliest_match is None:
            # 没有更多样式，剩余部分作为普通文本
            if remaining:
                kwargs = {}
                if default_bold:
                    kwargs["bold"] = True
                if default_italic:
                    kwargs["italic"] = True
                if default_color:
                    kwargs["color"] = default_color
                para.add_run(remaining, **kwargs)
            break

        # 添加匹配前的普通文本
        if earliest_pos > 0:
            kwargs = {}
            if default_bold:
                kwargs["bold"] = True
            if default_italic:
                kwargs["italic"] = True
            if default_color:
                kwargs["color"] = default_color
            para.add_run(remaining[:earliest_pos], **kwargs)

        # 添加带样式的文本
        run_content = earliest_match.group(1)
        run_kwargs = dict(earliest_styles)
        if default_bold:
            run_kwargs.setdefault("bold", True)
        if default_italic:
            run_kwargs.setdefault("italic", True)
        if default_color and "color" not in run_kwargs:
            run_kwargs["color"] = default_color
        para.add_run(run_content, **run_kwargs)

        # 继续处理剩余部分
        remaining = remaining[earliest_match.end():]
