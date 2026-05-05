"""PPTX 动画渲染 — IR IRAnimation → PPTX XML

python-pptx 不提供高级动画 API，需通过 Oxml 直接操作 slide XML。

支持四类动画（对应 PowerPoint 四大类）：
  1. 入场 (entry)     — 40 种效果
  2. 退出 (exit)      — 40 种效果
  3. 强调 (emphasis)   — 缩放 / 旋转 / 变色 / 脉冲
  4. 动作路径 (motion_path) — 直线 / 弧线 / 预设路径 / 自定义 SVG
"""

from lxml import etree

from ...ir.types import IRAnimation, ANIMATION_FALLBACK

# 全局自增 ID 计数器（每个 slide 内唯一）
_anim_id_counter = 0

# slide 级动画缓冲 —— apply_animations 往里存，flush 时统一写入 XML
_anim_buffer: list[tuple] = []  # [(shape_id, IRAnimation), ...]


def _next_anim_id() -> str:
    """返回下一个全局唯一的动画节点 ID"""
    global _anim_id_counter
    _anim_id_counter += 1
    return str(_anim_id_counter)


def reset_anim_id_counter():
    """重置计数器 — 每个 slide 渲染前调用"""
    global _anim_id_counter
    _anim_id_counter = 0


def reset_anim_buffer():
    """清空动画缓冲 — 每个 slide 渲染前调用"""
    global _anim_buffer
    _anim_buffer = []


# PPTX 动画效果名映射
# type: XML 元素类型 (animEffect / animScale / animRot / animClr / animMotion)
# filter: animEffect 的 filter 属性值
# transition: animEffect 的 transition 属性 (in/out)
# scale_to: animScale 的目标百分比 (100000=100%)
# rotate_to: animRot 的目标角度 (度)
# color_to: animClr 的目标颜色 (hex)
# path: animMotion 的 SVG 路径
EFFECT_MAP = {
    # ── 入场 ──────────────────────────────────────────────────
    "fade":          {"type": "animEffect", "filter": "fade",           "transition": "in"},
    "fade_in":       {"type": "animEffect", "filter": "fade",           "transition": "in"},
    # 擦除 (方向)
    "wipe_up":       {"type": "animEffect", "filter": "wipe(t)",        "transition": "in"},
    "wipe_down":     {"type": "animEffect", "filter": "wipe(b)",        "transition": "in"},
    "wipe_left":     {"type": "animEffect", "filter": "wipe(l)",        "transition": "in"},
    "wipe_right":    {"type": "animEffect", "filter": "wipe(r)",        "transition": "in"},
    "slide_up":      {"type": "animEffect", "filter": "wipe(t)",        "transition": "in"},
    "slide_down":    {"type": "animEffect", "filter": "wipe(b)",        "transition": "in"},
    "slide_left":    {"type": "animEffect", "filter": "wipe(l)",        "transition": "in"},
    "slide_right":   {"type": "animEffect", "filter": "wipe(r)",        "transition": "in"},
    # 飞入
    "fly_in":        {"type": "animEffect", "filter": "flyIn",          "transition": "in"},
    # 缩放
    "zoom_in":       {"type": "animEffect", "filter": "zoom",           "transition": "in"},
    "zoom_out_in":   {"type": "animEffect", "filter": "zoom",           "transition": "in"},
    # 百叶窗
    "blinds_h":      {"type": "animEffect", "filter": "blinds(h)",      "transition": "in"},
    "blinds_v":      {"type": "animEffect", "filter": "blinds(v)",      "transition": "in"},
    # 棋盘
    "checkerboard":  {"type": "animEffect", "filter": "checkerboard(h)","transition": "in"},
    "checkerboard_v":{"type": "animEffect", "filter": "checkerboard(v)","transition": "in"},
    # 盒状
    "box_in":        {"type": "animEffect", "filter": "box(in)",        "transition": "in"},
    "box_out":       {"type": "animEffect", "filter": "box(out)",       "transition": "in"},
    # 菱形
    "diamond":       {"type": "animEffect", "filter": "diamond",        "transition": "in"},
    # 十字
    "plus":          {"type": "animEffect", "filter": "plus",           "transition": "in"},
    # 轮辐
    "wheel_1":       {"type": "animEffect", "filter": "wheel(1)",       "transition": "in"},
    "wheel_2":       {"type": "animEffect", "filter": "wheel(2)",       "transition": "in"},
    "wheel_3":       {"type": "animEffect", "filter": "wheel(3)",       "transition": "in"},
    "wheel_4":       {"type": "animEffect", "filter": "wheel(4)",       "transition": "in"},
    "wheel_8":       {"type": "animEffect", "filter": "wheel(8)",       "transition": "in"},
    # 随机条
    "random_bars_h": {"type": "animEffect", "filter": "randomBar(h)",   "transition": "in"},
    "random_bars_v": {"type": "animEffect", "filter": "randomBar(v)",   "transition": "in"},
    # 形状
    "circle":        {"type": "animEffect", "filter": "circle",         "transition": "in"},
    "shape_diamond": {"type": "animEffect", "filter": "shape(diamond)", "transition": "in"},
    "shape_plus":    {"type": "animEffect", "filter": "shape(plus)",    "transition": "in"},
    # 切入
    "cut_in":        {"type": "animEffect", "filter": "none",           "transition": "in"},
    # 淡出变大
    "faded_swivel":  {"type": "animEffect", "filter": "fade",           "transition": "in"},
    # 条纹
    "strips_upleft":    {"type": "animEffect", "filter": "strips(lu)",  "transition": "in"},
    "strips_upright":   {"type": "animEffect", "filter": "strips(ru)",  "transition": "in"},
    "strips_downleft":  {"type": "animEffect", "filter": "strips(ld)",  "transition": "in"},
    "strips_downright": {"type": "animEffect", "filter": "strips(rd)",  "transition": "in"},
    # 轮子
    "wheel":         {"type": "animEffect", "filter": "wheel(8)",       "transition": "in"},

    # ── 退出 ──────────────────────────────────────────────────
    "fade_out":         {"type": "animEffect", "filter": "fade",           "transition": "out"},
    "wipe_out_up":      {"type": "animEffect", "filter": "wipe(t)",        "transition": "out"},
    "wipe_out_down":    {"type": "animEffect", "filter": "wipe(b)",        "transition": "out"},
    "wipe_out_left":    {"type": "animEffect", "filter": "wipe(l)",        "transition": "out"},
    "wipe_out_right":   {"type": "animEffect", "filter": "wipe(r)",        "transition": "out"},
    "slide_out_up":     {"type": "animEffect", "filter": "wipe(t)",        "transition": "out"},
    "slide_out_down":   {"type": "animEffect", "filter": "wipe(b)",        "transition": "out"},
    "slide_out_left":   {"type": "animEffect", "filter": "wipe(l)",        "transition": "out"},
    "slide_out_right":  {"type": "animEffect", "filter": "wipe(r)",        "transition": "out"},
    "fly_out":          {"type": "animEffect", "filter": "flyIn",          "transition": "out"},
    "zoom_out":         {"type": "animEffect", "filter": "zoom",           "transition": "out"},
    "zoom_out_exit":    {"type": "animEffect", "filter": "zoom",           "transition": "out"},
    "blinds_out_h":     {"type": "animEffect", "filter": "blinds(h)",      "transition": "out"},
    "blinds_out_v":     {"type": "animEffect", "filter": "blinds(v)",      "transition": "out"},
    "checkerboard_out": {"type": "animEffect", "filter": "checkerboard(h)","transition": "out"},
    "box_out_exit":     {"type": "animEffect", "filter": "box(out)",       "transition": "out"},
    "diamond_out":      {"type": "animEffect", "filter": "diamond",        "transition": "out"},
    "circle_out":       {"type": "animEffect", "filter": "circle",         "transition": "out"},
    "random_bars_out_h":{"type": "animEffect", "filter": "randomBar(h)",   "transition": "out"},
    "random_bars_out_v":{"type": "animEffect", "filter": "randomBar(v)",   "transition": "out"},
    "strips_out_upleft":   {"type": "animEffect", "filter": "strips(lu)",  "transition": "out"},
    "strips_out_upright":  {"type": "animEffect", "filter": "strips(ru)",  "transition": "out"},
    "strips_out_downleft": {"type": "animEffect", "filter": "strips(ld)",  "transition": "out"},
    "strips_out_downright":{"type": "animEffect", "filter": "strips(rd)",  "transition": "out"},

    # ── 强调：缩放 ────────────────────────────────────────────
    "pulse":    {"type": "animScale", "scale_to": 110000},
    "grow":     {"type": "animScale", "scale_to": 150000},
    "shrink":   {"type": "animScale", "scale_to": 75000},
    "grow_s":   {"type": "animScale", "scale_to": 120000},  # 轻微放大
    "shrink_s": {"type": "animScale", "scale_to": 90000},   # 轻微缩小

    # ── 强调：旋转 ────────────────────────────────────────────
    "spin_cw":         {"type": "animRot", "rotate_to": 360},
    "spin_ccw":        {"type": "animRot", "rotate_to": -360},
    "spin_half_cw":    {"type": "animRot", "rotate_to": 180},
    "spin_half_ccw":   {"type": "animRot", "rotate_to": -180},
    "spin_emphasis":   {"type": "animRot", "rotate_to": 360},

    # ── 强调：变色 ────────────────────────────────────────────
    "color_pulse":     {"type": "animClr", "color_to": "38BDF8"},  # 强调蓝
    "color_grow":      {"type": "animClr", "color_to": "22C55E"},  # 成功绿
    "color_warn":      {"type": "animClr", "color_to": "F59E0B"},  # 警告黄
    "color_flash":     {"type": "animClr", "color_to": "EF4444"},  # 错误红

    # ── 动作路径：直线 ────────────────────────────────────────
    "path_right":      {"type": "animMotion", "path": "M 0 0 L 1 0"},
    "path_left":       {"type": "animMotion", "path": "M 0 0 L -1 0"},
    "path_up":         {"type": "animMotion", "path": "M 0 0 L 0 -1"},
    "path_down":       {"type": "animMotion", "path": "M 0 0 L 0 1"},
    "path_up_right":   {"type": "animMotion", "path": "M 0 0 L 1 -1"},
    "path_down_right": {"type": "animMotion", "path": "M 0 0 L 1 1"},
    "path_up_left":    {"type": "animMotion", "path": "M 0 0 L -1 -1"},
    "path_down_left":  {"type": "animMotion", "path": "M 0 0 L -1 1"},

    # ── 动作路径：弧线 ────────────────────────────────────────
    "path_arc_right":  {"type": "animMotion", "path": "M 0 0 C 0.5 -0.5 1 -0.5 1 0"},
    "path_arc_left":   {"type": "animMotion", "path": "M 0 0 C -0.5 -0.5 -1 -0.5 -1 0"},
    "path_loop":       {"type": "animMotion", "path": "M 0 0 C 0.5 -1 1 0 0.5 0.5 C 0 1 -0.5 0 0 0"},

    # ── 动作路径：预设 ────────────────────────────────────────
    "path_diamond":    {"type": "animMotion", "path": "M 0 0 L 0.5 -0.5 L 1 0 L 0.5 0.5 Z"},
    "path_triangle":   {"type": "animMotion", "path": "M 0 0 L 0.5 -0.5 L 1 0 Z"},
    "path_hexagon":    {"type": "animMotion", "path": "M 0 0 L 0.5 -0.3 L 1 0 L 1 0.3 L 0.5 0.6 L 0 0.3 Z"},
    "path_figure_8":   {"type": "animMotion", "path": "M 0 0 C 0.5 -0.5 1 0 0.5 0.5 C 0 1 -0.5 0.5 0 0"},
}

# 缓动函数 → PPTX 加速/减速
EASING_PPTX = {
    "linear": {"accelerate": "0", "decelerate": "0"},
    "ease_in": {"accelerate": "100000", "decelerate": "0"},
    "ease_out": {"accelerate": "0", "decelerate": "100000"},
    "ease_in_out": {"accelerate": "50000", "decelerate": "50000"},
}

# 触发器映射
TRIGGER_MAP = {
    "on_click": "onClick",
    "with_previous": "withPrev",
    "after_previous": "afterPrev",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_animations(slide, shape, animations: list[IRAnimation]):
    """缓冲 IR 动画列表（不立即写入 XML）。

    真正写入延迟到 flush_slide_animations()，以便跨 shape 分组交错。
    """
    if not animations:
        return
    shape_id = shape.shape_id
    for anim in animations:
        _anim_buffer.append((shape_id, anim))


def flush_slide_animations(slide):
    """将本 slide 缓冲的所有动画统一分组并写入 timing XML。

    分组策略：
    - delay=0 的动画作为主动画（用户点击时触发）
    - delay>0 的动画在上一个动画结束后等待 delay 毫秒再播放
    """
    if not _anim_buffer:
        return

    p_ns = 'http://schemas.openxmlformats.org/presentationml/2006/main'
    a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    r_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    nsmap = {'p': p_ns, 'a': a_ns, 'r': r_ns}

    slide_elem = slide._element
    timing = slide_elem.find(f'{{{p_ns}}}timing')
    if timing is None:
        timing = etree.SubElement(slide_elem, f'{{{p_ns}}}timing')

    tn_lst = timing.find(f'{{{p_ns}}}tnLst')
    if tn_lst is None:
        tn_lst = etree.SubElement(timing, f'{{{p_ns}}}tnLst')

    # 按 delay 排序，分组
    sorted_buf = sorted(_anim_buffer, key=lambda x: x[1].delay)
    groups: list[list[tuple]] = []
    for item in sorted_buf:
        if not groups or item[1].delay == 0:
            groups.append([item])
        else:
            groups[-1].append(item)

    for group in groups:
        _add_anim_group(tn_lst, group, nsmap)

    _anim_buffer.clear()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_anim_group(tn_lst, group: list[tuple], nsmap: dict):
    """在 tnLst 下创建一个动画组（一个 par 容器），包含组内所有动画。

    group: [(shape_id, IRAnimation), ...]
    """
    p_ns = nsmap['p']

    # 顶层 par → cTn (container, indefinite)
    par = etree.SubElement(tn_lst, f'{{{p_ns}}}par')
    ctn = etree.SubElement(par, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', 'indefinite')
    ctn.set('restart', 'never')

    child = etree.SubElement(ctn, f'{{{p_ns}}}childTnLst')

    # seq（含 prevCondLst / nextCondLst —— PowerPoint 必需）
    seq = etree.SubElement(child, f'{{{p_ns}}}seq')
    seq.set('concurrent', '1')
    seq.set('nextAc', 'seek')

    prev_cl = etree.SubElement(seq, f'{{{p_ns}}}prevCondLst')
    prev_c = etree.SubElement(prev_cl, f'{{{p_ns}}}cond')
    prev_c.set('evt', 'onBegin')
    prev_c.set('delay', '0')
    etree.SubElement(etree.SubElement(prev_c, f'{{{p_ns}}}tgtEl'), f'{{{p_ns}}}sldTgt')

    next_cl = etree.SubElement(seq, f'{{{p_ns}}}nextCondLst')
    next_c = etree.SubElement(next_cl, f'{{{p_ns}}}cond')
    next_c.set('evt', 'onEnd')
    next_c.set('delay', '0')
    etree.SubElement(etree.SubElement(next_c, f'{{{p_ns}}}tgtEl'), f'{{{p_ns}}}sldTgt')

    seq_ctn = etree.SubElement(seq, f'{{{p_ns}}}cTn')
    seq_ctn.set('id', _next_anim_id())
    seq_ctn.set('dur', 'indefinite')
    seq_child = etree.SubElement(seq_ctn, f'{{{p_ns}}}childTnLst')

    # 第一个动画：onClick
    # 后续动画：onEnd（上一个动画结束后 + delay 毫秒播放）
    for i, (shape_id, anim) in enumerate(group):
        is_first = (i == 0)
        anim_par = etree.SubElement(seq_child, f'{{{p_ns}}}par')
        anim_ctn = etree.SubElement(anim_par, f'{{{p_ns}}}cTn')
        anim_ctn.set('id', _next_anim_id())
        anim_ctn.set('fill', 'hold')

        # stCondLst
        st = etree.SubElement(anim_ctn, f'{{{p_ns}}}stCondLst')
        cond = etree.SubElement(st, f'{{{p_ns}}}cond')

        if is_first:
            # 主动画：由用户点击触发
            cond.set('evt', 'onNext')
            cond.set('delay', '0')
        else:
            # 从属动画：上一个动画结束后等待 delay 毫秒
            cond.set('evt', 'onEnd')
            delay_ms = int(anim.delay * 1000)
            cond.set('delay', str(delay_ms))

        inner_child = etree.SubElement(anim_ctn, f'{{{p_ns}}}childTnLst')
        inner_par = etree.SubElement(inner_child, f'{{{p_ns}}}par')

        inner_ctn = etree.SubElement(inner_par, f'{{{p_ns}}}cTn')
        inner_ctn.set('id', _next_anim_id())
        inner_ctn.set('fill', 'hold')

        inner_st = etree.SubElement(inner_ctn, f'{{{p_ns}}}stCondLst')
        inner_cond = etree.SubElement(inner_st, f'{{{p_ns}}}cond')
        inner_cond.set('delay', '0')

        final_child = etree.SubElement(inner_ctn, f'{{{p_ns}}}childTnLst')

        # 查找效果信息
        effect_info = _resolve_effect(anim.effect)
        xml_type = effect_info.get("type", "animEffect")

        # 按 XML 类型分发到对应 builder
        if anim.anim_type == "motion_path" or xml_type == "animMotion":
            _build_motion_path(final_child, shape_id, anim, effect_info, p_ns, nsmap['a'])
        elif anim.anim_type == "entry":
            _build_entry_effect(final_child, shape_id, anim, effect_info, p_ns, nsmap['a'])
        elif anim.anim_type == "exit":
            _build_exit_effect(final_child, shape_id, anim, effect_info, p_ns, nsmap['a'])
        elif anim.anim_type == "emphasis":
            _build_emphasis_effect(final_child, shape_id, anim, effect_info, p_ns, nsmap['a'])


def _resolve_effect(effect_name: str) -> dict:
    """查找动画效果信息，未找到则降级到 fade"""
    info = EFFECT_MAP.get(effect_name)
    if info is not None:
        return info
    fallback = ANIMATION_FALLBACK.get(effect_name)
    if fallback:
        info = EFFECT_MAP.get(fallback)
        if info is not None:
            return info
    return EFFECT_MAP["fade"]


# ---------------------------------------------------------------------------
# Effect builders
# ---------------------------------------------------------------------------

def _build_entry_effect(parent, shape_id: int, anim: IRAnimation,
                        effect_info: dict, p_ns: str, a_ns: str):
    """构建入场效果 XML"""
    # set visibility → visible
    set_elem = etree.SubElement(parent, f'{{{p_ns}}}set')

    set_cbn = etree.SubElement(set_elem, f'{{{p_ns}}}cBhvr')
    set_ctn = etree.SubElement(set_cbn, f'{{{p_ns}}}cTn')
    set_ctn.set('id', _next_anim_id())
    set_ctn.set('dur', '1')
    set_ctn.set('fill', 'hold')

    set_tgt_el = etree.SubElement(set_cbn, f'{{{p_ns}}}tgtEl')
    set_sp_tgt = etree.SubElement(set_tgt_el, f'{{{p_ns}}}spTgt')
    set_sp_tgt.set('spid', str(shape_id))

    set_attr_name_l = etree.SubElement(set_cbn, f'{{{p_ns}}}attrNameLst')
    set_attr_name = etree.SubElement(set_attr_name_l, f'{{{p_ns}}}attrName')
    set_attr_name.text = 'style.visibility'

    set_to = etree.SubElement(set_elem, f'{{{p_ns}}}to')
    set_str = etree.SubElement(set_to, f'{{{p_ns}}}strVal')
    set_str.set('val', 'visible')

    # animEffect
    anim_effect = etree.SubElement(parent, f'{{{p_ns}}}animEffect')
    anim_effect.set('transition', effect_info.get('transition', 'in'))
    anim_effect.set('filter', effect_info.get('filter', 'fade'))

    # duration + easing
    anim_effect_cbn = etree.SubElement(anim_effect, f'{{{p_ns}}}cBhvr')
    anim_effect_ctn = etree.SubElement(anim_effect_cbn, f'{{{p_ns}}}cTn')
    anim_effect_ctn.set('id', _next_anim_id())
    dur_ms = int(anim.duration * 1000)
    anim_effect_ctn.set('dur', str(dur_ms))

    tgt_el = etree.SubElement(anim_effect_cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))

    easing_info = EASING_PPTX.get(anim.easing, EASING_PPTX["ease_out"])
    if easing_info.get("accelerate", "0") != "0":
        anim_effect_ctn.set('accelerate', easing_info["accelerate"])
    if easing_info.get("decelerate", "0") != "0":
        anim_effect_ctn.set('decelerate', easing_info["decelerate"])


def _build_exit_effect(parent, shape_id: int, anim: IRAnimation,
                       effect_info: dict, p_ns: str, a_ns: str):
    """构建退出效果 XML"""
    anim_effect = etree.SubElement(parent, f'{{{p_ns}}}animEffect')
    anim_effect.set('transition', 'out')
    anim_effect.set('filter', effect_info.get('filter', 'fade'))

    cbn = etree.SubElement(anim_effect, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))


def _build_emphasis_effect(parent, shape_id: int, anim: IRAnimation,
                           effect_info: dict, p_ns: str, a_ns: str):
    """构建强调效果 XML — 按 effect_info.type 分发到 animScale / animRot / animClr"""
    xml_type = effect_info.get("type", "animScale")

    if xml_type == "animRot":
        _build_emphasis_rot(parent, shape_id, anim, effect_info, p_ns)
    elif xml_type == "animClr":
        _build_emphasis_color(parent, shape_id, anim, effect_info, p_ns, a_ns)
    else:
        _build_emphasis_scale(parent, shape_id, anim, effect_info, p_ns)


def _build_emphasis_scale(parent, shape_id: int, anim: IRAnimation,
                           effect_info: dict, p_ns: str):
    """强调 — 缩放"""
    anim_scale = etree.SubElement(parent, f'{{{p_ns}}}animScale')
    anim_scale.set('zoomContent', '0')

    cbn = etree.SubElement(anim_scale, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))

    scale_val = str(effect_info.get("scale_to", 110000))
    to_elem = etree.SubElement(anim_scale, f'{{{p_ns}}}to')
    sx = etree.SubElement(to_elem, f'{{{p_ns}}}sx')
    sx.set('val', scale_val)
    sy = etree.SubElement(to_elem, f'{{{p_ns}}}sy')
    sy.set('val', scale_val)


def _build_emphasis_rot(parent, shape_id: int, anim: IRAnimation,
                         effect_info: dict, p_ns: str):
    """强调 — 旋转"""
    anim_rot = etree.SubElement(parent, f'{{{p_ns}}}animRot')
    rotate_deg = effect_info.get("rotate_to", 360)
    # PPTX 用 60000ths of a degree
    anim_rot.set('by', str(int(rotate_deg * 60000)))

    cbn = etree.SubElement(anim_rot, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))


def _build_emphasis_color(parent, shape_id: int, anim: IRAnimation,
                           effect_info: dict, p_ns: str, a_ns: str):
    """强调 — 颜色变化"""
    anim_clr = etree.SubElement(parent, f'{{{p_ns}}}animClr')

    cbn = etree.SubElement(anim_clr, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))
    ctn.set('fill', 'hold')

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))

    attr_lst = etree.SubElement(cbn, f'{{{p_ns}}}attrNameLst')
    attr = etree.SubElement(attr_lst, f'{{{p_ns}}}attrName')
    attr.text = 'fill'

    # 目标颜色
    color_hex = effect_info.get("color_to", "38BDF8")
    to_elem = etree.SubElement(anim_clr, f'{{{p_ns}}}to')
    srgb = etree.SubElement(to_elem, f'{{{a_ns}}}srgbClr')
    srgb.set('val', color_hex)


def _build_motion_path(parent, shape_id: int, anim: IRAnimation,
                        effect_info: dict, p_ns: str, a_ns: str):
    """动作路径 — 元素沿路径移动

    path 格式为归一化坐标 (0~1)，渲染时乘以 slide 尺寸转换为 EMU。
    SVG path 支持 M/L/C/Z 指令。
    """
    anim_motion = etree.SubElement(parent, f'{{{p_ns}}}animMotion')

    # 路径数据
    path_data = effect_info.get("path", anim.direction or "M 0 0 L 1 0")
    # 归一化 → PPTX 坐标系 (100000 = 100%)
    scaled_path = _scale_motion_path(path_data, 100000)
    anim_motion.set('path', scaled_path)

    # origin: parent 让路径相对于父容器
    anim_motion.set('origin', 'parent')

    cbn = etree.SubElement(anim_motion, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))


def _scale_motion_path(path_data: str, scale: int) -> str:
    """将归一化路径坐标 (0~1) 缩放为 PPTX 坐标

    输入: "M 0 0 L 1 0" 或 "M 0 0 C 0.5 -0.5 1 -0.5 1 0"
    输出: "M 0 0 L 100000 0" (scale=100000)
    """
    tokens = path_data.strip().split()
    result = []
    for t in tokens:
        if t.isalpha():
            result.append(t)
        else:
            try:
                val = float(t)
                result.append(str(int(val * scale)))
            except ValueError:
                result.append(t)
    return " ".join(result)
