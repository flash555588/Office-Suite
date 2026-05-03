"""LaTeX 数学 → Unicode 转换器

将基础 LaTeX 数学表达式转换为 Unicode 文本，可直接在 PPT 文本框中渲染。

支持范围：
  - 希腊字母：\alpha → α, \Beta → Β
  - 数学符号：\sum → Σ, \int → ∫, \infty → ∞
  - 上下标：x^2 → x², a_i → aᵢ
  - 分数：\frac{a}{b} → a/b
  - 根号：\sqrt{x} → √x, \sqrt[3]{x} → ³√x
  - 括号：\left( ... \right) → ( ... )
  - 运算符：\times → ×, \cdot → ·, \pm → ±
  - 关系符：\leq → ≤, \geq → ≥, \neq → ≠, \approx → ≈
  - 集合：\in → ∈, \subset → ⊂, \cup → ∪, \cap → ∩
  - 逻辑：\forall → ∀, \exists → ∃, \neg → ¬
  - 箭头：\rightarrow → →, \leftarrow → ←, \Rightarrow ⇒
  - 杂项：\ldots → …, \cdots → ⋯, \nabla → ∇

不支持：矩阵、对齐方程组、复杂排版。
这些超出 PPT 文本框的需求，请使用图片或手绘示意图。
"""

from __future__ import annotations

import re

# ============================================================
# 符号映射表
# ============================================================

# 希腊字母
_GREEK = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\vartheta": "ϑ", r"\iota": "ι", r"\kappa": "κ",
    r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ",
    r"\pi": "π", r"\rho": "ρ", r"\sigma": "σ", r"\tau": "τ",
    r"\upsilon": "υ", r"\phi": "φ", r"\varphi": "φ", r"\chi": "χ",
    r"\psi": "ψ", r"\omega": "ω",
    r"\Alpha": "Α", r"\Beta": "Β", r"\Gamma": "Γ", r"\Delta": "Δ",
    r"\Epsilon": "Ε", r"\Zeta": "Ζ", r"\Eta": "Η", r"\Theta": "Θ",
    r"\Iota": "Ι", r"\Kappa": "Κ", r"\Lambda": "Λ", r"\Mu": "Μ",
    r"\Nu": "Ν", r"\Xi": "Ξ", r"\Pi": "Π", r"\Rho": "Ρ",
    r"\Sigma": "Σ", r"\Tau": "Τ", r"\Upsilon": "Υ", r"\Phi": "Φ",
    r"\Chi": "Χ", r"\Psi": "Ψ", r"\Omega": "Ω",
}

# 大型运算符
_OPERATORS = {
    r"\sum": "Σ", r"\prod": "Π", r"\coprod": "∐",
    r"\int": "∫", r"\iint": "∬", r"\iiint": "∭", r"\oint": "∮",
    r"\bigcup": "⋃", r"\bigcap": "⋂", r"\bigoplus": "⨁", r"\bigotimes": "⨂",
}

# 运算符
_BINARY_OPS = {
    r"\times": "×", r"\div": "÷", r"\cdot": "·", r"\pm": "±", r"\mp": "∓",
    r"\ast": "∗", r"\star": "⋆", r"\circ": "∘", r"\bullet": "•",
    r"\oplus": "⊕", r"\otimes": "⊗",
}

# 关系符
_RELATIONS = {
    r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\neq": "≠", r"\ne": "≠", r"\approx": "≈", r"\equiv": "≡",
    r"\sim": "∼", r"\simeq": "≃", r"\cong": "≅", r"\propto": "∝",
    r"\ll": "≪", r"\gg": "≫", r"\prec": "≺", r"\succ": "≻",
    r"\perp": "⊥", r"\parallel": "∥",
}

# 集合与逻辑
_SETS = {
    r"\in": "∈", r"\notin": "∉", r"\ni": "∋",
    r"\subset": "⊂", r"\subseteq": "⊆", r"\supset": "⊃", r"\supseteq": "⊇",
    r"\cup": "∪", r"\cap": "∩", r"\setminus": "∖",
    r"\emptyset": "∅", r"\varnothing": "∅",
    r"\forall": "∀", r"\exists": "∃", r"\nexists": "∄",
    r"\neg": "¬", r"\lnot": "¬", r"\land": "∧", r"\lor": "∨",
}

# 箭头
_ARROWS = {
    r"\rightarrow": "→", r"\to": "→", r"\leftarrow": "←",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐",
    r"\leftrightarrow": "↔", r"\Leftrightarrow": "⇔",
    r"\uparrow": "↑", r"\downarrow": "↓",
    r"\mapsto": "↦", r"\hookrightarrow": "↪",
}

# 杂项
_MISC = {
    r"\infty": "∞", r"\partial": "∂", r"\nabla": "∇",
    r"\ldots": "…", r"\cdots": "⋯", r"\vdots": "⋮", r"\ddots": "⋱",
    r"\angle": "∠", r"\triangle": "△", r"\square": "□",
    r"\diamond": "◇", r"\star": "⋆",
    r"\dagger": "†", r"\ddagger": "‡",
    r"\ell": "ℓ", r"\hbar": "ℏ", r"\Re": "ℜ", r"\Im": "ℑ",
    r"\aleph": "ℵ", r"\wp": "℘",
    r"\prime": "′", r"\degree": "°",
    r"\quad": " ", r"\,": " ", r"\;": "  ",
    r"\!": "", r"\enspace": " ", r"\thinspace": " ",
    r"\left": "", r"\right": "",
    r"\text{": "", r"\mathrm{": "", r"\mathbf{": "", r"\mathit{": "",
    r"\textrm{": "", r"\operatorname{": "",
}

# 上标/下标映射
_SUPERSCRIPT = str.maketrans(
    "0123456789+-=()abcdefghijklmnoprstuvwxyzABDEGHIJKLMNOPRTUVW",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ",
)
_SUBSCRIPT = str.maketrans(
    "0123456789+-=()aehijklmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ",
)

# 合并所有符号表
_ALL_SYMBOLS: dict[str, str] = {}
for table in [_GREEK, _OPERATORS, _BINARY_OPS, _RELATIONS, _SETS, _ARROWS, _MISC]:
    _ALL_SYMBOLS.update(table)

# 按长度降序排列（优先匹配长命令）
_SYMBOL_RE = re.compile(
    r"\\(" + "|".join(re.escape(k.lstrip("\\")) for k in sorted(_ALL_SYMBOLS, key=len, reverse=True)) + r")(?=[^a-zA-Z]|$)"
)

# 上下标正则
_SUP_RE = re.compile(r"\^{([^}]*)}|\^([a-zA-Z0-9+-=])")
_SUB_RE = re.compile(r"_{([^}]*)}|_([a-zA-Z0-9+-=])")

# 分数正则
_FRAC_RE = re.compile(r"\\frac{([^}]*)}{([^}]*)}")

# 根号正则
_SQRT_RE = re.compile(r"\\sqrt(?:\[([^\]]*)\])?{([^}]*)}")


def latex_to_unicode(text: str) -> str:
    """将 LaTeX 数学表达式转换为 Unicode 文本

    Args:
        text: LaTeX 数学表达式（不带 $ 分隔符）

    Returns:
        Unicode 文本
    """
    result = text

    # 1. 处理分数 \frac{a}{b} → a/b
    result = _FRAC_RE.sub(lambda m: f"{m.group(1)}/{m.group(2)}", result)

    # 2. 处理根号
    def _sqrt_replace(m):
        index = m.group(1)
        content = m.group(2)
        if index:
            # \sqrt[3]{x} → ³√x
            sup = index.translate(_SUPERSCRIPT)
            return f"{sup}√{content}"
        return f"√{content}"

    result = _SQRT_RE.sub(_sqrt_replace, result)

    # 3. 处理上标
    def _sup_replace(m):
        content = m.group(1) or m.group(2)
        return content.translate(_SUPERSCRIPT)

    result = _SUP_RE.sub(_sup_replace, result)

    # 4. 处理下标
    def _sub_replace(m):
        content = m.group(1) or m.group(2)
        return content.translate(_SUBSCRIPT)

    result = _SUB_RE.sub(_sub_replace, result)

    # 5. 替换所有符号命令
    def _symbol_replace(m):
        cmd = "\\" + m.group(1)
        return _ALL_SYMBOLS.get(cmd, m.group(0))

    result = _SYMBOL_RE.sub(_symbol_replace, result)

    # 6. 清理残留的花括号
    result = result.replace("{", "").replace("}", "")

    # 7. 清理多余空格
    result = re.sub(r"  +", " ", result).strip()

    return result


def is_latex(text: str) -> bool:
    """判断文本是否包含 LaTeX 数学命令"""
    return "\\" in text and bool(re.search(r"\\[a-zA-Z]+", text))
