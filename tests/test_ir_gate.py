"""IR Gate 校验 + dump-ir 序列化测试"""

import json
import pytest

from office_suite.ir.types import (
    IRDocument, IRNode, IRPosition, IRStyle, NodeType,
    dump_ir_json,
)
from office_suite.ir.validator import (
    validate_ir_v2, gate_validate_ir,
    GateValidator, GateValidationError, Severity,
)


# ── 辅助工厂 ──────────────────────────────────────────────────


def _slide(children=None, position=None):
    return IRNode(
        node_type=NodeType.SLIDE,
        extra={"layout": "title"},
        children=children if children is not None else [],
        position=position,
    )


def _text(content="hello", position=None, style_ref=None):
    return IRNode(
        node_type=NodeType.TEXT,
        content=content,
        position=position or IRPosition(x_mm=10, y_mm=10, width_mm=50, height_mm=20),
        style_ref=style_ref,
    )


def _doc(slides=None, styles=None):
    return IRDocument(
        children=slides if slides is not None else [_slide([_text()])],
        styles=styles if styles is not None else {},
    )


# ── to_dict / dump_ir_json ──────────────────────────────────────


class TestDumpIR:
    def test_basic_roundtrip(self):
        doc = _doc()
        d = doc.to_dict()
        assert d["version"] == "4.0"
        assert d["children"][0]["node_type"] == "slide"
        assert d["children"][0]["children"][0]["content"] == "hello"

    def test_enum_serialization(self):
        doc = _doc()
        d = doc.to_dict()
        # NodeType 应序列化为字符串值，不是枚举对象
        assert d["children"][0]["node_type"] == "slide"
        assert isinstance(d["children"][0]["node_type"], str)

    def test_position_serialization(self):
        doc = _doc([_slide([_text(position=IRPosition(x_mm=10.5, y_mm=20.3, width_mm=100, height_mm=50))])])
        json_str = dump_ir_json(doc, pretty=False)
        parsed = json.loads(json_str)
        pos = parsed["children"][0]["children"][0]["position"]
        assert pos["x_mm"] == 10.5
        assert pos["width_mm"] == 100

    def test_style_serialization(self):
        style = IRStyle(font_size=24, font_color="#333", fill_gradient={"angle": 90})
        doc = _doc(styles={"title": style})
        json_str = dump_ir_json(doc)
        parsed = json.loads(json_str)
        assert parsed["styles"]["title"]["font_size"] == 24
        assert parsed["styles"]["title"]["fill_gradient"]["angle"] == 90

    def test_json_valid(self):
        """确保 dump_ir_json 输出的是合法 JSON"""
        doc = _doc()
        json_str = dump_ir_json(doc)
        parsed = json.loads(json_str)
        assert parsed["doc_type"] == "presentation"

    def test_pretty_output(self):
        doc = _doc()
        pretty = dump_ir_json(doc, pretty=True)
        compact = dump_ir_json(doc, pretty=False)
        assert len(pretty) > len(compact)  # 缩进会增加长度
        assert "\n" in pretty


# ── validate_ir_v2（非阻断） ────────────────────────────────────


class TestValidateV2:
    def test_valid_doc(self):
        result = validate_ir_v2(_doc())
        assert result.is_valid

    def test_empty_doc_warning(self):
        doc = _doc(slides=[])
        result = validate_ir_v2(doc)
        assert any("no slides" in w.message.lower() or "no sections" in w.message.lower()
                    for w in result.warnings)


# ── GateValidator 增强检查 ──────────────────────────────────────


class TestGateStyleRef:
    def test_valid_style_ref(self):
        styles = {"title": IRStyle(font_size=32)}
        slide = _slide([_text(style_ref="title")])
        doc = _doc([slide], styles=styles)
        result = gate_validate_ir(doc)
        assert result.is_valid

    def test_dangling_style_ref(self):
        slide = _slide([_text(style_ref="nonexistent")])
        doc = _doc([slide])
        with pytest.raises(GateValidationError) as exc_info:
            gate_validate_ir(doc)
        result = exc_info.value.result
        assert any(i.rule == "style_ref_dangling" for i in result.errors)

    def test_no_style_ref_passes(self):
        """无 style_ref 的节点不应报 style_ref_dangling"""
        slide = _slide([_text()])
        doc = _doc([slide])
        result = gate_validate_ir(doc)
        assert not any(i.rule == "style_ref_dangling" for i in result.issues)


class TestGatePosition:
    def test_overflow_right(self):
        """元素超出幻灯片右边界 → WARNING"""
        # 幻灯片宽 254mm，元素右边界 260mm → 超出
        slide = _slide([_text(position=IRPosition(x_mm=210, y_mm=10, width_mm=50, height_mm=20))])
        doc = _doc([slide])
        with pytest.raises(GateValidationError):
            gate_validate_ir(doc, strict=True)  # strict 下 WARNING 也报错

        # 非 strict 模式下只报警告不抛异常
        result = gate_validate_ir(doc, strict=False)
        assert any(i.rule == "position_overflow" for i in result.warnings)

    def test_overflow_bottom(self):
        """元素超出幻灯片底边界 → WARNING"""
        slide = _slide([_text(position=IRPosition(x_mm=10, y_mm=130, width_mm=50, height_mm=20))])
        doc = _doc([slide])
        with pytest.raises(GateValidationError):
            gate_validate_ir(doc, strict=True)

    def test_zero_width_warning(self):
        """非 auto 元素 width=0 → WARNING"""
        slide = _slide([_text(position=IRPosition(x_mm=10, y_mm=10, width_mm=0, height_mm=20))])
        doc = _doc([slide])
        with pytest.raises(GateValidationError):
            gate_validate_ir(doc, strict=True)

    def test_auto_element_no_zero_warning(self):
        """auto 元素 width=0 不应报零尺寸警告"""
        slide = _slide([_text(position=IRPosition(x_mm=0, y_mm=0, width_mm=0, height_mm=0, is_auto=True))])
        doc = _doc([slide])
        result = gate_validate_ir(doc, strict=False)
        assert not any("zero width" in i.message.lower() for i in result.issues)
        assert not any("zero height" in i.message.lower() for i in result.issues)

    def test_negative_position_error(self):
        """负 width → ERROR"""
        slide = _slide([_text(position=IRPosition(x_mm=10, y_mm=10, width_mm=-5, height_mm=20))])
        doc = _doc([slide])
        with pytest.raises(GateValidationError) as exc_info:
            gate_validate_ir(doc)
        assert any("negative" in e.message.lower() for e in exc_info.value.result.errors)


class TestGateStrict:
    def test_strict_promotes_warnings(self):
        """strict 模式下 WARNING 也阻止渲染"""
        slide = _slide([_text(position=IRPosition(x_mm=210, y_mm=10, width_mm=50, height_mm=20))])
        doc = _doc([slide])
        with pytest.raises(GateValidationError):
            gate_validate_ir(doc, strict=True)

    def test_non_strict_passes_warnings(self):
        """非 strict 模式下 WARNING 不阻止渲染"""
        slide = _slide([_text(position=IRPosition(x_mm=210, y_mm=10, width_mm=50, height_mm=20))])
        doc = _doc([slide])
        result = gate_validate_ir(doc, strict=False)
        assert result.is_valid  # 只有 warnings，无 errors


class TestGateContaiment:
    def test_invalid_nesting(self):
        """TEXT 不可包含 SLIDE"""
        inner = IRNode(node_type=NodeType.SLIDE, extra={"layout": "title"})
        outer = IRNode(node_type=NodeType.TEXT, content="bad", children=[inner],
                        position=IRPosition(x_mm=10, y_mm=10, width_mm=50, height_mm=20))
        doc = _doc([_slide([outer])])
        with pytest.raises(GateValidationError) as exc_info:
            gate_validate_ir(doc)
        assert any("cannot contain" in e.message.lower() for e in exc_info.value.result.errors)


class TestGateMultipleIssues:
    def test_multiple_errors_reported(self):
        """一次运行应报告所有错误，不只第一个"""
        t1 = _text(style_ref="missing_a",
                    position=IRPosition(x_mm=10, y_mm=10, width_mm=-5, height_mm=20))
        t2 = _text(style_ref="missing_b",
                    position=IRPosition(x_mm=10, y_mm=10, width_mm=50, height_mm=20))
        doc = _doc([_slide([t1, t2])])
        with pytest.raises(GateValidationError) as exc_info:
            gate_validate_ir(doc)
        errors = exc_info.value.result.errors
        rules = {e.rule for e in errors}
        assert "style_ref_dangling" in rules
        assert "position" in rules
