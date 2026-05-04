"""中间表示 — IR 类型 / 编译 / 校验 / 优化"""

from .types import (
    NodeType, IRNode, IRDocument, IRStyle, IRAnimation, IRPathText,
    validate_ir, dump_ir_json,
)
from .compiler import compile_document
from .validator import validate_ir_v2, gate_validate_ir, GateValidationError, ValidationResult
from .cascade import cascade_style
from .graph import IRGraph
from .resolver import ReferenceResolver
from .optimizer import IROptimizer
from .diff import IRDiff, DiffResult

__all__ = [
    "NodeType", "IRNode", "IRDocument", "IRStyle", "IRAnimation", "IRPathText",
    "validate_ir", "dump_ir_json",
    "compile_document", "validate_ir_v2", "gate_validate_ir", "GateValidationError",
    "ValidationResult", "cascade_style",
    "IRGraph", "ReferenceResolver", "IROptimizer", "IRDiff", "DiffResult",
]
