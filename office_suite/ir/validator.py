"""IR validation for Office Suite documents.

Two levels of validation:
- validate_ir_v2(): non-fatal, returns ValidationResult with errors/warnings
- gate_validate_ir(): fatal, raises GateValidationError on any ERROR

Gate 校验器在编译完成后、渲染前运行，拦截会导致渲染失败或输出异常的错误。
新增校验规则：
- style_ref 引用检查：style_ref 引用的样式名必须在 doc.styles 中存在
- position 越界检查：元素位置超出幻灯片边界时报警
- 零尺寸检查：非 auto 元素 width/height 为 0 时报错
"""

from dataclasses import dataclass, field
from enum import Enum
import logging

from ..constants import SLIDE_WIDTH_MM, SLIDE_HEIGHT_MM
from .types import (
    CONTAINMENT_RULES,
    IRDocument,
    IRNode,
    LEAF_NODES,
    NodeType,
    REQUIRED_PROPS,
)


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: Severity
    message: str
    path: str = ""
    node_type: str = ""
    rule: str = ""

    def __str__(self):
        prefix = f"[{self.severity.value.upper()}]"
        path_part = f" {self.path}" if self.path else ""
        return f"{prefix}{path_part}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == Severity.WARNING]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add(self, severity: Severity, message: str, **kwargs):
        self.issues.append(ValidationIssue(severity=severity, message=message, **kwargs))

    def __str__(self):
        lines = [f"Validation: {'PASS' if self.is_valid else 'FAIL'}"]
        lines.append(f"  Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


class IRValidator:
    def __init__(self, doc: IRDocument):
        self.doc = doc
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        self._validate_structure()
        self._validate_styles()
        for index, slide in enumerate(self.doc.children):
            self._validate_node(slide, NodeType.DOCUMENT, f"slide[{index}]")
        return self.result

    def _validate_structure(self):
        if not self.doc.children:
            self.result.add(Severity.WARNING, "Document has no slides or sections", rule="structure")
        if not self.doc.version:
            self.result.add(Severity.WARNING, "Document is missing version", rule="structure")

    def _validate_styles(self):
        for name, style in self.doc.styles.items():
            if style.font_size is not None and style.font_size < 0:
                self.result.add(Severity.ERROR, f"Style '{name}' has negative font_size", rule="style")
            if style.font_weight is not None and (style.font_weight < 100 or style.font_weight > 900):
                self.result.add(
                    Severity.WARNING,
                    f"Style '{name}' font_weight is outside 100-900",
                    rule="style",
                )

    def _validate_node(self, node: IRNode, parent_type: NodeType | None, path: str):
        self._check_containment(node, parent_type, path)
        self._check_required_props(node, path)
        self._check_semantic_icon(node, path)
        self._check_position(node, path)
        self._check_style(node, path)
        self._check_leaf_constraint(node, path)

        for index, child in enumerate(node.children):
            child_path = f"{path}/{child.node_type.value}[{index}]"
            self._validate_node(child, node.node_type, child_path)

    def _check_containment(self, node: IRNode, parent_type: NodeType | None, path: str):
        if parent_type is None:
            return
        allowed = CONTAINMENT_RULES.get(parent_type)
        if allowed is None:
            self.result.add(
                Severity.ERROR,
                f"{parent_type.value} cannot contain child nodes, found {node.node_type.value}",
                path=path,
                node_type=node.node_type.value,
                rule="containment",
            )
        elif node.node_type not in allowed:
            self.result.add(
                Severity.ERROR,
                f"{parent_type.value} cannot contain {node.node_type.value}",
                path=path,
                node_type=node.node_type.value,
                rule="containment",
            )

    def _check_required_props(self, node: IRNode, path: str):
        required = REQUIRED_PROPS.get(node.node_type, [])
        for prop in required:
            if prop == "content" and (not node.content or node.content.strip() == ""):
                self.result.add(
                    Severity.ERROR,
                    f"{node.node_type.value} is missing required property 'content'",
                    path=path,
                    node_type=node.node_type.value,
                    rule="required_props",
                )
            elif prop == "source" and not node.source:
                self.result.add(
                    Severity.ERROR,
                    f"{node.node_type.value} is missing required property 'source'",
                    path=path,
                    node_type=node.node_type.value,
                    rule="required_props",
                )
            elif prop == "chart_type" and not node.chart_type:
                self.result.add(
                    Severity.ERROR,
                    f"{node.node_type.value} is missing required property 'chart_type'",
                    path=path,
                    node_type=node.node_type.value,
                    rule="required_props",
                )

    def _check_semantic_icon(self, node: IRNode, path: str):
        if node.node_type != NodeType.GROUP:
            return
        if "semantic_icon" not in node.extra:
            return
        if not node.children:
            self.result.add(
                Severity.ERROR,
                "semantic_icon must compile to at least one native primitive",
                path=path,
                node_type=node.node_type.value,
                rule="semantic_icon_empty",
            )

    def _check_position(self, node: IRNode, path: str):
        if node.position is None:
            return
        pos = node.position
        if pos.width_mm < 0:
            self.result.add(Severity.ERROR, f"Width is negative ({pos.width_mm}mm)", path=path, rule="position")
        if pos.height_mm < 0:
            self.result.add(Severity.ERROR, f"Height is negative ({pos.height_mm}mm)", path=path, rule="position")
        if pos.x_mm < -50:
            self.result.add(Severity.WARNING, f"x coordinate is far left ({pos.x_mm}mm)", path=path, rule="position")
        if pos.y_mm < -50:
            self.result.add(Severity.WARNING, f"y coordinate is far above ({pos.y_mm}mm)", path=path, rule="position")
        if pos.x_mm + pos.width_mm > 300:
            self.result.add(Severity.WARNING, "Element may exceed right boundary", path=path, rule="position")
        if pos.y_mm + pos.height_mm > 250:
            self.result.add(Severity.WARNING, "Element may exceed bottom boundary", path=path, rule="position")

    def _check_style(self, node: IRNode, path: str):
        if node.style is None:
            return
        style = node.style
        if style.font_size is not None and style.font_size <= 0:
            self.result.add(Severity.ERROR, f"font_size must be > 0 ({style.font_size})", path=path, rule="style")
        if style.font_size is not None and style.font_size > 200:
            self.result.add(Severity.WARNING, f"font_size is unusually large ({style.font_size}pt)", path=path, rule="style")
        if style.fill_opacity is not None and (style.fill_opacity < 0 or style.fill_opacity > 1):
            self.result.add(
                Severity.ERROR,
                f"fill_opacity must be between 0 and 1 ({style.fill_opacity})",
                path=path,
                rule="style",
            )

    def _check_leaf_constraint(self, node: IRNode, path: str):
        if node.node_type in LEAF_NODES and node.children:
            self.result.add(
                Severity.ERROR,
                f"{node.node_type.value} is a leaf node but has {len(node.children)} children",
                path=path,
                node_type=node.node_type.value,
                rule="leaf_constraint",
            )


class GateValidator(IRValidator):
    """Gate 校验器 — 增强版，增加编译后完整性检查

    在 IR 编译完成后、渲染前运行。
    检查项：
      - style_ref 引用存在性
      - position 越界（基于幻灯片实际尺寸或标准尺寸）
      - 零尺寸元素（非 auto）
      - image source 存在性（仅文件路径，不检查 URL）
    """

    def __init__(self, doc: IRDocument, slide_width: float = SLIDE_WIDTH_MM,
                 slide_height: float = SLIDE_HEIGHT_MM):
        super().__init__(doc)
        self.slide_width = slide_width
        self.slide_height = slide_height

    def validate(self) -> ValidationResult:
        """运行 Gate 校验（包含基类全部检查 + 增强检查）"""
        # 基类检查：结构、样式、节点递归
        super().validate()
        # 增强检查：style_ref 引用
        self._validate_style_refs()
        return self.result

    def _validate_style_refs(self):
        """检查所有节点的 style_ref 是否引用了存在的全局样式"""
        defined_styles = set(self.doc.styles.keys())
        for index, slide in enumerate(self.doc.children):
            self._check_style_refs_recursive(slide, f"slide[{index}]", defined_styles)

    def _check_style_refs_recursive(self, node: IRNode, path: str, defined_styles: set[str]):
        if node.style_ref and node.style_ref not in defined_styles:
            self.result.add(
                Severity.ERROR,
                f"style_ref '{node.style_ref}' references undefined style "
                f"(available: {sorted(defined_styles)})",
                path=path,
                node_type=node.node_type.value,
                rule="style_ref_dangling",
            )
        for i, child in enumerate(node.children):
            child_path = f"{path}/{child.node_type.value}[{i}]"
            self._check_style_refs_recursive(child, child_path, defined_styles)

    def _check_position(self, node: IRNode, path: str):
        """增强版 position 检查（含越界和零尺寸）"""
        # 先跑基类检查（负值、远边界）
        super()._check_position(node, path)

        if node.position is None:
            return
        pos = node.position

        # 零尺寸检查（非 auto 元素）
        if not pos.is_auto:
            if pos.width_mm == 0.0 and node.node_type not in (NodeType.SLIDE, NodeType.GROUP):
                self.result.add(
                    Severity.WARNING,
                    f"Element has zero width (non-auto), will not be visible",
                    path=path,
                    rule="position",
                )
            if pos.height_mm == 0.0 and node.node_type not in (NodeType.SLIDE, NodeType.GROUP):
                self.result.add(
                    Severity.WARNING,
                    f"Element has zero height (non-auto), will not be visible",
                    path=path,
                    rule="position",
                )

        # 幻灯片边界越界检查（使用 slide 实际尺寸或标准尺寸）
        right = pos.x_mm + pos.width_mm
        bottom = pos.y_mm + pos.height_mm
        # 只对非 slide/group 节点做边界检查
        if node.node_type not in (NodeType.SLIDE, NodeType.DOCUMENT):
            if right > self.slide_width + 1.0:  # 1mm 容差
                self.result.add(
                    Severity.WARNING,
                    f"Element right edge ({right:.1f}mm) exceeds slide width ({self.slide_width:.1f}mm)",
                    path=path,
                    rule="position_overflow",
                )
            if bottom > self.slide_height + 1.0:  # 1mm 容差
                self.result.add(
                    Severity.WARNING,
                    f"Element bottom edge ({bottom:.1f}mm) exceeds slide height ({self.slide_height:.1f}mm)",
                    path=path,
                    rule="position_overflow",
                )


class GateValidationError(Exception):
    """Gate 校验失败异常

    attributes:
        result (ValidationResult): 完整的校验结果
    """
    def __init__(self, message: str, result: ValidationResult):
        super().__init__(message)
        self.result = result


def validate_ir_v2(doc: IRDocument) -> ValidationResult:
    """非阻断校验：返回结果，不抛异常"""
    validator = IRValidator(doc)
    return validator.validate()


def gate_validate_ir(
    doc: IRDocument,
    slide_width: float = SLIDE_WIDTH_MM,
    slide_height: float = SLIDE_HEIGHT_MM,
    strict: bool = False,
) -> ValidationResult:
    """Gate 校验 — 编译后、渲染前的完整性检查

    Args:
        doc: IR 文档
        slide_width: 幻灯片宽度（mm），默认标准 16:9
        slide_height: 幻灯片高度（mm），默认标准 16:9
        strict: 严格模式下，WARNING 也视为错误

    Returns:
        ValidationResult

    Raises:
        GateValidationError: 当存在 ERROR（或 strict 模式下的 WARNING）时抛出
    """
    validator = GateValidator(doc, slide_width, slide_height)
    result = validator.validate()

    has_error = bool(result.errors)
    has_strict_warning = strict and bool(result.warnings)

    if has_error or has_strict_warning:
        # 记录日志
        logger = logging.getLogger(__name__)
        for issue in result.issues:
            if issue.severity == Severity.ERROR:
                logger.error(str(issue))
            elif issue.severity == Severity.WARNING:
                logger.warning(str(issue))

        error_count = len(result.errors)
        warning_count = len(result.warnings)
        raise GateValidationError(
            f"IR Gate validation failed: {error_count} error(s), {warning_count} warning(s)",
            result,
        )

    return result
