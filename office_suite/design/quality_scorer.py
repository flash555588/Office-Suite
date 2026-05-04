"""5 维质量评分框架 — 纯规则检查，无需 LLM

评分维度（来自 ppt-agent 的评估体系，适配 Office Suite）：

  1. 视觉节奏 (Visual Rhythm)     25% — 布局多样性，同类页是否有变化
  2. 色彩叙事 (Color Narrative)    20% — 色彩一致性，是否遵循 3 区模型
  3. 叙事弧 (Narrative Arc)        20% — 内容逻辑，首/中/尾页是否合理
  4. 风格一致性 (Style Consistency) 20% — 主题 token 贯穿度
  5. 节奏 (Pacing)                 15% — 页面密度变化（避免全 dense 或全 sparse）

用法：
    from office_suite.design.quality_scorer import score_document
    result = score_document(ir_doc, palette="corporate")
    print(result.total)       # 0-100
    print(result.dimensions)  # 各维度得分
    print(result.report())    # 人类可读报告

架构位置：ir/compiler.py 输出 IR 后，renderer 渲染前调用。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..ir.types import IRDocument, IRNode, NodeType, IRStyle
from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM

logger = logging.getLogger(__name__)

# 维度权重
WEIGHTS = {
    "visual_rhythm": 0.25,
    "color_narrative": 0.20,
    "narrative_arc": 0.20,
    "style_consistency": 0.20,
    "pacing": 0.15,
}

# 评分等级
def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


@dataclass
class DimensionScore:
    """单维度评分"""
    name: str
    score: float  # 0-100
    weight: float
    issues: list[str] = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return self.score * self.weight

    @property
    def grade(self) -> str:
        return _grade(self.score)


@dataclass
class QualityResult:
    """质量评分结果"""
    dimensions: dict[str, DimensionScore] = field(default_factory=dict)
    palette: str = ""

    @property
    def total(self) -> float:
        """加权总分（0-100）"""
        return sum(d.weighted for d in self.dimensions.values())

    @property
    def grade(self) -> str:
        return _grade(self.total)

    def report(self) -> str:
        """生成人类可读报告"""
        lines = [f"Quality Score: {self.total:.0f}/100 ({self.grade})"]
        if self.palette:
            lines.append(f"Palette: {self.palette}")
        lines.append("")
        for dim in self.dimensions.values():
            issues_str = f"  [{len(dim.issues)} issues]" if dim.issues else ""
            lines.append(f"  {dim.name:<25} {dim.score:.0f}/100 ({dim.grade}){issues_str}")
            for issue in dim.issues[:3]:  # 最多显示 3 个
                lines.append(f"    - {issue}")
        return "\n".join(lines)


# ============================================================
# 维度 1: 视觉节奏 (Visual Rhythm) — 25%
# ============================================================

def _score_visual_rhythm(slides: list[IRNode]) -> DimensionScore:
    """检查布局多样性

    高分：不同幻灯片使用不同布局模式（grid/flex/absolute）
    低分：所有幻灯片都用同一种布局
    """
    issues = []
    if not slides:
        return DimensionScore("Visual Rhythm", 0, WEIGHTS["visual_rhythm"],
                              ["No slides found"])

    # 统计每张幻灯片使用的布局模式
    modes = []
    for slide in slides:
        mode = slide.extra.get("layout_mode", "absolute")
        modes.append(mode)

    unique_modes = set(modes)
    diversity_ratio = len(unique_modes) / max(len(modes), 1)

    # 统计每张幻灯片的子元素数量变化
    child_counts = [len(slide.children) for slide in slides]
    if len(child_counts) >= 2:
        avg_children = sum(child_counts) / len(child_counts)
        variance = sum((c - avg_children) ** 2 for c in child_counts) / len(child_counts)
        has_variance = variance > 1.0
    else:
        has_variance = False

    # 计算基础分
    score = 60.0  # 基准分

    # 布局多样性加分
    if len(unique_modes) >= 3:
        score += 25
    elif len(unique_modes) >= 2:
        score += 15
    elif len(unique_modes) == 1 and len(slides) > 3:
        issues.append(f"All {len(slides)} slides use the same layout mode '{modes[0]}'")
        score -= 10

    # 子元素数量变化加分
    if has_variance:
        score += 15
    elif len(slides) > 3:
        issues.append("Child element counts are uniform across slides")

    return DimensionScore("Visual Rhythm", max(0, min(100, score)),
                          WEIGHTS["visual_rhythm"], issues)


# ============================================================
# 维度 2: 色彩叙事 (Color Narrative) — 20%
# ============================================================

def _score_color_narrative(slides: list[IRNode], palette: str | None) -> DimensionScore:
    """检查色彩一致性

    高分：颜色来自主题 palette，无随机十六进制
    低分：大量颜色不在主题中
    """
    issues = []
    if not palette:
        return DimensionScore("Color Narrative", 70, WEIGHTS["color_narrative"],
                              ["No palette specified, cannot verify color consistency"])

    from .tokens import get_color_zones, PALETTE

    zones = get_color_zones(palette)
    allowed_colors = set()
    # Zone 1 语义色
    for v in zones["semantic"].values():
        allowed_colors.add(v.upper())
    # Zone 2 图表色
    for c in zones["chart"]:
        allowed_colors.add(c.upper())
    # 主调色板中的 bg/text/border 等基础色（3 区模型不含这些）
    pal = PALETTE.get(palette, {})
    for v in pal.values():
        if isinstance(v, str) and v.startswith("#"):
            allowed_colors.add(v.upper())

    # 收集所有幻灯片中使用的颜色
    found_colors: set[str] = set()
    for slide in slides:
        _collect_colors_recursive(slide, found_colors)

    if not found_colors:
        return DimensionScore("Color Narrative", 80, WEIGHTS["color_narrative"],
                              ["No explicit colors found in IR nodes"])

    # 检查有多少颜色在允许范围内
    matched = 0
    unmatched = 0
    for c in found_colors:
        c_upper = c.upper().lstrip("#")
        if len(c_upper) >= 6:
            c_hex = f"#{c_upper[:6]}"
        else:
            c_hex = f"#{c_upper}"
        if c_hex in allowed_colors:
            matched += 1
        else:
            unmatched += 1

    total = matched + unmatched
    if total == 0:
        return DimensionScore("Color Narrative", 80, WEIGHTS["color_narrative"], [])

    consistency = matched / total
    score = 50 + consistency * 50  # 50-100

    if consistency < 0.5:
        issues.append(f"Only {matched}/{total} colors match palette '{palette}'")
    if unmatched > 5:
        issues.append(f"{unmatched} colors outside palette zones")

    return DimensionScore("Color Narrative", max(0, min(100, score)),
                          WEIGHTS["color_narrative"], issues)


def _collect_colors_recursive(node: IRNode, out: set[str]):
    """递归收集节点中的所有颜色"""
    if node.style:
        if node.style.font_color:
            out.add(node.style.font_color)
        if node.style.fill_color:
            out.add(node.style.fill_color)
    for child in node.children:
        _collect_colors_recursive(child, out)


# ============================================================
# 维度 3: 叙事弧 (Narrative Arc) — 20%
# ============================================================

def _score_narrative_arc(slides: list[IRNode]) -> DimensionScore:
    """检查内容逻辑

    理想结构：封面页 → 内容页（多张）→ 总结页
    高分：符合此结构
    低分：没有明确的开头/结尾，或只有 1 页
    """
    issues = []
    n = len(slides)

    if n == 0:
        return DimensionScore("Narrative Arc", 0, WEIGHTS["narrative_arc"],
                              ["No slides found"])
    if n == 1:
        return DimensionScore("Narrative Arc", 50, WEIGHTS["narrative_arc"],
                              ["Single slide — no narrative arc possible"])

    score = 60.0  # 基准分

    # 检查首页：是否有标题/封面类元素
    first = slides[0]
    first_children = len(first.children)
    first_has_text = any(c.node_type == NodeType.TEXT and c.content for c in first.children)

    if first_children <= 3 and first_has_text:
        score += 15  # 封面页通常元素少但有文字
    elif first_children > 6:
        issues.append("First slide has many elements — may lack clear opening")

    # 检查尾页：是否与中间页有差异
    last = slides[-1]
    last_children = len(last.children)
    mid_children = [len(s.children) for s in slides[1:-1]] if n > 2 else [3]

    if mid_children:
        avg_mid = sum(mid_children) / len(mid_children)
        if last_children <= avg_mid * 0.8:
            score += 10  # 尾页更简洁 → 合理
        elif last_children > avg_mid * 1.5:
            issues.append("Last slide is denser than middle slides — consider simplifying")

    # 页数合理性
    if 5 <= n <= 20:
        score += 15  # 合理范围
    elif n > 20:
        issues.append(f"{n} slides — may be too long for a single narrative")
        score -= 5
    elif n < 3:
        issues.append(f"Only {n} slides — limited narrative depth")

    return DimensionScore("Narrative Arc", max(0, min(100, score)),
                          WEIGHTS["narrative_arc"], issues)


# ============================================================
# 维度 4: 风格一致性 (Style Consistency) — 20%
# ============================================================

def _score_style_consistency(slides: list[IRNode], doc: IRDocument) -> DimensionScore:
    """检查主题 token 贯穿度

    高分：大部分节点使用 style_ref 或一致的 inline 样式
    低分：大量随机 inline 样式，无 style_ref
    """
    issues = []
    total_nodes = 0
    with_style_ref = 0
    with_inline_style = 0
    with_no_style = 0
    font_families: set[str] = set()

    for slide in slides:
        _count_styles_recursive(slide, total_nodes_holder := [0],
                                 ref_holder := [0], inline_holder := [0],
                                 none_holder := [0], font_families)
        total_nodes += total_nodes_holder[0]
        with_style_ref += ref_holder[0]
        with_inline_style += inline_holder[0]
        with_no_style += none_holder[0]

    if total_nodes == 0:
        return DimensionScore("Style Consistency", 80, WEIGHTS["style_consistency"], [])

    score = 60.0  # 基准分

    # style_ref 使用率
    ref_ratio = with_style_ref / total_nodes
    if ref_ratio > 0.7:
        score += 25
    elif ref_ratio > 0.3:
        score += 10
    else:
        issues.append(f"Only {with_style_ref}/{total_nodes} nodes use style_ref")

    # 字体多样性（越少越好）
    if len(font_families) <= 2:
        score += 15
    elif len(font_families) <= 4:
        score += 5
    else:
        issues.append(f"{len(font_families)} different font families — too many")
        score -= 5

    # 无样式节点比例
    no_style_ratio = with_no_style / total_nodes
    if no_style_ratio > 0.3:
        issues.append(f"{with_no_style}/{total_nodes} nodes have no style at all")
        score -= 10

    return DimensionScore("Style Consistency", max(0, min(100, score)),
                          WEIGHTS["style_consistency"], issues)


def _count_styles_recursive(
    node: IRNode,
    total: list[int],
    ref_count: list[int],
    inline_count: list[int],
    none_count: list[int],
    font_families: set[str],
):
    """递归统计样式使用情况"""
    total[0] += 1
    if node.style_ref:
        ref_count[0] += 1
    if node.style:
        inline_count[0] += 1
        if node.style.font_family:
            font_families.add(node.style.font_family)
    elif not node.style_ref:
        none_count[0] += 1

    for child in node.children:
        _count_styles_recursive(child, total, ref_count, inline_count, none_count, font_families)


# ============================================================
# 维度 5: 节奏 (Pacing) — 15%
# ============================================================

def _score_pacing(slides: list[IRNode]) -> DimensionScore:
    """检查页面密度变化

    高分：页面密度有变化（有的简洁，有的丰富）
    低分：所有页面都 dense 或都 sparse
    """
    issues = []
    if len(slides) < 2:
        return DimensionScore("Pacing", 70, WEIGHTS["pacing"],
                              ["Too few slides to assess pacing"])

    densities = []
    for slide in slides:
        # 密度 = 子元素数量 + 内容总字符数 / 100
        child_count = len(slide.children)
        content_chars = sum(len(c.content or "") for c in slide.children
                           if c.node_type == NodeType.TEXT)
        density = child_count + content_chars / 100
        densities.append(density)

    avg = sum(densities) / len(densities)
    if avg == 0:
        return DimensionScore("Pacing", 60, WEIGHTS["pacing"], [])

    # 变异系数 (CV)
    variance = sum((d - avg) ** 2 for d in densities) / len(densities)
    cv = (variance ** 0.5) / avg if avg > 0 else 0

    score = 60.0

    # CV 在 0.2-0.6 为理想区间
    if 0.2 <= cv <= 0.6:
        score += 30
    elif 0.1 <= cv < 0.2:
        score += 15
        issues.append("Pacing is slightly uniform — consider more density variation")
    elif cv > 0.6:
        score += 10
        issues.append("Pacing is highly variable — check if intentional")
    else:  # cv < 0.1
        issues.append("All slides have nearly identical density — pacing is flat")
        score -= 10

    # 检查是否有极稀疏或极密集的页面
    for i, d in enumerate(densities):
        if d > avg * 3:
            issues.append(f"Slide[{i}] is much denser than average")
        elif d < avg * 0.2 and avg > 1:
            issues.append(f"Slide[{i}] is much sparser than average")

    return DimensionScore("Pacing", max(0, min(100, score)),
                          WEIGHTS["pacing"], issues)


# ============================================================
# 入口函数
# ============================================================

def score_document(
    doc: IRDocument,
    palette: str | None = None,
) -> QualityResult:
    """对 IR 文档进行 5 维质量评分

    Args:
        doc: IR 文档
        palette: 配色方案名（用于色彩叙事维度）

    Returns:
        QualityResult，包含各维度分数和总体报告
    """
    slides = doc.children

    result = QualityResult(palette=palette or "")
    result.dimensions["visual_rhythm"] = _score_visual_rhythm(slides)
    result.dimensions["color_narrative"] = _score_color_narrative(slides, palette)
    result.dimensions["narrative_arc"] = _score_narrative_arc(slides)
    result.dimensions["style_consistency"] = _score_style_consistency(slides, doc)
    result.dimensions["pacing"] = _score_pacing(slides)

    logger.info("Quality score: %.0f/100 (%s)", result.total, result.grade)
    return result
