"""格式互转工具 — 在不同输出格式之间转换

转换路径：
  PPTX -> PDF  (通过 PDF 渲染器重新渲染 IR)
  PPTX -> HTML (通过 HTML 渲染器重新渲染 IR)
  DOCX -> PDF
  HTML -> PDF

注意：转换通过 IR 中间层完成，不是文件格式级别的转换。
输入可以是 IRDocument 或原始 DSL 文件。
"""

import logging
from pathlib import Path
from typing import Any

from ..dsl.parser import parse_yaml, parse_yaml_string
from ..ir.compiler import compile_document
from ..ir.types import IRDocument, dump_ir_json
from ..ir.validator import gate_validate_ir, GateValidationError
from ..renderer.pptx.deck import PPTXRenderer
from ..renderer.docx.document import DOCXRenderer
from ..renderer.xlsx.workbook import XLSXRenderer
from ..renderer.pdf.canvas import PDFRenderer
from ..renderer.html.dom import HTMLRenderer

logger = logging.getLogger(__name__)


_RENDERERS = {
    "pptx": PPTXRenderer,
    "docx": DOCXRenderer,
    "xlsx": XLSXRenderer,
    "pdf": PDFRenderer,
    "html": HTMLRenderer,
}


def convert_ir(ir_doc: IRDocument, output_path: Path | str, target_format: str) -> Path:
    """将 IR 文档渲染为目标格式

    Args:
        ir_doc: IR 文档
        output_path: 输出路径（不含扩展名也可以）
        target_format: 目标格式（pptx/docx/xlsx/pdf/html）

    Returns:
        输出文件路径
    """
    target_format = target_format.lower().lstrip(".")
    if target_format not in _RENDERERS:
        raise ValueError(f"不支持的目标格式: {target_format}，可选: {list(_RENDERERS.keys())}")

    output_path = Path(output_path)
    if output_path.suffix != f".{target_format}":
        output_path = output_path.with_suffix(f".{target_format}")

    renderer = _RENDERERS[target_format]()
    return renderer.render(ir_doc, output_path)


def convert_dsl_file(
    dsl_path: Path | str,
    output_path: Path | str,
    target_format: str,
    *,
    dump_ir_path: Path | str | None = None,
    strict: bool = False,
) -> Path:
    """从 DSL 文件转换为目标格式

    编译流程：
      1. parse_yaml → Document
      2. compile_document → IRDocument
      3. gate_validate_ir → 校验 position/style_ref/完整性
      4. dump_ir (可选) → 导出 IR JSON
      5. convert_ir → 渲染为目标格式

    Args:
        dsl_path: DSL YAML 文件路径
        output_path: 输出路径
        target_format: 目标格式
        dump_ir_path: 若指定，将 IR 树导出为 JSON 文件（用于调试/审查）
        strict: 严格模式，WARNING 也阻止渲染

    Returns:
        输出文件路径

    Raises:
        GateValidationError: 当 IR 校验发现不可忽略的错误时
    """
    doc = parse_yaml(Path(dsl_path))
    ir = compile_document(doc)

    # Gate 校验：拦截 position/style_ref/完整性问题
    try:
        gate_validate_ir(ir, strict=strict)
    except GateValidationError as exc:
        logger.warning("IR Gate validation found issues:\n%s", exc.result)
        raise

    # 可选：导出 IR JSON
    if dump_ir_path is not None:
        dump_path = Path(dump_ir_path)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = dump_ir_json(ir, pretty=True)
        dump_path.write_text(json_str, encoding="utf-8")
        logger.info("IR dumped to %s", dump_path)

    return convert_ir(ir, output_path, target_format)


def convert_dsl_string(yaml_str: str, output_path: Path | str, target_format: str) -> Path:
    """从 DSL 字符串转换为目标格式

    Args:
        yaml_str: DSL YAML 字符串
        output_path: 输出路径
        target_format: 目标格式

    Returns:
        输出文件路径
    """
    doc = parse_yaml_string(yaml_str)
    ir = compile_document(doc)
    return convert_ir(ir, output_path, target_format)


def batch_convert(ir_doc: IRDocument, output_dir: Path | str, formats: list[str]) -> dict[str, Path]:
    """将 IR 文档批量渲染为多种格式

    Args:
        ir_doc: IR 文档
        output_dir: 输出目录
        formats: 目标格式列表

    Returns:
        {格式: 输出路径} 映射
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for fmt in formats:
        out_path = output_dir / f"output.{fmt}"
        results[fmt] = convert_ir(ir_doc, out_path, fmt)
    return results
