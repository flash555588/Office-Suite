"""DSL 层约束校验 — 在编译为 IR 之前验证 DSL 文档的合法性

校验规则：
  1. 文档结构校验（必填字段、类型匹配）
  2. 元素类型合法性
  3. 位置坐标格式校验
  4. 样式属性合法性
  5. 资源引用格式校验
  6. 数据绑定引用校验

与 ir/validator.py 的区别：
  - 本文件：DSL 原始结构校验（语法级）
  - ir/validator.py：IR 节点语义校验（包含约束、布局冲突等）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DSLValidationIssue:
    severity: Severity
    message: str
    path: str = ""           # 出错的 DSL 路径，如 slides[0].elements[2]
    rule: str = ""           # 规则名称


@dataclass
class DSLValidationResult:
    issues: list[DSLValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def errors(self) -> list[DSLValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[DSLValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def summary(self) -> str:
        lines = []
        for i in self.issues:
            prefix = {"error": "E", "warning": "W", "info": "I"}[i.severity.value]
            path = f" @ {i.path}" if i.path else ""
            lines.append(f"[{prefix}] {i.message}{path}")
        return "\n".join(lines) if lines else "Validation passed."


# ============================================================
# 校验规则
# ============================================================

VALID_DOC_TYPES = {"presentation", "document", "spreadsheet"}
VALID_ELEMENT_TYPES = {
    "text", "image", "shape", "table", "chart", "group",
    "semantic_icon", "component", "video", "audio", "code", "diagram",
    "3d_model", "model_3d", "map",
}
VALID_SHAPE_TYPES = {
    "rectangle", "rounded_rectangle", "ellipse", "circle",
    "triangle", "diamond", "arrow", "line", "star",
}
VALID_SEMANTIC_ICON_PRIMITIVES = {
    "rectangle", "rounded_rectangle", "round_rect", "rect",
    "ellipse", "circle", "triangle", "line",
}
VALID_CHART_TYPES = {
    # 原生 PPTX 图表
    "bar", "column", "line", "pie", "area", "scatter",
    "doughnut", "radar", "bubble",
    "bar_stacked", "column_stacked", "line_marked",
    # 外部引擎图表 (matplotlib/plotly/ggplot2/pgfplots/vega-lite)
    "heatmap", "box", "violin", "histogram", "density",
    "funnel", "sunburst", "treemap",
}
VALID_TEXT_FORMATS = {"plain", "markdown", "latex", "rich"}
VALID_CHART_ENGINES = {"native", "matplotlib", "plotly", "vega-lite", "ggplot2", "pgfplots"}
VALID_LAYOUT_MODES = {
    "absolute", "relative", "grid", "flex", "constraint",
    # 语义布局预设（由 semantic_layouts.py 解析为具体配置）
    "cover_center", "title_body", "card_grid_2x2", "card_grid_3x2",
    "card_row_4", "split_50_50", "timeline_h6", "three_column",
    "hero_card_left", "panel_with_grid", "quote", "stats_row",
}
VALID_POSITION_KEYS = {"x", "y", "width", "height", "bottom", "center"}
VALID_FONT_KEYS = {"family", "size", "weight", "color", "italic", "underline"}
VALID_FILL_KEYS = {"color", "gradient", "image", "opacity"}
VALID_GRADIENT_KEYS = {"type", "angle", "stops", "center"}
VALID_SHADOW_KEYS = {"blur", "offset", "color", "spread"}
VALID_LENGTH_PATTERN = r"^-?\d+(\.\d+)?(mm|cm|in|pt|px|%)?$"


def _check_required_fields(doc: dict, path: str, result: DSLValidationResult):
    """检查文档级必填字段"""
    if "version" not in doc:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "缺少 version 字段", path, "required_fields"))
    if "type" not in doc:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "缺少 type 字段", path, "required_fields"))
    elif doc["type"] not in VALID_DOC_TYPES:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR,
            f"无效的文档类型 '{doc['type']}'，合法值: {VALID_DOC_TYPES}",
            f"{path}.type", "doc_type"))


def _check_slides(doc: dict, path: str, result: DSLValidationResult):
    """检查 slides 结构"""
    slides = doc.get("slides")
    if slides is None:
        pages = doc.get("pages")
        if isinstance(pages, list):
            return
        result.issues.append(DSLValidationIssue(
            Severity.WARNING, "文档没有 slides 字段", path, "slides"))
        return
    if not isinstance(slides, list):
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "slides 必须是列表", f"{path}.slides", "slides_type"))
        return
    for i, slide in enumerate(slides):
        sp = f"{path}.slides[{i}]"
        if not isinstance(slide, dict):
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "slide 必须是字典", sp, "slide_type"))
            continue
        if "layout" not in slide:
            result.issues.append(DSLValidationIssue(
                Severity.WARNING, "slide 缺少 layout 字段", sp, "slide_layout"))
        _check_slide_layout(slide, sp, result)
        _check_elements(slide.get("elements", []), sp, result)


def _check_slide_layout(slide: dict, path: str, result: DSLValidationResult):
    """检查幻灯片级布局配置"""
    layout_mode = slide.get("layout_mode", "")
    if layout_mode and layout_mode not in VALID_LAYOUT_MODES:
        result.issues.append(DSLValidationIssue(
            Severity.WARNING,
            f"未知布局模式 '{layout_mode}'，合法值: {sorted(VALID_LAYOUT_MODES)}",
            f"{path}.layout_mode", "layout_mode_unknown"))

    grid = slide.get("grid")
    if grid is not None:
        if not isinstance(grid, dict):
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "grid 必须是字典", f"{path}.grid", "grid_type"))
        elif "columns" in grid and not isinstance(grid["columns"], int):
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "grid.columns 必须是整数",
                f"{path}.grid.columns", "grid_columns_type"))

    flex = slide.get("flex")
    if flex is not None and not isinstance(flex, dict):
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "flex 必须是字典", f"{path}.flex", "flex_type"))

    constraints = slide.get("constraints")
    if constraints is not None:
        if not isinstance(constraints, list):
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "constraints 必须是列表",
                f"{path}.constraints", "constraints_type"))
        else:
            for k, c in enumerate(constraints):
                if not isinstance(c, dict):
                    result.issues.append(DSLValidationIssue(
                        Severity.ERROR, "constraint 必须是字典",
                        f"{path}.constraints[{k}]", "constraint_type"))


def _check_elements(elements: list, path: str, result: DSLValidationResult):
    """检查元素列表"""
    if not isinstance(elements, list):
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "elements 必须是列表", f"{path}.elements", "elements_type"))
        return
    for j, elem in enumerate(elements):
        ep = f"{path}.elements[{j}]"
        if not isinstance(elem, dict):
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "element 必须是字典", ep, "element_type"))
            continue
        _check_element(elem, ep, result)


def _check_element(elem: dict, path: str, result: DSLValidationResult):
    """检查单个元素"""
    etype = elem.get("type")
    if etype is None:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "元素缺少 type 字段", path, "element_type_required"))
        return
    if etype not in VALID_ELEMENT_TYPES:
        result.issues.append(DSLValidationIssue(
            Severity.WARNING,
            f"未知元素类型 '{etype}'，可能不被所有渲染器支持",
            f"{path}.type", "element_type_unknown"))

    # 文本元素必须有 content
    if etype == "text" and "content" not in elem:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "text 元素必须有 content 字段",
            path, "text_content_required"))

    # 文本 format 字段校验
    if etype == "text":
        fmt = elem.get("format", "plain")
        if fmt and fmt not in VALID_TEXT_FORMATS:
            result.issues.append(DSLValidationIssue(
                Severity.WARNING,
                f"未知文本格式 '{fmt}'，合法值: {sorted(VALID_TEXT_FORMATS)}",
                f"{path}.format", "text_format_unknown"))

    # 图片元素必须有 source
    if etype == "image" and "source" not in elem:
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "image 元素必须有 source 字段",
            path, "image_source_required"))

    # shape 子类型
    if etype == "semantic_icon":
        primitives = elem.get("primitives")
        if not isinstance(primitives, list) or not primitives:
            result.issues.append(DSLValidationIssue(
                Severity.ERROR,
                "semantic_icon must include AI-authored primitives; preset icon names are not allowed",
                path,
                "semantic_icon_primitives_required",
            ))
        else:
            for k, primitive in enumerate(primitives):
                pp = f"{path}.primitives[{k}]"
                if not isinstance(primitive, dict):
                    result.issues.append(DSLValidationIssue(
                        Severity.ERROR,
                        "semantic_icon primitive must be a dictionary",
                        pp,
                        "semantic_icon_primitive_type",
                    ))
                    continue
                primitive_type = str(primitive.get("type", "shape")).lower()
                shape_name = str(primitive.get("shape", primitive_type)).lower()
                if shape_name not in VALID_SEMANTIC_ICON_PRIMITIVES:
                    result.issues.append(DSLValidationIssue(
                        Severity.ERROR,
                        f"unsupported semantic_icon primitive '{shape_name}'",
                        pp,
                        "semantic_icon_primitive_unknown",
                    ))

    if etype == "shape":
        st = elem.get("shape_type")
        if st and st not in VALID_SHAPE_TYPES:
            result.issues.append(DSLValidationIssue(
                Severity.WARNING,
                f"未知形状类型 '{st}'",
                f"{path}.shape_type", "shape_type_unknown"))

    # chart 子类型
    if etype == "chart":
        ct = elem.get("chart_type")
        if not ct:
            result.issues.append(DSLValidationIssue(
                Severity.ERROR, "chart 元素必须有 chart_type 字段",
                path, "chart_type_required"))
        elif ct not in VALID_CHART_TYPES:
            result.issues.append(DSLValidationIssue(
                Severity.WARNING,
                f"未知图表类型 '{ct}'",
                f"{path}.chart_type", "chart_type_unknown"))
        # chart engine 校验
        engine = (elem.get("extra") or {}).get("engine")
        if engine and engine not in VALID_CHART_ENGINES:
            result.issues.append(DSLValidationIssue(
                Severity.WARNING,
                f"未知图表引擎 '{engine}'，合法值: {sorted(VALID_CHART_ENGINES)}",
                f"{path}.extra.engine", "chart_engine_unknown"))

    # 位置校验
    pos = elem.get("position")
    if pos and isinstance(pos, dict):
        _check_position(pos, f"{path}.position", result)

    # 样式校验
    style = elem.get("style")
    if style and isinstance(style, dict):
        _check_inline_style(style, f"{path}.style", result)

    # 递归检查 group 子元素
    if etype == "group" and "elements" in elem:
        _check_elements(elem["elements"], path, result)


def _check_position(pos: dict, path: str, result: DSLValidationResult):
    """检查位置属性"""
    for key in pos:
        if key not in VALID_POSITION_KEYS:
            result.issues.append(DSLValidationIssue(
                Severity.INFO,
                f"未知位置属性 '{key}'",
                f"{path}.{key}", "position_unknown_key"))


def _check_inline_style(style: dict, path: str, result: DSLValidationResult):
    """检查内联样式"""
    if "font" in style and isinstance(style["font"], dict):
        for key in style["font"]:
            if key not in VALID_FONT_KEYS:
                result.issues.append(DSLValidationIssue(
                    Severity.INFO,
                    f"未知字体属性 '{key}'",
                    f"{path}.font.{key}", "font_unknown_key"))
    if "fill" in style and isinstance(style["fill"], dict):
        for key in style["fill"]:
            if key not in VALID_FILL_KEYS:
                result.issues.append(DSLValidationIssue(
                    Severity.INFO,
                    f"未知填充属性 '{key}'",
                    f"{path}.fill.{key}", "fill_unknown_key"))
    if "gradient" in style and isinstance(style["gradient"], dict):
        for key in style["gradient"]:
            if key not in VALID_GRADIENT_KEYS:
                result.issues.append(DSLValidationIssue(
                    Severity.INFO,
                    f"未知渐变属性 '{key}'",
                    f"{path}.gradient.{key}", "gradient_unknown_key"))
    if "shadow" in style and isinstance(style["shadow"], dict):
        for key in style["shadow"]:
            if key not in VALID_SHADOW_KEYS:
                result.issues.append(DSLValidationIssue(
                    Severity.INFO,
                    f"未知阴影属性 '{key}'",
                    f"{path}.shadow.{key}", "shadow_unknown_key"))


def _check_styles(doc: dict, path: str, result: DSLValidationResult):
    """检查全局样式定义"""
    styles = doc.get("styles")
    if styles and isinstance(styles, dict):
        for name, style in styles.items():
            if not isinstance(style, dict):
                result.issues.append(DSLValidationIssue(
                    Severity.ERROR,
                    f"样式 '{name}' 必须是字典",
                    f"{path}.styles.{name}", "style_type"))
            else:
                _check_inline_style(style, f"{path}.styles.{name}", result)


def _check_data(doc: dict, path: str, result: DSLValidationResult):
    """检查数据绑定"""
    data = doc.get("data")
    if data and isinstance(data, dict):
        for name, binding in data.items():
            if not isinstance(binding, dict):
                result.issues.append(DSLValidationIssue(
                    Severity.ERROR,
                    f"数据绑定 '{name}' 必须是字典",
                    f"{path}.data.{name}", "data_type"))
                continue
            if "source" not in binding and "formula" not in binding:
                result.issues.append(DSLValidationIssue(
                    Severity.WARNING,
                    f"数据绑定 '{name}' 缺少 source 或 formula",
                    f"{path}.data.{name}", "data_source"))


# ============================================================
# 入口
# ============================================================

def validate_dsl(doc: dict) -> DSLValidationResult:
    """校验 DSL 文档

    Args:
        doc: 解析后的 DSL 字典

    Returns:
        DSLValidationResult，包含所有校验问题
    """
    result = DSLValidationResult()

    if not isinstance(doc, dict):
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, "文档必须是字典", "", "root_type"))
        return result

    _check_required_fields(doc, "root", result)
    _check_slides(doc, "root", result)
    _check_styles(doc, "root", result)
    _check_data(doc, "root", result)

    return result


def validate_dsl_string(yaml_str: str) -> DSLValidationResult:
    """从 YAML 字符串校验 DSL 文档"""
    from .parser import safe_yaml_load
    try:
        doc = safe_yaml_load(yaml_str)
    except yaml.YAMLError as e:
        result = DSLValidationResult()
        result.issues.append(DSLValidationIssue(
            Severity.ERROR, f"YAML 解析错误: {e}", "", "yaml_parse"))
        return result
    return validate_dsl(doc)
