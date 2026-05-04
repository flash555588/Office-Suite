"""dsl/validator.py — 校验规则全覆盖测试"""

from office_suite.dsl.validator import validate_dsl, Severity


# ============================================================
# 文档结构校验
# ============================================================

def test_valid_document_passes():
    doc = {"version": "4.0", "type": "presentation", "slides": []}
    result = validate_dsl(doc)
    assert result.is_valid
    assert result.errors == []


def test_missing_version():
    doc = {"type": "presentation", "slides": []}
    result = validate_dsl(doc)
    assert not result.is_valid
    assert any("version" in i.message for i in result.errors)


def test_missing_type():
    doc = {"version": "4.0", "slides": []}
    result = validate_dsl(doc)
    assert not result.is_valid
    assert any("type" in i.message for i in result.errors)


def test_invalid_doc_type():
    doc = {"version": "4.0", "type": "foobar", "slides": []}
    result = validate_dsl(doc)
    assert not result.is_valid
    assert any("foobar" in i.message for i in result.errors)


def test_valid_doc_types():
    for t in ("presentation", "document", "spreadsheet"):
        doc = {"version": "4.0", "type": t, "slides": []}
        result = validate_dsl(doc)
        assert result.is_valid, f"type '{t}' should be valid"


def test_root_not_dict():
    result = validate_dsl("not a dict")
    assert not result.is_valid
    assert any("字典" in i.message for i in result.errors)


# ============================================================
# slides 结构
# ============================================================

def test_slides_not_list():
    doc = {"version": "4.0", "type": "presentation", "slides": "oops"}
    result = validate_dsl(doc)
    assert any("slides 必须是列表" in i.message for i in result.errors)


def test_no_slides_warns():
    doc = {"version": "4.0", "type": "presentation"}
    result = validate_dsl(doc)
    assert any(i.severity == Severity.WARNING for i in result.issues)


def test_pages_field_accepted():
    """pages 字段应替代 slides，不产生警告"""
    doc = {"version": "4.0", "type": "presentation", "pages": []}
    result = validate_dsl(doc)
    slide_warnings = [i for i in result.issues if "slides" in i.message.lower()]
    assert len(slide_warnings) == 0


def test_slide_not_dict():
    doc = {"version": "4.0", "type": "presentation", "slides": ["oops"]}
    result = validate_dsl(doc)
    assert any("slide 必须是字典" in i.message for i in result.errors)


def test_slide_missing_layout_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [{}]}
    result = validate_dsl(doc)
    assert any("layout" in i.message for i in result.issues)


# ============================================================
# 元素类型
# ============================================================

def test_element_missing_type():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"content": "hello"}]}
    ]}
    result = validate_dsl(doc)
    assert any("type" in i.message for i in result.errors)


def test_unknown_element_type_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"type": "foobar"}]}
    ]}
    result = validate_dsl(doc)
    assert any("foobar" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


def test_valid_element_types():
    for t in ("text", "image", "shape", "table", "chart", "group",
              "semantic_icon", "component"):
        doc = {"version": "4.0", "type": "presentation", "slides": [
            {"layout": "blank", "elements": [{"type": t}]}
        ]}
        result = validate_dsl(doc)
        type_warnings = [i for i in result.issues
                         if "元素类型" in i.message and t in i.message]
        # 不应产生"未知元素类型"警告
        assert len(type_warnings) == 0, f"'{t}' flagged as unknown"


# ============================================================
# text 元素
# ============================================================

def test_text_requires_content():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"type": "text"}]}
    ]}
    result = validate_dsl(doc)
    assert any("content" in i.message for i in result.errors)


def test_text_unknown_format_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "text", "content": "hi", "format": "binary"}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("binary" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


def test_text_valid_formats():
    for fmt in ("plain", "markdown", "latex", "rich"):
        doc = {"version": "4.0", "type": "presentation", "slides": [
            {"layout": "blank", "elements": [
                {"type": "text", "content": "hi", "format": fmt}
            ]}
        ]}
        result = validate_dsl(doc)
        fmt_warnings = [i for i in result.issues
                        if "文本格式" in i.message and fmt in i.message]
        assert len(fmt_warnings) == 0, f"format '{fmt}' flagged as unknown"


# ============================================================
# image 元素
# ============================================================

def test_image_requires_source():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"type": "image"}]}
    ]}
    result = validate_dsl(doc)
    assert any("source" in i.message for i in result.errors)


# ============================================================
# shape 元素
# ============================================================

def test_unknown_shape_type_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "shape", "shape_type": "dodecahedron"}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("dodecahedron" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


# ============================================================
# chart 元素
# ============================================================

def test_chart_requires_chart_type():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"type": "chart"}]}
    ]}
    result = validate_dsl(doc)
    assert any("chart_type" in i.message for i in result.errors)


def test_unknown_chart_type_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "chart", "chart_type": "waterfall"}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("waterfall" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


def test_unknown_chart_engine_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "chart", "chart_type": "bar", "extra": {"engine": "d3"}}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("d3" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


# ============================================================
# semantic_icon 元素
# ============================================================

def test_semantic_icon_requires_primitives():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [{"type": "semantic_icon"}]}
    ]}
    result = validate_dsl(doc)
    assert any("primitives" in i.message for i in result.errors)


def test_semantic_icon_empty_primitives():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "semantic_icon", "primitives": []}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("primitives" in i.message for i in result.errors)


def test_semantic_icon_invalid_primitive_type():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "semantic_icon", "primitives": ["not_a_dict"]}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("dictionary" in i.message for i in result.errors)


def test_semantic_icon_unknown_primitive_shape():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "semantic_icon", "primitives": [
                {"type": "shape", "shape": "dodecahedron"}
            ]}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("dodecahedron" in i.message for i in result.errors)


# ============================================================
# position 校验
# ============================================================

def test_unknown_position_key_info():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "text", "content": "hi", "position": {"x": 0, "z": 99}}
        ]}
    ]}
    result = validate_dsl(doc)
    infos = [i for i in result.issues if "z" in i.message
             and i.severity == Severity.INFO]
    assert len(infos) >= 1


# ============================================================
# 样式校验
# ============================================================

def test_unknown_font_key_info():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "text", "content": "hi", "style": {
                "font": {"family": "Arial", "stretch": "condensed"}
            }}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("stretch" in i.message for i in result.issues
               if i.severity == Severity.INFO)


def test_unknown_fill_key_info():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "text", "content": "hi", "style": {
                "fill": {"pattern": "dots"}
            }}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("pattern" in i.message for i in result.issues
               if i.severity == Severity.INFO)


def test_unknown_shadow_key_info():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "text", "content": "hi", "style": {
                "shadow": {"angle": 45}
            }}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("angle" in i.message for i in result.issues
               if i.severity == Severity.INFO)


# ============================================================
# 全局 styles
# ============================================================

def test_global_style_must_be_dict():
    doc = {"version": "4.0", "type": "presentation", "slides": [],
           "styles": {"h1": "not a dict"}}
    result = validate_dsl(doc)
    assert any("h1" in i.message and "字典" in i.message for i in result.errors)


def test_global_style_valid():
    doc = {"version": "4.0", "type": "presentation", "slides": [],
           "styles": {"h1": {"font": {"size": 24}}}}
    result = validate_dsl(doc)
    style_errors = [i for i in result.errors if "h1" in i.message]
    assert len(style_errors) == 0


# ============================================================
# 数据绑定
# ============================================================

def test_data_binding_must_be_dict():
    doc = {"version": "4.0", "type": "presentation", "slides": [],
           "data": {"sales": "not a dict"}}
    result = validate_dsl(doc)
    assert any("sales" in i.message and "字典" in i.message for i in result.errors)


def test_data_binding_missing_source_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [],
           "data": {"sales": {"type": "csv"}}}
    result = validate_dsl(doc)
    assert any("sales" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


def test_data_binding_with_source_passes():
    doc = {"version": "4.0", "type": "presentation", "slides": [],
           "data": {"sales": {"source": "data.csv"}}}
    result = validate_dsl(doc)
    data_warnings = [i for i in result.issues
                     if "sales" in i.message and i.severity == Severity.WARNING]
    assert len(data_warnings) == 0


# ============================================================
# 布局配置
# ============================================================

def test_unknown_layout_mode_warns():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "layout_mode": "mosaic"}
    ]}
    result = validate_dsl(doc)
    assert any("mosaic" in i.message for i in result.issues
               if i.severity == Severity.WARNING)


def test_grid_not_dict():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "grid": "oops"}
    ]}
    result = validate_dsl(doc)
    assert any("grid" in i.message and "字典" in i.message for i in result.errors)


def test_grid_columns_not_int():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "grid": {"columns": "three"}}
    ]}
    result = validate_dsl(doc)
    assert any("columns" in i.message for i in result.errors)


def test_constraints_not_list():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "constraints": "oops"}
    ]}
    result = validate_dsl(doc)
    assert any("constraints" in i.message and "列表" in i.message
               for i in result.errors)


# ============================================================
# group 递归检查
# ============================================================

def test_group_children_checked():
    doc = {"version": "4.0", "type": "presentation", "slides": [
        {"layout": "blank", "elements": [
            {"type": "group", "elements": [
                {"type": "text"}  # 缺少 content
            ]}
        ]}
    ]}
    result = validate_dsl(doc)
    assert any("content" in i.message for i in result.errors)


# ============================================================
# validate_dsl_string
# ============================================================

def test_validate_dsl_string_valid():
    from office_suite.dsl.validator import validate_dsl_string
    yaml_str = 'version: "4.0"\ntype: presentation\nslides: []\n'
    result = validate_dsl_string(yaml_str)
    assert result.is_valid


def test_validate_dsl_string_invalid_yaml():
    from office_suite.dsl.validator import validate_dsl_string
    yaml_str = 'version: [invalid yaml'
    result = validate_dsl_string(yaml_str)
    assert not result.is_valid
    assert any("YAML" in i.message for i in result.errors)
