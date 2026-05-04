"""DSL Parser — YAML/JSON → Document 对象解析器

数据流：YAML 文件/字符串 → load_yaml() → 原始 dict → parse_document() → Document 对象

注意：parse_element() 中 style 字段保持原始 dict 不做解析，
由 ir/compiler.py::compile_element() 负责将 dict → StyleSpec → IRStyle。
这样设计的原因：编译器需要在样式级联的上下文中处理样式，
而不是在解析阶段就丢失级联信息。

架构位置：YAML 文件 → [本文件] → Document → ir/compiler.py → IRDocument
"""

from pathlib import Path
from typing import Any

import yaml

from .schema import (
    DataBinding,
    Document,
    DocType,
    Element,
    FillSpec,
    FontSpec,
    GradientSpec,
    PositionSpec,
    ShadowSpec,
    Slide,
    StyleSpec,
)


def parse_position(raw: dict[str, Any] | None) -> PositionSpec | None:
    """解析位置规格"""
    if not raw:
        return None
    return PositionSpec(
        x=raw.get("x"),
        y=raw.get("y"),
        width=raw.get("width"),
        height=raw.get("height"),
        bottom=raw.get("bottom"),
        center=raw.get("center", False),
    )


def parse_font(raw: dict[str, Any] | None) -> FontSpec | None:
    """解析字体规格"""
    if not raw:
        return None
    return FontSpec(
        family=raw.get("family", "Microsoft YaHei UI"),
        size=raw.get("size", 18),
        weight=raw.get("weight", 400),
        italic=raw.get("italic", False),
        color=raw.get("color", "#000000"),
    )


def parse_gradient(raw: dict[str, Any] | None) -> GradientSpec | None:
    """解析渐变规格"""
    if not raw:
        return None
    return GradientSpec(
        type=raw.get("type", "linear"),
        angle=raw.get("angle", 0),
        stops=raw.get("stops", ["#000000", "#FFFFFF"]),
    )


def parse_fill(raw: dict[str, Any] | None) -> FillSpec | None:
    """解析填充规格"""
    if not raw:
        return None
    return FillSpec(
        color=raw.get("color"),
        gradient=parse_gradient(raw.get("gradient")),
        opacity=raw.get("opacity", 1.0),
    )


def parse_shadow(raw: dict[str, Any] | None) -> ShadowSpec | None:
    """解析阴影规格"""
    if not raw:
        return None
    return ShadowSpec(
        blur=raw.get("blur", 0),
        offset=raw.get("offset", [0, 0]),
        color=raw.get("color", "#00000040"),
    )


def parse_style(raw: dict[str, Any] | None) -> StyleSpec | None:
    """解析样式规格"""
    if not raw:
        return None
    return StyleSpec(
        font=parse_font(raw.get("font")),
        fill=parse_fill(raw.get("fill")),
        shadow=parse_shadow(raw.get("shadow")),
        border=raw.get("border"),
        text_effect=raw.get("text_effect"),
    )


def parse_element(raw: dict[str, Any]) -> Element:
    """解析单个元素"""
    position_raw = raw.get("position")
    # 支持简写：position 可以直接是字符串 "background"
    if isinstance(position_raw, str) and position_raw == "background":
        position_raw = None  # 特殊标记

    # extra 字段：收集所有非标准属性
    # 特殊处理：YAML 中的 "extra" 键会展开合并，避免嵌套
    EXCLUDE_KEYS = {
        "type", "content", "format", "source", "style", "style_ref", "position",
        "data_ref", "chart_type", "query", "prompt",
        "size", "opacity", "filter", "animation", "children",
        "catalog_ref", "catalog_id", "catalog_params", "params",
    }
    extra = {k: v for k, v in raw.items() if k not in EXCLUDE_KEYS}
    # 如果 YAML 中有显式的 "extra" 键，展开合并
    if "extra" in extra and isinstance(extra["extra"], dict):
        nested = extra.pop("extra")
        extra.update(nested)

    # catalog_ref 支持：type=catalog_ref 或显式 catalog_id 字段
    catalog_ref = raw.get("catalog_ref")
    if catalog_ref is None and raw.get("type") == "catalog_ref":
        catalog_ref = raw.get("catalog_id", raw.get("id"))

    return Element(
        type=raw.get("type", "text"),
        content=raw.get("content"),
        format=raw.get("format", "plain"),
        source=raw.get("source", raw.get("src")),
        style_ref=raw.get("style_ref"),
        style=raw.get("style"),  # 可以是字符串引用或内联样式
        position=parse_position(position_raw) if isinstance(position_raw, dict) else None,
        data_ref=raw.get("data_ref"),
        chart_type=raw.get("chart_type"),
        query=raw.get("query"),
        prompt=raw.get("prompt"),
        size=raw.get("size"),
        opacity=raw.get("opacity", 1.0),
        filter=raw.get("filter"),
        animation=raw.get("animation"),
        children=[parse_element(c) for c in raw.get("children", [])],
        catalog_ref=catalog_ref,
        catalog_params=raw.get("catalog_params", raw.get("params")),
        extra=extra,
    )


def parse_layers(raw: dict[str, Any] | None) -> dict[str, list[Element]]:
    """解析 slide.layers，允许单个对象或对象列表。"""
    if not isinstance(raw, dict):
        return {}
    layers: dict[str, list[Element]] = {}
    for layer_name, layer_items in raw.items():
        if isinstance(layer_items, dict):
            items = [layer_items]
        elif isinstance(layer_items, list):
            items = [item for item in layer_items if isinstance(item, dict)]
        else:
            items = []
        layers[str(layer_name)] = [parse_element(item) for item in items]
    return layers


def _expand_catalog_refs(elements_raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """展开元素列表中的 catalog_ref 引用

    对于 type=catalog_ref 或含 catalog_ref 字段的元素，
    调用 ElementCatalog.generate_dsl() 将其展开为标准元素列表。
    非 catalog_ref 元素原样保留。
    """
    expanded: list[dict[str, Any]] = []
    for raw in elements_raw:
        if not isinstance(raw, dict):
            expanded.append(raw)
            continue

        is_catalog_ref = (
            raw.get("type") == "catalog_ref"
            or "catalog_ref" in raw
            or "catalog_id" in raw
        )
        if not is_catalog_ref:
            expanded.append(raw)
            continue

        ref_id = raw.get("catalog_ref") or raw.get("catalog_id") or raw.get("id")
        params = raw.get("catalog_params", raw.get("params", {}))
        pos = raw.get("position")  # 保留位置覆盖

        try:
            from ..catalog.catalog import get_catalog
            catalog = get_catalog()
            fragments = catalog.generate_dsl(ref_id, params)
            if pos and isinstance(fragments, list):
                for frag in fragments:
                    if isinstance(frag, dict) and "position" not in frag:
                        frag["position"] = pos
            expanded.extend(fragments)
        except (KeyError, ImportError):
            # catalog 未加载或条目不存在，保留原始元素
            expanded.append(raw)

    return expanded


def parse_slide(raw: dict[str, Any]) -> Slide:
    """解析单张幻灯片"""
    # 在解析前展开 catalog_ref 引用
    raw_elements = _expand_catalog_refs(raw.get("elements", []))
    # 创建一个修改过的 raw dict（不修改原始）
    raw = {**raw, "elements": raw_elements}
    return Slide(
        layout=raw.get("layout", "blank"),
        layout_mode=raw.get("layout_mode", ""),
        grid=raw.get("grid"),
        flex=raw.get("flex"),
        constraints=raw.get("constraints"),
        card_container=raw.get("card_container", False),
        background=raw.get("background"),
        background_board=raw.get("background_board"),
        layers=parse_layers(raw.get("layers")),
        elements=[parse_element(e) for e in raw.get("elements", [])],
        transition=raw.get("transition"),
    )


def parse_data_binding(raw: dict[str, Any]) -> DataBinding:
    """解析数据绑定"""
    return DataBinding(
        source=raw.get("source"),
        columns=raw.get("columns", []),
        formula=raw.get("formula"),
        inline=raw.get("inline"),
    )


def _resolve_src_paths(raw: Any, base_dir: Path | str) -> None:
    """递归解析 slide YAML 中元素的 src/source 相对路径为绝对路径"""
    if isinstance(base_dir, str):
        base_dir = Path(base_dir)
    if isinstance(raw, dict):
        for key in ("src", "source"):
            val = raw.get(key)
            if isinstance(val, str) and not val.startswith(("http://", "https://", "file://", "/")):
                resolved = (base_dir / val).resolve()
                raw[key] = str(resolved)
        for v in raw.values():
            if isinstance(v, (dict, list)):
                _resolve_src_paths(v, base_dir)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, (dict, list)):
                _resolve_src_paths(item, base_dir)


def _load_slide_refs(page_refs: list[Any], base_dir: Path | None) -> list[dict[str, Any]]:
    """Load slide/page YAML files referenced by a presentation entry file.

    The legacy format keeps every slide under top-level ``slides``.  The
    preferred presentation authoring format keeps one slide per YAML file and
    lists those files under top-level ``pages``:

    pages:
      - pages/001_cover.yml
      - pages/002_agenda.yml

    A referenced file may contain a slide object directly, ``slide: {...}``, or
    ``slides: [...]`` for compatibility with existing examples.
    """
    slides: list[dict[str, Any]] = []
    for index, ref in enumerate(page_refs):
        if isinstance(ref, dict):
            if "path" in ref:
                ref = ref["path"]
            else:
                slides.append(ref)
                continue

        if not isinstance(ref, str):
            raise TypeError(f"pages[{index}] must be a path string or slide object")
        if base_dir is None:
            raise ValueError("String paths in 'pages' require parse_yaml(path); parse_yaml_string cannot resolve them")

        page_path = Path(ref)
        if not page_path.is_absolute():
            page_path = base_dir / page_path
        page_raw = load_yaml(page_path)

        # 将元素中的 src/source 相对路径解析为绝对路径（相对于页面文件所在目录）
        _resolve_src_paths(page_raw, page_path.parent)

        if "slides" in page_raw:
            raw_slides = page_raw.get("slides") or []
            if not isinstance(raw_slides, list):
                raise TypeError(f"{page_path}: slides must be a list")
            slides.extend(raw_slides)
        elif "slide" in page_raw:
            slide = page_raw["slide"]
            if not isinstance(slide, dict):
                raise TypeError(f"{page_path}: slide must be an object")
            slides.append(slide)
        else:
            slides.append(page_raw)
    return slides


def parse_document(raw: dict[str, Any], base_dir: Path | None = None) -> Document:
    """解析完整文档"""
    doc_type_str = raw.get("type", "presentation")
    try:
        doc_type = DocType(doc_type_str)
    except ValueError:
        doc_type = DocType.PRESENTATION

    data_bindings = {}
    for key, val in (raw.get("data") or {}).items():
        if isinstance(val, dict):
            data_bindings[key] = parse_data_binding(val)

    styles = {}
    for key, val in (raw.get("styles") or {}).items():
        if isinstance(val, dict):
            styles[key] = parse_style(val)

    raw_slides = list(raw.get("slides", []) or [])
    page_refs = raw.get("pages", []) or []
    if page_refs:
        if not isinstance(page_refs, list):
            raise TypeError("pages must be a list")
        raw_slides.extend(_load_slide_refs(page_refs, base_dir))

    # 内联 slides 也需要解析 src/source 相对路径
    if base_dir:
        for s in raw_slides:
            _resolve_src_paths(s, base_dir)

    slides = [parse_slide(s) for s in raw_slides]

    return Document(
        version=raw.get("version", "4.0"),
        type=doc_type,
        theme=raw.get("theme", "default"),
        title=raw.get("title", ""),
        style_preset=raw.get("style_preset", ""),
        design_manifest=raw.get("design_manifest", ""),
        auto_enhance=bool(raw.get("auto_enhance", False)),
        data=data_bindings,
        styles=styles,
        slides=slides,
        sections=raw.get("sections", []),
        raw=raw,
    )


def _sanitize_yaml_quotes(text: str) -> str:
    """将中文引号替换为 ASCII 引号，避免 YAML 解析失败。

    PyYAML 在双引号字符串中遇到未转义的 ``"`` 会报错。
    中文排版常用 ``“`` (U+201C) 和 ``”`` (U+201D)，这里统一替换。
    """
    return text.replace("“", '\\"').replace("”", '\\"')


def safe_yaml_load(text: str):
    """带引号净化的 yaml.safe_load，供全项目统一使用。"""
    return yaml.safe_load(_sanitize_yaml_quotes(text))


def load_yaml(path: str | Path) -> dict[str, Any]:
    """加载 YAML 文件"""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return safe_yaml_load(text)


def parse_yaml(path: str | Path) -> Document:
    """从 YAML 文件解析为 Document"""
    path = Path(path)
    raw = load_yaml(path)
    return parse_document(raw, base_dir=path.parent)


def parse_yaml_string(yaml_str: str) -> Document:
    """从 YAML 字符串解析为 Document"""
    raw = safe_yaml_load(yaml_str)
    return parse_document(raw)
