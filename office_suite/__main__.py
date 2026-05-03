"""Command line entry point for Office Suite.

Provides the documented command:
    python -m office_suite build input.yml -o output.pptx
    python -m office_suite --help
"""

from __future__ import annotations

import argparse
from pathlib import Path

SUPPORTED_FORMATS = {"pptx", "docx", "xlsx", "pdf", "html"}


def _infer_format(output_path: Path, explicit_format: str | None) -> str:
    if explicit_format:
        fmt = explicit_format.lower().lstrip(".")
    else:
        fmt = output_path.suffix.lower().lstrip(".")

    if fmt not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(
            f"Cannot infer output format. Use an output suffix or --format. "
            f"Supported formats: {supported}"
        )
    return fmt


def build_command(args: argparse.Namespace) -> int:
    # 延迟导入：仅在实际渲染时才加载渲染器依赖
    from .tools.convert import convert_dsl_file

    input_path = Path(args.input)
    output_path = Path(args.output)
    target_format = _infer_format(output_path, args.format)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_path = convert_dsl_file(input_path, output_path, target_format)
    print(f"Rendered {target_format}: {rendered_path}")
    return 0


def import_media_command(args: argparse.Namespace) -> int:
    """将外部图片复制到项目产出目录"""
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    from .ai.media import import_media, collect_dsl_media, update_dsl_image_paths

    target_dir = Path(args.target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if args.dsl:
        # DSL 模式：自动收集 DSL 中的外部图片并更新路径引用
        dsl_path = Path(args.dsl)
        # 先扫描收集
        imported = collect_dsl_media(dsl_path, target_dir, overwrite=args.overwrite)
        if imported:
            print(f"Collected {len(imported)} image(s) to {target_dir}")
            for p in imported:
                print(f"  {p.name}")
            # 再更新 DSL 中的路径引用
            update_dsl_image_paths(dsl_path, target_dir, overwrite=args.overwrite)
            print(f"Updated DSL references: {dsl_path}")
        else:
            print("No external images found in DSL")
        return 0

    # 单张/批量模式
    if args.sources:
        for src in args.sources:
            dest = import_media(src, target_dir, overwrite=args.overwrite)
            print(f"Imported: {src} -> {dest}")
        print(f"\nTotal: {len(args.sources)} image(s) -> {target_dir}")
    else:
        print("error: provide --dsl or one or more source paths/URLs")
        return 1


def chart_engines_command(args: argparse.Namespace) -> int:
    from .engine.chart import list_engines

    engines = list_engines()
    print("Chart Rendering Engines:\n")
    print(f"  {'Engine':<14} {'Status':<16} {'Install Hint'}")
    print(f"  {'-'*12:<14} {'-'*14:<16} {'-'*40}")
    for e in engines:
        status = "available" if e["available"] else "not installed"
        print(f"  {e['name']:<14} {status:<16} {e['install_hint']}")
    print()
    n_available = sum(1 for e in engines if e["available"])
    print(f"  {n_available}/{len(engines)} engines available")
    return 0

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="office-suite",
        description="Office Suite 4.0 — Omni-media fusion document engine",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Render a YAML DSL file")
    build_parser.add_argument("input", help="Path to the YAML DSL entry file")
    build_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path, e.g. output/deck.pptx",
    )
    build_parser.add_argument(
        "-f",
        "--format",
        choices=sorted(SUPPORTED_FORMATS),
        help="Output format. Defaults to the output file extension.",
    )
    build_parser.set_defaults(func=build_command)

    # -- import-media --
    media_parser = subparsers.add_parser(
        "import-media",
        help="Import external images (URL/local path) to the project output directory",
    )
    media_parser.add_argument(
        "sources",
        nargs="*",
        help="Image source paths or URLs to import",
    )
    media_parser.add_argument(
        "-t",
        "--target-dir",
        required=True,
        help="Target directory to copy images into",
    )
    media_parser.add_argument(
        "--dsl",
        help="DSL YAML file path — auto-collect and update all external image references",
    )
    media_parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing files in target directory",
    )
    media_parser.set_defaults(func=import_media_command)

    # -- chart-engines --
    engines_parser = subparsers.add_parser(
        "chart-engines",
        help="List available chart rendering engines (matplotlib/plotly/vega-lite/ggplot2/pgfplots)",
    )
    engines_parser.set_defaults(func=chart_engines_command)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
