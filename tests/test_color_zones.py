"""3 区色彩模型 + Bento Grid 预设 + 5 维质量评分测试 + ppt-agent 扩展风格测试"""

import pytest

from office_suite.design.tokens import (
    COLOR_ZONES, get_color_zones, get_chart_palette,
    PALETTE, FONT_MAP, GRADIENTS,
)
from office_suite.design.auto_style import (
    get_zone_semantic, get_zone_chart, get_zone_decorative,
)
from office_suite.design.semantic_layouts import (
    SEMANTIC_LAYOUTS, resolve_semantic_layout,
)
from office_suite.design.quality_scorer import (
    score_document, QualityResult, DimensionScore,
)
from office_suite.ir.types import (
    IRDocument, IRNode, IRPosition, IRStyle, NodeType,
)


# ── 3 区色彩模型 ──────────────────────────────────────────────


class TestColorZones:
    def test_all_palettes_have_zones(self):
        """所有 PALETTE 中的主题都必须有对应 COLOR_ZONES"""
        for palette_name in PALETTE:
            assert palette_name in COLOR_ZONES, f"'{palette_name}' missing from COLOR_ZONES"

    def test_zone_structure(self):
        """每个主题的 COLOR_ZONES 结构完整"""
        for name, zones in COLOR_ZONES.items():
            assert "semantic" in zones, f"'{name}' missing 'semantic'"
            assert "chart" in zones, f"'{name}' missing 'chart'"
            assert "decorative_range" in zones, f"'{name}' missing 'decorative_range'"

            # semantic 必须有 3 个键
            assert set(zones["semantic"].keys()) == {"primary", "accent", "highlight"}, \
                f"'{name}' semantic keys: {zones['semantic'].keys()}"

            # chart 至少 8 色
            assert len(zones["chart"]) >= 8, f"'{name}' chart has {len(zones['chart'])} colors"

            # decorative_range 有 2 个值
            assert len(zones["decorative_range"]) == 2

    def test_chart_colors_are_hex(self):
        """chart 色板中的颜色必须是合法 hex"""
        for name, zones in COLOR_ZONES.items():
            for c in zones["chart"]:
                assert c.startswith("#") and len(c) == 7, \
                    f"'{name}' invalid chart color: {c}"

    def test_get_color_zones_fallback(self):
        """不存在的主题回退到 corporate"""
        zones = get_color_zones("nonexistent_theme")
        assert zones == COLOR_ZONES["corporate"]

    def test_get_chart_palette_index_wrap(self):
        """索引超出范围时自动取模"""
        chart = get_chart_palette("corporate")
        assert get_zone_chart("corporate", 0) == chart[0]
        assert get_zone_chart("corporate", 15) == chart[5]  # 15 % 10 = 5

    def test_get_zone_decorative_returns_tuple(self):
        result = get_zone_decorative("tech")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0].startswith("#")  # lightest
        assert result[1].startswith("#")  # darkest

    def test_all_palettes_have_font_map(self):
        """所有 PALETTE 中的主题都必须有对应 FONT_MAP"""
        for palette_name in PALETTE:
            assert palette_name in FONT_MAP, f"'{palette_name}' missing from FONT_MAP"

    def test_font_map_structure(self):
        """每个 FONT_MAP 条目必须有 body 和 display 键"""
        for name, fonts in FONT_MAP.items():
            assert "body" in fonts, f"'{name}' missing 'body' in FONT_MAP"
            assert "display" in fonts, f"'{name}' missing 'display' in FONT_MAP"
            assert isinstance(fonts["body"], str) and len(fonts["body"]) > 0
            assert isinstance(fonts["display"], str) and len(fonts["display"]) > 0

    def test_all_palettes_have_gradients(self):
        """所有 PALETTE 中的主题都必须有对应 GRADIENTS"""
        for palette_name in PALETTE:
            assert palette_name in GRADIENTS, f"'{palette_name}' missing from GRADIENTS"

    def test_gradient_structure(self):
        """每个 GRADIENTS 条目结构完整"""
        for name, grad in GRADIENTS.items():
            assert "type" in grad, f"'{name}' missing 'type'"
            assert "angle" in grad, f"'{name}' missing 'angle'"
            assert "stops" in grad, f"'{name}' missing 'stops'"
            assert len(grad["stops"]) >= 2, f"'{name}' needs at least 2 stops"
            for stop in grad["stops"]:
                assert stop.startswith("#") and len(stop) == 7, \
                    f"'{name}' invalid stop color: {stop}"


# ── Bento Grid 预设 ──────────────────────────────────────────


class TestBentoGridPresets:
    BENTO_PRESETS = [
        "hero_sidebar", "feature_showcase", "data_dashboard",
        "timeline_vertical", "comparison_table", "quote_highlight",
        "kpi_grid", "magazine_layout",
    ]

    def test_all_bento_presets_exist(self):
        """8 种 Bento 预设都已注册"""
        for name in self.BENTO_PRESETS:
            assert name in SEMANTIC_LAYOUTS, f"'{name}' missing from SEMANTIC_LAYOUTS"

    def test_bento_presets_are_12col_grid(self):
        """所有 Bento 预设使用 12 列 grid"""
        for name in self.BENTO_PRESETS:
            config = SEMANTIC_LAYOUTS[name]
            assert config["mode"] == "grid", f"'{name}' mode: {config['mode']}"
            assert config["grid"]["columns"] == 12, f"'{name}' columns: {config['grid']['columns']}"

    def test_bento_presets_have_margin(self):
        """所有 Bento 预设有 margin"""
        for name in self.BENTO_PRESETS:
            grid = SEMANTIC_LAYOUTS[name]["grid"]
            assert "margin" in grid, f"'{name}' missing margin"
            assert len(grid["margin"]) == 4

    def test_resolve_semantic_layout_bento(self):
        """resolve_semantic_layout 能解析 Bento 预设"""
        result = resolve_semantic_layout("hero_sidebar")
        assert result is not None
        assert result["mode"] == "grid"

    def test_old_presets_still_work(self):
        """原有 12 种预设不受影响"""
        for name in ["card_grid_2x2", "split_50_50", "cover_center"]:
            result = resolve_semantic_layout(name)
            assert result is not None

    def test_total_layout_count(self):
        """总布局数量至少 20 种（12 原有 + 8 Bento）"""
        assert len(SEMANTIC_LAYOUTS) >= 20


# ── 5 维质量评分 ──────────────────────────────────────────────


def _make_slide(children=None, layout_mode="absolute"):
    return IRNode(
        node_type=NodeType.SLIDE,
        extra={"layout_mode": layout_mode},
        children=children or [],
    )


def _make_text(content="hello", style_ref=None, font_color=None, font_family=None):
    style = None
    if font_color or font_family:
        style = IRStyle(font_color=font_color, font_family=font_family)
    return IRNode(
        node_type=NodeType.TEXT,
        content=content,
        position=IRPosition(x_mm=10, y_mm=10, width_mm=50, height_mm=20),
        style_ref=style_ref,
        style=style,
    )


class TestQualityScorer:
    def test_basic_scoring(self):
        """正常文档应该有合理分数"""
        slides = [
            _make_slide([_make_text("Title")], "grid"),
            _make_slide([_make_text("Content A"), _make_text("Content B")], "flex"),
            _make_slide([_make_text("Summary")], "grid"),
        ]
        doc = IRDocument(children=slides)
        result = score_document(doc, palette="corporate")

        assert isinstance(result, QualityResult)
        assert 0 <= result.total <= 100
        assert len(result.dimensions) == 5
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_report_format(self):
        """report() 输出包含关键信息"""
        slides = [_make_slide([_make_text("Test")])]
        doc = IRDocument(children=slides)
        result = score_document(doc)
        report = result.report()

        assert "Quality Score" in report
        assert "/100" in report
        assert "Visual Rhythm" in report
        assert "Color Narrative" in report
        assert "Narrative Arc" in report
        assert "Style Consistency" in report
        assert "Pacing" in report

    def test_empty_doc(self):
        """空文档评分不崩溃"""
        doc = IRDocument(children=[])
        result = score_document(doc)
        assert isinstance(result.total, float)
        assert result.total >= 0

    def test_single_slide(self):
        """单页文档评分"""
        doc = IRDocument(children=[_make_slide([_make_text("Only")])])
        result = score_document(doc)
        assert 0 <= result.total <= 100

    def test_visual_rhythm_diversity(self):
        """不同布局模式的文档，视觉节奏分更高"""
        # 多样布局
        diverse_slides = [
            _make_slide([_make_text("A")], "grid"),
            _make_slide([_make_text("B")], "flex"),
            _make_slide([_make_text("C")], "absolute"),
            _make_slide([_make_text("D")], "grid"),
        ]
        # 单一布局
        uniform_slides = [
            _make_slide([_make_text("A")], "grid"),
            _make_slide([_make_text("B")], "grid"),
            _make_slide([_make_text("C")], "grid"),
            _make_slide([_make_text("D")], "grid"),
        ]

        diverse_result = score_document(IRDocument(children=diverse_slides))
        uniform_result = score_document(IRDocument(children=uniform_slides))

        assert diverse_result.dimensions["visual_rhythm"].score >= \
               uniform_result.dimensions["visual_rhythm"].score

    def test_style_consistency_with_refs(self):
        """使用 style_ref 的文档，风格一致性更高"""
        styled_slides = [
            _make_slide([
                _make_text("A", style_ref="heading"),
                _make_text("B", style_ref="body"),
            ]),
            _make_slide([
                _make_text("C", style_ref="heading"),
            ]),
        ]
        unstyed_slides = [
            _make_slide([_make_text("A"), _make_text("B")]),
            _make_slide([_make_text("C")]),
        ]

        styled = score_document(IRDocument(
            children=styled_slides,
            styles={"heading": IRStyle(font_size=24), "body": IRStyle(font_size=12)},
        ))
        unstyled = score_document(IRDocument(children=unstyed_slides))

        assert styled.dimensions["style_consistency"].score >= \
               unstyled.dimensions["style_consistency"].score

    def test_narrative_arc_long_deck(self):
        """合理长度的文档，叙事弧得分不低"""
        slides = [_make_slide([_make_text(f"Slide {i}")]) for i in range(10)]
        doc = IRDocument(children=slides)
        result = score_document(doc)
        assert result.dimensions["narrative_arc"].score >= 50

    def test_dimension_weights_sum_to_one(self):
        """五个维度权重加总为 1.0"""
        from office_suite.design.quality_scorer import WEIGHTS
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_score_document_with_palette(self):
        """指定 palette 时色彩叙事维度会检查颜色一致性"""
        slides = [
            _make_slide([
                _make_text("Title", font_color="#1E40AF"),  # corporate primary
                _make_text("Sub", font_color="#3B82F6"),     # corporate secondary
            ]),
            _make_slide([_make_text("End", font_color="#FFFFFF")]),
        ]
        doc = IRDocument(children=slides)
        result = score_document(doc, palette="corporate")
        # 颜色来自 corporate palette，应有较高分数
        assert result.dimensions["color_narrative"].score >= 70

    def test_pacing_with_varying_density(self):
        """密度差异大的文档，节奏分有变化"""
        sparse = _make_slide([_make_text("Brief")])
        dense = _make_slide([
            _make_text(f"Item {i}") for i in range(8)
        ])
        slides = [sparse, dense, sparse, dense]
        doc = IRDocument(children=slides)
        result = score_document(doc)
        # 有明显密度变化，节奏分不应太低
        assert result.dimensions["pacing"].score >= 60


# ── ppt-agent 扩展风格验证 ────────────────────────────────────


_PPT_AGENT_NEW_STYLES = [
    "blueprint", "bold_editorial", "chalkboard",
    "editorial_infographic", "fantasy_animation",
    "intuition_machine", "notion", "pixel_art",
    "sketch_notes", "vector_illustration", "vintage", "watercolor",
]


class TestPptAgentStyles:
    def test_all_new_styles_in_palette(self):
        """12 种 ppt-agent 新风格都已注册到 PALETTE"""
        for name in _PPT_AGENT_NEW_STYLES:
            assert name in PALETTE, f"'{name}' missing from PALETTE"

    def test_all_new_styles_in_color_zones(self):
        """12 种新风格都已注册到 COLOR_ZONES"""
        for name in _PPT_AGENT_NEW_STYLES:
            assert name in COLOR_ZONES, f"'{name}' missing from COLOR_ZONES"

    def test_all_new_styles_in_font_map(self):
        """12 种新风格都已注册到 FONT_MAP"""
        for name in _PPT_AGENT_NEW_STYLES:
            assert name in FONT_MAP, f"'{name}' missing from FONT_MAP"

    def test_all_new_styles_in_gradients(self):
        """12 种新风格都已注册到 GRADIENTS"""
        for name in _PPT_AGENT_NEW_STYLES:
            assert name in GRADIENTS, f"'{name}' missing from GRADIENTS"

    def test_new_styles_palette_has_required_keys(self):
        """新风格 PALETTE 必须有所有必需键"""
        required = {"primary", "secondary", "accent", "bg", "text", "text_secondary", "border"}
        for name in _PPT_AGENT_NEW_STYLES:
            missing = required - set(PALETTE[name].keys())
            assert not missing, f"'{name}' missing keys: {missing}"

    def test_total_palette_count(self):
        """总配色方案数量至少 27 种（15 原有 + 12 ppt-agent）"""
        assert len(PALETTE) >= 27

    def test_total_color_zones_count(self):
        """总 COLOR_ZONES 数量与 PALETTE 一致"""
        assert len(COLOR_ZONES) >= len(PALETTE)

    def test_palette_color_zones_font_map_keys_match(self):
        """PALETTE、COLOR_ZONES、FONT_MAP 的键集合完全一致"""
        assert set(PALETTE.keys()) == set(COLOR_ZONES.keys()), \
            "PALETTE and COLOR_ZONES key mismatch"
        assert set(PALETTE.keys()) == set(FONT_MAP.keys()), \
            "PALETTE and FONT_MAP key mismatch"


# ── CLI --quality 集成 ─────────────────────────────────────────


class TestCLIQuality:
    def test_cli_quality_flag(self):
        """--quality 标志在 help 中显示"""
        from office_suite.__main__ import main
        import io
        import contextlib

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                main(["build", "--help"])
            except SystemExit:
                pass
        help_text = f.getvalue()
        assert "--quality" in help_text
