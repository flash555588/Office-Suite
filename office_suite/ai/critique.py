"""设计质量评审 — 自动检查设计质量

设计方案第九章：
  - 对比度检查: 文本/背景对比度是否符合 WCAG AA
  - 对齐检查: 元素是否对齐到网格
  - 层次检查: 标题/正文字号层次是否清晰
  - 一致性检查: 同类元素样式是否一致

检查结果分级: ERROR (必须修复) / WARNING (建议修复) / INFO (提示)

数据流：
  IRDocument → [本模块] → CritiqueReport
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..ir.types import IRDocument, IRNode, IRStyle, NodeType


class CritiqueSeverity(Enum):
    """评审严重程度"""
    ERROR = "error"      # 必须修复
    WARNING = "warning"  # 建议修复
    INFO = "info"        # 提示


@dataclass
class CritiqueIssue:
    """单个评审问题"""
    severity: CritiqueSeverity
    category: str         # contrast / alignment / hierarchy / consistency
    message: str
    node_name: str = ""
    suggestion: str = ""


@dataclass
class CritiqueReport:
    """评审报告"""
    issues: list[CritiqueIssue] = field(default_factory=list)
    score: float = 100.0  # 0-100 质量分

    @property
    def errors(self) -> list[CritiqueIssue]:
        return [i for i in self.issues if i.severity == CritiqueSeverity.ERROR]

    @property
    def warnings(self) -> list[CritiqueIssue]:
        return [i for i in self.issues if i.severity == CritiqueSeverity.WARNING]

    @property
    def is_passing(self) -> bool:
        return len(self.errors) == 0


def critique_document(doc: IRDocument) -> CritiqueReport:
    """评审 IRDocument 设计质量

    Args:
        doc: IR 文档

    Returns:
        CritiqueReport 评审报告
    """
    report = CritiqueReport()

    # 收集所有内容节点
    all_nodes = _collect_content_nodes(doc)

    # 1. 对比度检查
    _check_contrast(all_nodes, report)

    # 2. 层次检查
    _check_hierarchy(all_nodes, report)

    # 3. 一致性检查
    _check_consistency(all_nodes, report)

    # 4. 布局检查
    _check_layout(all_nodes, report)

    # 计算质量分
    report.score = _calculate_score(report)

    return report


def _collect_content_nodes(doc: IRDocument) -> list[IRNode]:
    """递归收集所有内容节点"""
    nodes = []

    def walk(node: IRNode):
        if node.node_type in (NodeType.TEXT, NodeType.IMAGE, NodeType.SHAPE,
                               NodeType.TABLE, NodeType.CHART):
            nodes.append(node)
        for child in node.children:
            walk(child)

    for child in doc.children:
        walk(child)

    return nodes


# ============================================================
# 对比度检查
# ============================================================

def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """HEX → RGB"""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 8:
        hex_str = hex_str[:6]
    if len(hex_str) != 6:
        return (0, 0, 0)
    try:
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except ValueError:
        return (0, 0, 0)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """计算相对亮度 (WCAG 2.1)"""
    def linearize(c: int) -> float:
        c_srgb = c / 255.0
        if c_srgb <= 0.03928:
            return c_srgb / 12.92
        return ((c_srgb + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast_ratio(color1: str, color2: str) -> float:
    """计算两颜色的对比度 (WCAG 2.1)"""
    l1 = _relative_luminance(_hex_to_rgb(color1))
    l2 = _relative_luminance(_hex_to_rgb(color2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _check_contrast(nodes: list[IRNode], report: CritiqueReport):
    """检查文本/背景对比度"""
    for node in nodes:
        if node.node_type != NodeType.TEXT:
            continue
        style = node.style
        if style is None:
            continue

        text_color = style.font_color
        bg_color = style.fill_color

        if text_color and bg_color:
            ratio = _contrast_ratio(text_color, bg_color)
            if ratio < 4.5:
                report.issues.append(CritiqueIssue(
                    severity=CritiqueSeverity.WARNING,
                    category="contrast",
                    message=f"对比度不足: {ratio:.1f}:1 (最低 4.5:1)",
                    node_name=node.content[:20] if node.content else "",
                    suggestion="调整文本色或背景色以提高对比度",
                ))
            elif ratio < 7.0:
                report.issues.append(CritiqueIssue(
                    severity=CritiqueSeverity.INFO,
                    category="contrast",
                    message=f"对比度尚可: {ratio:.1f}:1 (推荐 7:1)",
                    node_name=node.content[:20] if node.content else "",
                ))


# ============================================================
# 层次检查
# ============================================================

def _check_hierarchy(nodes: list[IRNode], report: CritiqueReport):
    """检查标题/正文层次"""
    text_sizes = []
    for node in nodes:
        if node.node_type == NodeType.TEXT and node.style and node.style.font_size:
            text_sizes.append((node.content[:20] if node.content else "", node.style.font_size))

    if len(text_sizes) < 2:
        return

    sizes = [s for _, s in text_sizes]
    max_size = max(sizes)
    min_size = min(sizes)

    # 层次不够分明
    if max_size - min_size < 8 and max_size > 14:
        report.issues.append(CritiqueIssue(
            severity=CritiqueSeverity.WARNING,
            category="hierarchy",
            message=f"字号层次不够分明: 最大 {max_size}pt, 最小 {min_size}pt (差值 < 8pt)",
            suggestion="增大标题与正文字号差异",
        ))

    # 检查是否有标题级别
    has_heading = any(s >= 24 for _, s in text_sizes)
    has_body = any(s <= 16 for _, s in text_sizes)
    if has_heading and not has_body:
        report.issues.append(CritiqueIssue(
            severity=CritiqueSeverity.INFO,
            category="hierarchy",
            message="只有标题没有正文，考虑添加正文段落",
        ))


# ============================================================
# 一致性检查
# ============================================================

def _check_consistency(nodes: list[IRNode], report: CritiqueReport):
    """检查同类元素样式一致性"""
    # 收集同类文本元素的字号
    text_by_size: dict[int, list[str]] = {}
    for node in nodes:
        if node.node_type == NodeType.TEXT and node.style and node.style.font_size:
            size = node.style.font_size
            if size not in text_by_size:
                text_by_size[size] = []
            text_by_size[size].append(node.content[:15] if node.content else "")

    # 如果有太多不同的字号（超过 4 种），提示不一致
    if len(text_by_size) > 4:
        report.issues.append(CritiqueIssue(
            severity=CritiqueSeverity.WARNING,
            category="consistency",
            message=f"使用了 {len(text_by_size)} 种不同字号，建议统一为 3-4 种",
            suggestion="建立统一的字号体系: 标题/子标题/正文/注释",
        ))

    # 检查表格样式一致性
    table_nodes = [n for n in nodes if n.node_type == NodeType.TABLE]
    if len(table_nodes) > 1:
        # 如果有多个表格，检查它们是否有相同的行列结构
        structures = set()
        for t in table_nodes:
            rows = t.extra.get("rows", 0)
            cols = t.extra.get("cols", 0)
            structures.add((rows, cols))
        if len(structures) > 1:
            report.issues.append(CritiqueIssue(
                severity=CritiqueSeverity.INFO,
                category="consistency",
                message=f"多个表格结构不一致: {structures}",
                suggestion="考虑统一表格行列数",
            ))


# ============================================================
# 布局检查
# ============================================================

def _check_layout(nodes: list[IRNode], report: CritiqueReport):
    """检查布局质量"""
    # 收集所有有位置的节点
    positioned = [(n, n.position) for n in nodes if n.position]

    if len(positioned) < 2:
        return

    # 检查元素重叠
    for i, (n1, p1) in enumerate(positioned):
        for j, (n2, p2) in enumerate(positioned):
            if j <= i:
                continue
            if _positions_overlap(p1, p2):
                report.issues.append(CritiqueIssue(
                    severity=CritiqueSeverity.WARNING,
                    category="alignment",
                    message=f"元素可能重叠: '{n1.content[:10]}' 和 '{n2.content[:10]}'",
                    suggestion="调整位置或添加间距",
                ))

    # 检查元素是否超出边界（16:9 幻灯片 254mm x 142.875mm）
    for node, pos in positioned:
        if pos.x_mm + pos.width_mm > 260:
            report.issues.append(CritiqueIssue(
                severity=CritiqueSeverity.WARNING,
                category="alignment",
                message=f"元素超出右边界: x={pos.x_mm:.0f}mm + w={pos.width_mm:.0f}mm",
                node_name=node.content[:15] if node.content else "",
                suggestion="减小宽度或调整 x 坐标",
            ))
        if pos.y_mm + pos.height_mm > 148:
            report.issues.append(CritiqueIssue(
                severity=CritiqueSeverity.WARNING,
                category="alignment",
                message=f"元素超出下边界: y={pos.y_mm:.0f}mm + h={pos.height_mm:.0f}mm",
                node_name=node.content[:15] if node.content else "",
                suggestion="减小高度或调整 y 坐标",
            ))


def _positions_overlap(p1, p2) -> bool:
    """检查两个位置是否重叠"""
    return not (
        p1.x_mm + p1.width_mm <= p2.x_mm or
        p2.x_mm + p2.width_mm <= p1.x_mm or
        p1.y_mm + p1.height_mm <= p2.y_mm or
        p2.y_mm + p2.height_mm <= p1.y_mm
    )


# ============================================================
# 质量分计算
# ============================================================

def _calculate_score(report: CritiqueReport) -> float:
    """计算质量分 (0-100)"""
    score = 100.0
    for issue in report.issues:
        if issue.severity == CritiqueSeverity.ERROR:
            score -= 15.0
        elif issue.severity == CritiqueSeverity.WARNING:
            score -= 5.0
        elif issue.severity == CritiqueSeverity.INFO:
            score -= 1.0
    return max(0.0, min(100.0, score))
