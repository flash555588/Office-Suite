"""PPTX 幻灯片切换效果

支持的切换类型：
  fade, push, wipe, split, dissolve,
  blinds, checkerboard, cover, uncover,
  cut, diamond, newsflash, plus, random,
  fly, peek, strip, wheel, circle, shape

用法：
    from office_suite.renderer.pptx.transition import apply_transition
    apply_transition(slide, {"type": "fade", "speed": "med"})
"""

from pptx.oxml.ns import qn
import logging

logger = logging.getLogger(__name__)

# 切换类型 → PPTX XML 子元素名
# 向后兼容别名
TRANSITION_MAP = {
    "fade": {"spd": "med", "advClick": "1"},
    "push": {"spd": "med", "advClick": "1"},
    "wipe": {"spd": "med", "advClick": "1"},
    "split": {"spd": "med", "advClick": "1"},
    "dissolve": {"spd": "med", "advClick": "1"},
    "none": {},
}

TRANSITION_ELEMENTS = {
    "fade": "p:fade",
    "push": "p:push",
    "wipe": "p:wipe",
    "split": "p:split",
    "dissolve": "p:dissolve",
    "blinds": "p:blinds",
    "checkerboard": "p:checkerboard",
    "cover": "p:cover",
    "uncover": "p:uncover",
    "cut": "p:cut",
    "diamond": "p:diamond",
    "newsflash": "p:newsflash",
    "plus": "p:plus",
    "random": "p:randomBar",
    "fly": "p:fly",
    "peek": "p:peek",
    "strip": "p:strips",
    "wheel": "p:wheel",
    "circle": "p:circle",
    "shape": "p:shape",
}

# 方向映射（部分切换支持 dir 属性）
DIRECTION_MAP = {
    "left": "l",
    "right": "r",
    "up": "u",
    "down": "d",
}


def apply_transition(slide, transition_data: dict):
    """应用幻灯片切换效果

    Args:
        slide: python-pptx Slide 对象
        transition_data: 切换配置：
          - type: 切换类型 (fade/push/wipe/split/dissolve/...)
          - speed: 速度 (slow/med/fast)
          - advance_on_click: 是否点击切换 (默认 True)
          - advance_after: 自动切换秒数 (0 = 不自动)
          - direction: 方向 (left/right/up/down)
    """
    if not transition_data:
        return

    trans_type = str(transition_data.get("type", "none")).lower()
    if trans_type == "none" or trans_type not in TRANSITION_ELEMENTS:
        return

    speed = transition_data.get("speed", "med")
    advance_click = transition_data.get("advance_on_click", True)
    advance_after = transition_data.get("advance_after", 0)
    direction = transition_data.get("direction")

    try:
        sld_elem = slide._element

        # 移除已有 transition
        existing = sld_elem.find(qn("p:transition"))
        if existing is not None:
            sld_elem.remove(existing)

        # 构建 p:transition 元素
        trans_elem = sld_elem.makeelement(qn("p:transition"), {
            "spd": str(speed),
            "advClick": "1" if advance_click else "0",
        })

        if advance_after and advance_after > 0:
            # advanceAfter 单位是 1/1000 秒
            trans_elem.set("advTm", str(int(advance_after * 1000)))

        # 切换效果子元素
        elem_name = TRANSITION_ELEMENTS[trans_type]
        effect_elem = sld_elem.makeelement(qn(elem_name), {})

        # 方向属性（push/wipe/cover/uncover/fly/peek/strip 支持）
        if direction and trans_type in ("push", "wipe", "cover", "uncover", "fly", "peek", "strip"):
            dir_val = DIRECTION_MAP.get(direction, direction)
            effect_elem.set("dir", dir_val)

        # blinds 支持 vert 属性
        if trans_type == "blinds" and direction == "vertical":
            effect_elem.set("vert", "1")

        trans_elem.append(effect_elem)

        # 插入到 p:sld 中（在 p:timing 之前，若无则追加末尾）
        timing = sld_elem.find(qn("p:timing"))
        if timing is not None:
            sld_elem.insert(list(sld_elem).index(timing), trans_elem)
        else:
            sld_elem.append(trans_elem)

        logger.debug("[PPTX Transition] slide transition: %s (speed=%s, dir=%s)", trans_type, speed, direction)

    except Exception as e:
        logger.warning("[PPTX Transition] 切换效果注入失败: %s", e)
