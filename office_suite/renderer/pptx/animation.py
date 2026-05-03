"""PPTX 动画渲染 — IR IRAnimation → PPTX XML

python-pptx 不提供高级动画 API，需通过 Oxml 注入 XML。

PPTX 动画 XML 结构：
  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" restart="never">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite">
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="3" fill="hold">
                      <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="4" fill="hold">
                            <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                            <p:childTnLst>
                              <p:set>...</p:set>  <!-- 入场 -->
                              <p:animEffect>...</p:animEffect>  <!-- 效果 -->
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>

简化实现：使用 Oxml 直接操作 slide XML。
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
# <a:animEffect transition="in" filter="..."> 或 <p:anim> 类型
EFFECT_MAP = {
    # 入场
    "fade": {"type": "animEffect", "filter": "fade", "transition": "in"},
    "fade_in": {"type": "animEffect", "filter": "fade", "transition": "in"},
    "slide_up": {"type": "animEffect", "filter": "wipe(t)", "transition": "in"},
    "slide_down": {"type": "animEffect", "filter": "wipe(b)", "transition": "in"},
    "slide_left": {"type": "animEffect", "filter": "wipe(l)", "transition": "in"},
    "slide_right": {"type": "animEffect", "filter": "wipe(r)", "transition": "in"},
    "zoom_in": {"type": "animEffect", "filter": "zoom", "transition": "in"},
    "zoom_out": {"type": "animEffect", "filter": "zoom", "transition": "out"},
    "fly_in": {"type": "animEffect", "filter": "flyIn", "transition": "in"},
    "wipe_up": {"type": "animEffect", "filter": "wipe(t)", "transition": "in"},
    "wipe_down": {"type": "animEffect", "filter": "wipe(b)", "transition": "in"},
    "wipe_left": {"type": "animEffect", "filter": "wipe(l)", "transition": "in"},
    "wipe_right": {"type": "animEffect", "filter": "wipe(r)", "transition": "in"},
    # 退出
    "fade_out": {"type": "animEffect", "filter": "fade", "transition": "out"},
    "slide_out_up": {"type": "animEffect", "filter": "wipe(t)", "transition": "out"},
    "slide_out_down": {"type": "animEffect", "filter": "wipe(b)", "transition": "out"},
    "slide_out_left": {"type": "animEffect", "filter": "wipe(l)", "transition": "out"},
    "slide_out_right": {"type": "animEffect", "filter": "wipe(r)", "transition": "out"},
    "zoom_out_exit": {"type": "animEffect", "filter": "zoom", "transition": "out"},
    # 强调
    "pulse": {"type": "animScale", "filter": "pulse"},
    "grow": {"type": "animScale", "filter": "grow"},
    "shrink": {"type": "animScale", "filter": "shrink"},
    "spin_emphasis": {"type": "animRot", "filter": "spin"},
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

        # 构建效果节点
        if anim.anim_type == "entry":
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
    """构建强调效果 XML（animScale，不绑定透明度）"""
    anim_scale = etree.SubElement(parent, f'{{{p_ns}}}animScale')
    anim_scale.set('zoomContent', '0')

    cbn = etree.SubElement(anim_scale, f'{{{p_ns}}}cBhvr')
    ctn = etree.SubElement(cbn, f'{{{p_ns}}}cTn')
    ctn.set('id', _next_anim_id())
    ctn.set('dur', str(int(anim.duration * 1000)))

    tgt_el = etree.SubElement(cbn, f'{{{p_ns}}}tgtEl')
    sp_tgt = etree.SubElement(tgt_el, f'{{{p_ns}}}spTgt')
    sp_tgt.set('spid', str(shape_id))

    # scale to（110% 放大，无透明度耦合）
    to_elem = etree.SubElement(anim_scale, f'{{{p_ns}}}to')
    sx = etree.SubElement(to_elem, f'{{{p_ns}}}sx')
    sx.set('val', '110000')
    sy = etree.SubElement(to_elem, f'{{{p_ns}}}sy')
    sy.set('val', '110000')
