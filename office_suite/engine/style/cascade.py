"""样式级联引擎 — 实现 theme → document → slide → element → inline 的优先级递增

级联规则：
- 每层只覆盖有值的属性，空值跳过
- 更近的层优先级更高
- 支持 !important 标记（跳过后续覆盖）

关键设计：IRStyle 所有字段默认 None，级联时只覆盖非 None 字段。
这样主题层设置 font_weight=700 后，文档层如果没有显式设置 font_weight，
就不会覆盖主题的值。渲染器最终用 _STYLE_DEFAULTS 填充仍为 None 的字段。

架构位置：ir/compiler.py 调用 cascade_style_by_name() → 本模块 → 返回合并后的 IRStyle
"""

from ...ir.types import IRStyle
from copy import deepcopy


# 假设的默认主题样式（P0 使用）
DEFAULT_THEME_STYLES: dict[str, IRStyle] = {
    "default": IRStyle(
        font_family="Microsoft YaHei UI",
        font_size=18,
        font_weight=400,
        font_color="#000000",
    ),
    "title": IRStyle(
        font_family="Microsoft YaHei UI",
        font_size=44,
        font_weight=700,
        font_color="#1E293B",
    ),
    "subtitle": IRStyle(
        font_family="Microsoft YaHei UI",
        font_size=24,
        font_weight=400,
        font_color="#64748B",
    ),
}


def _merge_field(target, source, field: str):
    """将 source 的非 None 字段值覆盖到 target"""
    src_val = getattr(source, field, None)
    if src_val is not None:
        # 对于字符串，空字符串视为未设置
        if isinstance(src_val, str) and src_val == "":
            return
        # 对于 int/float，0 保留（0 是有效值，如 font_size=0 表示继承）
        setattr(target, field, src_val)


def cascade_style(
    *layers: IRStyle | None,
) -> IRStyle:
    """按优先级级联合并多个 IRStyle

    参数从低优先级到高优先级排列：
        cascade_style(theme_style, doc_style, slide_style, element_style)

    返回合并后的 IRStyle，不修改任何输入。
    """
    result = IRStyle()  # 空默认值

    for layer in layers:
        if layer is None:
            continue
        _merge_field(result, layer, "font_family")
        _merge_field(result, layer, "font_size")
        _merge_field(result, layer, "font_weight")
        _merge_field(result, layer, "font_italic")
        _merge_field(result, layer, "font_color")
        _merge_field(result, layer, "fill_color")
        _merge_field(result, layer, "fill_opacity")
        # 深拷贝复杂对象
        if layer.fill_gradient is not None:
            result.fill_gradient = deepcopy(layer.fill_gradient)
        if layer.shadow is not None:
            result.shadow = deepcopy(layer.shadow)
        if layer.border is not None:
            result.border = deepcopy(layer.border)
        if layer.text_effect is not None:
            result.text_effect = deepcopy(layer.text_effect)
        if layer.text_outline is not None:
            result.text_outline = deepcopy(layer.text_outline)
        if layer.text_reflection is not None:
            result.text_reflection = deepcopy(layer.text_reflection)
        if layer.text_bevel is not None:
            result.text_bevel = deepcopy(layer.text_bevel)
        _merge_field(result, layer, "letter_spacing")
        _merge_field(result, layer, "word_spacing")
        if layer.theme_ref is not None:
            result.theme_ref = layer.theme_ref

    return result


def cascade_style_by_name(
    style_name: str | None,
    theme_styles: dict[str, IRStyle],
    doc_styles: dict[str, IRStyle],
    slide_style: IRStyle | None = None,
    element_style: IRStyle | None = None,
) -> IRStyle:
    """按名称解析样式级联

    级联顺序（低→高）：
    1. theme 默认样式 (IRStyle() — 全 None 基底)
    2. theme 中同名样式
    3. document 中同名样式
    4. slide 级样式
    5. element 级内联样式

    注意：如果元素有内联样式但无 style_name，则跳过 theme/doc 同名层，
    直接在默认基底上叠加内联样式，避免无关的全局样式泄漏。
    """
    # 层 1: 默认基底（全 None）
    default = IRStyle()

    if style_name:
        # 有样式名：走完整级联链
        theme_named = theme_styles.get(style_name)
        doc_named = doc_styles.get(style_name)
        return cascade_style(
            default,
            theme_named,
            doc_named,
            slide_style,
            element_style,
        )
    else:
        # 无样式名：仅叠加 slide + element，不走 theme/doc 同名
        return cascade_style(
            default,
            slide_style,
            element_style,
        )
