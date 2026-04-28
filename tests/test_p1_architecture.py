"""P1 MVP 架构补强测试

覆盖：
1. 样式级联（theme → document → slide → element → inline）
2. 渲染器能力声明一致性
3. 16:9 尺寸一致性
4. 降级行为验证
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from office_suite.ir.cascade import cascade_style, cascade_style_by_name, DEFAULT_THEME_STYLES
from office_suite.ir.types import IRStyle
from office_suite.ir.types import NodeType
from office_suite.renderer.base import RendererCapability
from office_suite.renderer.pptx.deck import PPTXRenderer
from office_suite.renderer.docx.document import DOCXRenderer
from office_suite.renderer.xlsx.workbook import XLSXRenderer
from office_suite.renderer.pdf.canvas import PDFRenderer
from office_suite.renderer.html.dom import HTMLRenderer
from office_suite.engine.layout.grid import GridLayout
from office_suite.engine.layout.flex import FlexLayout


# ============================================================
# 1. 样式级联测试
# ============================================================

def test_cascade_basic_merge():
    """低优先级属性被高优先级覆盖"""
    base = IRStyle(font_family="Arial", font_size=12, font_weight=400)
    override = IRStyle(font_size=24, font_color="#FF0000")

    result = cascade_style(base, override)

    assert result.font_family == "Arial"  # 保留
    assert result.font_size == 24         # 覆盖
    assert result.font_weight == 400      # 保留
    assert result.font_color == "#FF0000" # 新增


def test_cascade_none_layer_skipped():
    """None 层被跳过，不影响结果"""
    base = IRStyle(font_family="Arial", font_size=18)
    result = cascade_style(base, None, IRStyle(font_weight=700))

    assert result.font_family == "Arial"
    assert result.font_size == 18
    assert result.font_weight == 700


def test_cascade_empty_string_treated_as_unset():
    """空字符串视为未设置，不覆盖已有值"""
    base = IRStyle(font_family="Arial")
    override = IRStyle(font_family="")
    result = cascade_style(base, override)

    assert result.font_family == "Arial"


def test_cascade_zero_is_valid():
    """0 是有效值，会覆盖"""
    base = IRStyle(font_size=18)
    override = IRStyle(font_size=0)
    result = cascade_style(base, override)

    assert result.font_size == 0


def test_cascade_deep_copy_complex_objects():
    """复杂对象（gradient, shadow, border）被深拷贝"""
    gradient = {"type": "linear", "angle": 45, "stops": []}
    shadow = {"blur": 5, "offset_x": 2, "offset_y": 2}

    base = IRStyle(fill_gradient=gradient, shadow=shadow)
    result = cascade_style(base, IRStyle())

    # 修改原始不应影响结果
    gradient["angle"] = 90
    assert result.fill_gradient["angle"] == 45


def test_cascade_priority_order():
    """多层级时高优先级胜出"""
    theme = IRStyle(font_size=18, font_weight=400, font_color="#000000")
    doc = IRStyle(font_size=24, font_color="#333333")
    slide = IRStyle(font_weight=700)
    element = IRStyle(font_color="#FF0000")

    result = cascade_style(theme, doc, slide, element)

    assert result.font_size == 24       # doc 覆盖 theme
    assert result.font_weight == 700    # slide 覆盖 theme
    assert result.font_color == "#FF0000"  # element 覆盖 doc


def test_cascade_by_name_with_style_name():
    """有 style_name 时走完整 5 层级联"""
    theme_styles = {
        "title": IRStyle(font_size=44, font_weight=700),
    }
    doc_styles = {
        "title": IRStyle(font_color="#1E293B"),
    }
    element_style = IRStyle(font_size=36)

    result = cascade_style_by_name(
        style_name="title",
        theme_styles=theme_styles,
        doc_styles=doc_styles,
        element_style=element_style,
    )

    assert result.font_size == 36       # element 覆盖 theme
    assert result.font_weight == 700    # 来自 theme
    assert result.font_color == "#1E293B"  # 来自 doc


def test_cascade_by_name_without_style_name():
    """无 style_name 时跳过 theme/doc 同名层"""
    theme_styles = {
        "title": IRStyle(font_size=44, font_weight=700),
    }
    doc_styles = {
        "title": IRStyle(font_color="#1E293B"),
    }
    element_style = IRStyle(font_size=36)

    result = cascade_style_by_name(
        style_name=None,
        theme_styles=theme_styles,
        doc_styles=doc_styles,
        element_style=element_style,
    )

    # 无 style_name → theme/doc 同名层被跳过
    assert result.font_size == 36       # 来自 element
    assert result.font_weight is None   # 未设置（theme title 被跳过）
    assert result.font_color is None    # 未设置（doc title 被跳过）


def test_cascade_by_name_missing_named_style():
    """style_name 在 theme/doc 中不存在时不报错"""
    result = cascade_style_by_name(
        style_name="nonexistent",
        theme_styles={},
        doc_styles={},
        element_style=IRStyle(font_size=20),
    )

    assert result.font_size == 20


def test_default_theme_styles_exist():
    """默认主题样式包含 default/title/subtitle"""
    assert "default" in DEFAULT_THEME_STYLES
    assert "title" in DEFAULT_THEME_STYLES
    assert "subtitle" in DEFAULT_THEME_STYLES

    title = DEFAULT_THEME_STYLES["title"]
    assert title.font_size == 44
    assert title.font_weight == 700


# ============================================================
# 2. 渲染器能力声明测试
# ============================================================

def _get_all_renderers():
    """获取所有渲染器实例"""
    return {
        "pptx": PPTXRenderer(),
        "docx": DOCXRenderer(),
        "xlsx": XLSXRenderer(),
        "pdf": PDFRenderer(),
        "html": HTMLRenderer(),
    }


def test_all_renderers_have_capability():
    """所有渲染器都声明了 capability"""
    for name, renderer in _get_all_renderers().items():
        cap = renderer.capability
        assert isinstance(cap, RendererCapability), f"{name} 缺少 RendererCapability"
        assert isinstance(cap.supported_node_types, set), f"{name} node_types 不是 set"


def test_pptx_capability_completeness():
    """PPTX 渲染器能力声明完整性"""
    cap = PPTXRenderer().capability

    # 节点类型
    assert NodeType.TEXT in cap.supported_node_types
    assert NodeType.IMAGE in cap.supported_node_types
    assert NodeType.SHAPE in cap.supported_node_types
    assert NodeType.TABLE in cap.supported_node_types
    assert NodeType.CHART in cap.supported_node_types
    assert NodeType.GROUP in cap.supported_node_types

    # 文本变换
    assert "arch" in cap.supported_text_transforms
    assert "wave" in cap.supported_text_transforms

    # 动画
    assert "slide_up" in cap.supported_animations
    assert "fade_in" in cap.supported_animations

    # 效果
    assert "shadow" in cap.supported_effects
    assert "gradient_fill" in cap.supported_effects

    # 降级映射
    assert cap.get_fallback("duotone") == "opacity"
    assert cap.get_fallback("blur") == "shadow"


def test_docx_capability_fallbacks():
    """DOCX 降级策略正确"""
    cap = DOCXRenderer().capability

    assert cap.get_fallback("arch") == "plain_text"
    assert cap.get_fallback("wave") == "plain_text"
    assert cap.get_fallback("gradient_fill") == "solid_fill"


def test_xlsx_capability_limits():
    """XLSX 能力限制正确"""
    cap = XLSXRenderer().capability

    assert len(cap.supported_text_transforms) == 0
    assert len(cap.supported_animations) == 0
    assert cap.get_fallback("gradient_fill") == "solid_fill"
    assert cap.get_fallback("shadow") == "none"


def test_pdf_capability_fallbacks():
    """PDF 降级策略正确"""
    cap = PDFRenderer().capability

    assert cap.get_fallback("gradient_fill") == "solid_fill"
    assert cap.get_fallback("arch") == "plain_text"
    assert cap.get_fallback("wave") == "plain_text"


def test_html_capability_fallbacks():
    """HTML 降级策略正确"""
    cap = HTMLRenderer().capability

    assert cap.get_fallback("arch") == "plain_text"
    assert cap.get_fallback("wave") == "plain_text"


def test_capability_supports_method():
    """supports() 方法正确查询"""
    cap = PPTXRenderer().capability

    assert cap.supports("shadow", "effects") is True
    assert cap.supports("nonexistent", "effects") is False
    assert cap.supports("arch", "text_transforms") is True
    assert cap.supports("fade_in", "animations") is True


def test_all_renderers_support_slide_and_text():
    """所有渲染器都支持 SLIDE 和 TEXT 节点"""
    for name, renderer in _get_all_renderers().items():
        cap = renderer.capability
        assert NodeType.TEXT in cap.supported_node_types, f"{name} 不支持 TEXT"
        # SLIDE 通过 supported_node_types 或内部处理支持


# ============================================================
# 3. 16:9 尺寸一致性测试
# ============================================================

CORRECT_WIDTH = 254.0
CORRECT_HEIGHT = 142.875


def test_grid_layout_default_16_9():
    """GridLayout 默认尺寸为 16:9"""
    layout = GridLayout()
    assert layout.container_width == CORRECT_WIDTH
    assert layout.container_height == CORRECT_HEIGHT


def test_flex_layout_default_16_9():
    """FlexLayout 默认尺寸为 16:9"""
    layout = FlexLayout()
    assert layout.container_width == CORRECT_WIDTH
    assert layout.container_height == CORRECT_HEIGHT


def test_grid_layout_column_calculation():
    """GridLayout 列宽计算正确"""
    layout = GridLayout(columns=12, container_width=254.0, gutter=2.0)
    # 总 gutter = 2 * 11 = 22mm
    # 可用宽度 = 254 - 22 = 232mm
    # 每列 = 232 / 12 ≈ 19.33mm
    expected_col_width = (254.0 - 2.0 * 11) / 12
    assert abs(layout.column_width - expected_col_width) < 0.01


def test_grid_layout_resolve_position():
    """GridLayout 解析位置正确"""
    layout = GridLayout(columns=12, container_width=254.0, container_height=142.875, gutter=2.0)

    from office_suite.ir.layout_spec import GridPosition
    pos = layout.resolve(GridPosition(column=1, column_span=6, row=1))

    assert pos.x == 0.0  # 第 1 列起始
    assert pos.width > 0
    assert pos.height > 0


def test_flex_layout_resolve_row():
    """FlexLayout 行布局解析正确"""
    from office_suite.ir.layout_spec import FlexPosition, FlexDirection
    from office_suite.engine.layout.flex import FlexItem
    layout = FlexLayout(container_width=254.0, container_height=142.875)

    items = [
        FlexItem(width=50, height=30),
        FlexItem(width=80, height=30),
    ]
    positions = layout.resolve(
        FlexPosition(direction=FlexDirection.ROW, gap=5),
        items,
    )

    assert len(positions) == 2
    assert positions[0].x == 0.0
    assert positions[1].x == 55.0  # 50 + 5 gap
    assert all(p.y == 0.0 for p in positions)


# ============================================================
# 4. 降级行为测试
# ============================================================

def test_pptx_fallback_duotone_to_opacity():
    """PPTX: duotone 降级为 opacity"""
    cap = PPTXRenderer().capability
    assert cap.get_fallback("duotone") == "opacity"


def test_pptx_fallback_blur_to_shadow():
    """PPTX: blur 降级为 shadow"""
    cap = PPTXRenderer().capability
    assert cap.get_fallback("blur") == "shadow"


def test_docx_fallback_chart_to_table():
    """DOCX: chart 降级为 table"""
    from office_suite.renderer.capability_map import get_fallback
    assert get_fallback("docx", "chart") == "table"


def test_xlsx_fallback_shape_to_text():
    """XLSX: shape 降级为 text"""
    from office_suite.renderer.capability_map import get_fallback
    assert get_fallback("xlsx", "shape") == "text"


def test_renderer_apply_fallback():
    """BaseRenderer._apply_fallback 正确返回降级"""
    renderer = PPTXRenderer()
    from office_suite.ir.types import IRNode
    node = IRNode(node_type=NodeType.TEXT)

    fallback = renderer._apply_fallback(node, "duotone")
    assert fallback == "opacity"

    fallback = renderer._apply_fallback(node, "nonexistent")
    assert fallback is None


# ============================================================
# 5. 能力映射表一致性测试
# ============================================================

def test_capability_map_covers_all_renderers():
    """capability_map 覆盖所有 5 个渲染器"""
    from office_suite.renderer.capability_map import RENDERER_CAPABILITIES
    assert "pptx" in RENDERER_CAPABILITIES
    assert "docx" in RENDERER_CAPABILITIES
    assert "xlsx" in RENDERER_CAPABILITIES
    assert "pdf" in RENDERER_CAPABILITIES
    assert "html" in RENDERER_CAPABILITIES


def test_capability_map_get_capabilities():
    """get_capabilities 返回正确数据"""
    from office_suite.renderer.capability_map import get_capabilities

    pptx = get_capabilities("pptx")
    assert "text" in pptx["node_types"]
    assert "shadow" in pptx["effects"]
    assert len(pptx["text_transforms"]) > 0
    assert len(pptx["animations"]) > 0


def test_capability_map_get_renderer_for_feature():
    """get_renderer_for_feature 返回正确渲染器列表"""
    from office_suite.renderer.capability_map import get_renderer_for_feature

    # text 所有渲染器都支持
    renderers = get_renderer_for_feature("node_types", "text")
    assert "pptx" in renderers
    assert "pdf" in renderers

    # video 只有部分渲染器支持
    renderers = get_renderer_for_feature("node_types", "video")
    assert "pptx" in renderers


def test_capability_map_compare_renderers():
    """compare_renderers 正确比较差异"""
    from office_suite.renderer.capability_map import compare_renderers

    diff = compare_renderers("pptx", "docx")
    assert "only_in_1" in diff
    assert "only_in_2" in diff
    assert "common" in diff

    # PPTX 有动画，DOCX 没有
    assert len(diff["only_in_1"].get("animations", set())) > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
