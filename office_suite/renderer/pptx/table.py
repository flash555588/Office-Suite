"""PPTX 表格渲染 — 表格创建、数据填充、样式"""

from pptx.util import Pt
from pptx.dml.color import RGBColor

from ...ir.types import IRDocument, IRNode


def render_table(renderer, slide, node: IRNode, doc: IRDocument):
    """渲染表格元素

    数据来源（优先级从高到低）：
      - data_ref: 引用 doc.data 中的键（二维数组）
      - extra.data: 内联二维数组
      - extra.rows/extra.cols: 行列数（空表格）
    """
    pos = node.position
    left, top, width, height = renderer._pos_to_emu(pos)

    # 解析数据
    resolved_data: list | None = None
    if node.data_ref and node.data_ref in doc.data:
        ref_val = doc.data[node.data_ref]
        if isinstance(ref_val, list):
            resolved_data = ref_val
    if resolved_data is None:
        inline_data = node.extra.get("data")
        if isinstance(inline_data, list):
            resolved_data = inline_data

    # 推断行列数
    if resolved_data:
        rows = len(resolved_data)
        cols = max((len(r) for r in resolved_data if isinstance(r, list)), default=1)
    else:
        rows = node.extra.get("rows", 3)
        cols = node.extra.get("cols", 3)

    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    # 填充数据
    if isinstance(resolved_data, list):
        for r, row_data in enumerate(resolved_data[:rows]):
            if isinstance(row_data, list):
                for c, cell_val in enumerate(row_data[:cols]):
                    cell = table.cell(r, c)
                    cell.text = str(cell_val)
                    # 首行加粗（表头）
                    if r == 0:
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True

    apply_table_style(table, rows, cols)


def apply_table_style(table, rows: int, cols: int):
    """应用表格样式（交替行颜色）"""
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x3B)
                for p in cell.text_frame.paragraphs:
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        run.font.size = Pt(11)
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xF1, 0xF5, 0xF9)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
