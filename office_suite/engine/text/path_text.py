"""路径文字 — 沿曲线排列文字

设计方案第八章：文本引擎。

路径文字将文本沿 SVG 路径曲线排列：
  - 沿弧线排列
  - 沿波浪线排列
  - 沿自定义 SVG 路径排列

PPTX 实现方式：
  python-pptx 不直接支持路径文字，
  通过 Oxml 注入 <a:pathLst> + 沿路径分布的关键帧实现。
  简化方案：将路径离散为多个文本片段，每个片段独立旋转定位。

其他渲染器：
  - HTML: SVG textPath + <textPath href="#path">
  - PDF: 降级为水平文本
  - DOCX: 降级为普通文本
"""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class PathPoint:
    """路径上的点"""
    x: float
    y: float
    angle: float  # 切线角度（度）


@dataclass
class PathTextConfig:
    """路径文字配置"""
    path_type: str = "arc"      # 预设类型或 custom
    radius: float = 100.0       # 弧线半径（mm）
    start_angle: float = 0.0    # 起始角度（度）
    end_angle: float = 180.0    # 结束角度（度）
    amplitude: float = 10.0     # 波浪振幅（mm）
    wavelength: float = 50.0    # 波长（mm）
    custom_path: str = ""       # SVG 路径数据（M x y C ...）
    char_spacing: float = 0.0   # 字符间距（mm）
    bend: float = 50.0          # 弯曲程度 0-100（presetTextWarp 用）


# path_type → PPTX presetTextWarp 映射
PATH_TYPE_TO_PPTX_PRESET = {
    "arc": "textArchDown",
    "arch_up": "textArchUp",
    "wave": "textWave1",
    "circle": "textCircle",
    "button": "textButton",
    "chevron": "textChevron",
    "slant_up": "textSlantUp",
    "slant_down": "textSlantDown",
    "triangle": "textTriangle",
    "inflate": "textInflate",
    "deflate": "textDeflate",
}

# 需要逐字符放置的路径类型（无对应 presetTextWarp）
CHAR_PLACEMENT_TYPES = {"custom"}


# ============================================================
# 路径生成
# ============================================================

def generate_arc_points(
    radius: float,
    start_angle: float,
    end_angle: float,
    num_points: int = 50,
    center_x: float = 0,
    center_y: float = 0,
) -> list[PathPoint]:
    """生成弧线路径点

    Args:
        radius: 弧线半径（mm）
        start_angle: 起始角度（度）
        end_angle: 结束角度（度）
        num_points: 采样点数
        center_x: 圆心 x
        center_y: 圆心 y

    Returns:
        路径点列表
    """
    points = []
    for i in range(num_points):
        t = i / max(1, num_points - 1)
        angle = math.radians(start_angle + (end_angle - start_angle) * t)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        # 切线角度 = 路径角度 + 90度（文字沿切线方向）
        tangent = math.degrees(angle) + 90
        points.append(PathPoint(x=x, y=y, angle=tangent))
    return points


def generate_wave_points(
    amplitude: float,
    wavelength: float,
    length: float,
    num_points: int = 50,
    start_x: float = 0,
    start_y: float = 0,
) -> list[PathPoint]:
    """生成波浪路径点

    Args:
        amplitude: 振幅（mm）
        wavelength: 波长（mm）
        length: 总长度（mm）
        num_points: 采样点数
        start_x: 起始 x
        start_y: 起始 y

    Returns:
        路径点列表
    """
    points = []
    for i in range(num_points):
        t = i / max(1, num_points - 1)
        x = start_x + length * t
        y = start_y + amplitude * math.sin(2 * math.pi * x / wavelength)
        # 切线角度
        dx = length / max(1, num_points - 1)
        dy = amplitude * 2 * math.pi / wavelength * math.cos(2 * math.pi * x / wavelength)
        angle = math.degrees(math.atan2(dy, dx))
        points.append(PathPoint(x=x, y=y, angle=angle))
    return points


def parse_svg_path(path_data: str, num_points: int = 50) -> list[PathPoint]:
    """解析简化版 SVG 路径数据

    支持的命令：M (moveto), L (lineto), C (cubic bezier), Q (quadratic bezier)

    Args:
        path_data: SVG 路径字符串
        num_points: 每段的采样点数

    Returns:
        路径点列表
    """
    points = []
    parts = path_data.replace(",", " ").split()
    current_x, current_y = 0.0, 0.0
    i = 0

    while i < len(parts):
        cmd = parts[i]
        if cmd in ("M", "m"):
            dx = float(parts[i + 1])
            dy = float(parts[i + 2])
            if cmd == "m":
                current_x += dx
                current_y += dy
            else:
                current_x = dx
                current_y = dy
            points.append(PathPoint(x=current_x, y=current_y, angle=0))
            i += 3
        elif cmd in ("L", "l"):
            dx = float(parts[i + 1])
            dy = float(parts[i + 2])
            if cmd == "l":
                new_x = current_x + dx
                new_y = current_y + dy
            else:
                new_x = dx
                new_y = dy
            seg_dx = new_x - current_x
            seg_dy = new_y - current_y
            angle = math.degrees(math.atan2(seg_dy, seg_dx))
            for j in range(1, num_points + 1):
                t = j / num_points
                points.append(PathPoint(
                    x=current_x + seg_dx * t,
                    y=current_y + seg_dy * t,
                    angle=angle,
                ))
            current_x, current_y = new_x, new_y
            i += 3
        elif cmd in ("C", "c"):
            # 三次贝塞尔：C x1 y1 x2 y2 x y
            raw_x1, raw_y1 = float(parts[i + 1]), float(parts[i + 2])
            raw_x2, raw_y2 = float(parts[i + 3]), float(parts[i + 4])
            raw_ex, raw_ey = float(parts[i + 5]), float(parts[i + 6])
            if cmd == "c":
                x1, y1 = current_x + raw_x1, current_y + raw_y1
                x2, y2 = current_x + raw_x2, current_y + raw_y2
                ex, ey = current_x + raw_ex, current_y + raw_ey
            else:
                x1, y1, x2, y2, ex, ey = raw_x1, raw_y1, raw_x2, raw_y2, raw_ex, raw_ey
            for j in range(1, num_points + 1):
                t = j / num_points
                mt = 1 - t
                x = mt**3 * current_x + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * ex
                y = mt**3 * current_y + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * ey
                dx_dt = 3 * mt**2 * (x1 - current_x) + 6 * mt * t * (x2 - x1) + 3 * t**2 * (ex - x2)
                dy_dt = 3 * mt**2 * (y1 - current_y) + 6 * mt * t * (y2 - y1) + 3 * t**2 * (ey - y2)
                angle = math.degrees(math.atan2(dy_dt, dx_dt))
                points.append(PathPoint(x=x, y=y, angle=angle))
            current_x, current_y = ex, ey
            i += 7
        elif cmd in ("Q", "q"):
            # 二次贝塞尔：Q x1 y1 x y
            raw_x1, raw_y1 = float(parts[i + 1]), float(parts[i + 2])
            raw_ex, raw_ey = float(parts[i + 3]), float(parts[i + 4])
            if cmd == "q":
                x1, y1 = current_x + raw_x1, current_y + raw_y1
                ex, ey = current_x + raw_ex, current_y + raw_ey
            else:
                x1, y1, ex, ey = raw_x1, raw_y1, raw_ex, raw_ey
            for j in range(1, num_points + 1):
                t = j / num_points
                mt = 1 - t
                x = mt**2 * current_x + 2 * mt * t * x1 + t**2 * ex
                y = mt**2 * current_y + 2 * mt * t * y1 + t**2 * ey
                dx_dt = 2 * mt * (x1 - current_x) + 2 * t * (ex - x1)
                dy_dt = 2 * mt * (y1 - current_y) + 2 * t * (ey - y1)
                angle = math.degrees(math.atan2(dy_dt, dx_dt))
                points.append(PathPoint(x=x, y=y, angle=angle))
            current_x, current_y = ex, ey
            i += 5
        else:
            i += 1

    return points


def parse_svg_path_struct(path_data: str) -> list[dict]:
    """解析 SVG 路径为结构化节点列表（用于自由形状渲染）

    返回节点列表，每个节点格式：
        {"type": "move"|"line"|"cubic"|"quad", "points": [(x,y), ...]}
    末尾如有 Z/z 命令则追加 {"type": "close"} 节点。

    Args:
        path_data: SVG 路径字符串
    Returns:
        结构化节点列表
    """
    nodes: list[dict] = []
    parts = path_data.replace(",", " ").split()
    cx, cy = 0.0, 0.0
    i = 0

    while i < len(parts):
        cmd = parts[i]
        if cmd in ("M", "m"):
            dx, dy = float(parts[i + 1]), float(parts[i + 2])
            if cmd == "m":
                cx, cy = cx + dx, cy + dy
            else:
                cx, cy = dx, dy
            nodes.append({"type": "move", "points": [(cx, cy)]})
            i += 3
        elif cmd in ("L", "l"):
            dx, dy = float(parts[i + 1]), float(parts[i + 2])
            if cmd == "l":
                cx, cy = cx + dx, cy + dy
            else:
                cx, cy = dx, dy
            nodes.append({"type": "line", "points": [(cx, cy)]})
            i += 3
        elif cmd in ("C", "c"):
            rx1, ry1 = float(parts[i + 1]), float(parts[i + 2])
            rx2, ry2 = float(parts[i + 3]), float(parts[i + 4])
            rex, rey = float(parts[i + 5]), float(parts[i + 6])
            if cmd == "c":
                x1, y1 = cx + rx1, cy + ry1
                x2, y2 = cx + rx2, cy + ry2
                cx, cy = cx + rex, cy + rey
            else:
                x1, y1 = rx1, ry1
                x2, y2 = rx2, ry2
                cx, cy = rex, rey
            nodes.append({"type": "cubic", "points": [(x1, y1), (x2, y2), (cx, cy)]})
            i += 7
        elif cmd in ("Q", "q"):
            rx1, ry1 = float(parts[i + 1]), float(parts[i + 2])
            rex, rey = float(parts[i + 3]), float(parts[i + 4])
            if cmd == "q":
                x1, y1 = cx + rx1, cy + ry1
                cx, cy = cx + rex, cy + rey
            else:
                x1, y1 = rx1, ry1
                cx, cy = rex, rey
            nodes.append({"type": "quad", "points": [(x1, y1), (cx, cy)]})
            i += 5
        elif cmd in ("Z", "z"):
            nodes.append({"type": "close"})
            i += 1
        else:
            i += 1

    return nodes


# ============================================================
# 路径文字布局
# ============================================================

@dataclass
class CharPlacement:
    """单个字符的放置信息"""
    char: str
    x: float       # 中心 x（mm）
    y: float       # 中心 y（mm）
    rotation: float  # 旋转角度（度）
    width: float   # 字符宽度（mm）


def layout_chars_on_path(
    text: str,
    path_points: list[PathPoint],
    font_size: float = 14.0,
    char_spacing: float = 0.0,
) -> list[CharPlacement]:
    """将文字沿路径排列

    Args:
        text: 文本内容
        path_points: 路径点列表
        font_size: 字号（pt，用于估算字符宽度）
        char_spacing: 额外字符间距（mm）

    Returns:
        每个字符的放置信息
    """
    if not text or not path_points:
        return []

    # 估算字符宽度（mm）
    char_width_mm = font_size * 0.35  # pt → mm 近似
    total_char_width = char_width_mm + char_spacing

    # 计算路径总长度
    total_path_length = 0.0
    for i in range(1, len(path_points)):
        dx = path_points[i].x - path_points[i - 1].x
        dy = path_points[i].y - path_points[i - 1].y
        total_path_length += math.sqrt(dx * dx + dy * dy)

    # 计算文本总宽度
    text_width = total_char_width * len(text)

    # 居中偏移
    start_offset = max(0, (total_path_length - text_width) / 2)

    placements = []
    current_offset = start_offset
    point_idx = 0
    segment_length = 0.0
    accumulated = 0.0

    for char in text:
        # 找到当前偏移对应的路径点
        target = current_offset
        accumulated = 0.0

        for i in range(1, len(path_points)):
            dx = path_points[i].x - path_points[i - 1].x
            dy = path_points[i].y - path_points[i - 1].y
            seg_len = math.sqrt(dx * dx + dy * dy)

            if accumulated + seg_len >= target:
                # 在这个段内
                t = (target - accumulated) / seg_len if seg_len > 0 else 0
                x = path_points[i - 1].x + dx * t
                y = path_points[i - 1].y + dy * t
                angle = path_points[i].angle
                placements.append(CharPlacement(
                    char=char, x=x, y=y, rotation=angle, width=char_width_mm,
                ))
                break
            accumulated += seg_len

        current_offset += total_char_width

    return placements


# ============================================================
# 渲染器适配
# ============================================================

def to_html_svg(text: str, config: PathTextConfig, font_size: float = 14.0) -> str:
    """生成 HTML SVG textPath 代码

    Args:
        text: 文本内容
        config: 路径配置
        font_size: 字号

    Returns:
        SVG 代码字符串
    """
    if config.path_type == "arc":
        # 生成弧线 SVG 路径
        r = config.radius
        start_rad = math.radians(config.start_angle)
        end_rad = math.radians(config.end_angle)
        x1 = r * math.cos(start_rad)
        y1 = r * math.sin(start_rad)
        x2 = r * math.cos(end_rad)
        y2 = r * math.sin(end_rad)
        large_arc = 1 if abs(config.end_angle - config.start_angle) > 180 else 0
        path_d = f"M {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2}"
    elif config.path_type == "wave":
        # 简化波浪为二次贝塞尔
        wl = config.wavelength
        amp = config.amplitude
        path_d = f"M 0 0 Q {wl/4} {-amp} {wl/2} 0 Q {wl*3/4} {amp} {wl} 0"
    else:
        path_d = config.custom_path or "M 0 0 L 100 0"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="-150 -100 300 200">
  <defs>
    <path id="textPath" d="{path_d}" fill="none"/>
  </defs>
  <text font-size="{font_size}" fill="#333">
    <textPath href="#textPath" startOffset="50%" text-anchor="middle">{text}</textPath>
  </text>
</svg>'''


def to_pptx_placements(
    text: str, config: PathTextConfig, font_size: float = 14.0,
) -> list[CharPlacement]:
    """生成 PPTX 路径文字放置信息

    将路径文字转换为独立文本框的列表，
    每个文本框包含一个旋转后的字符。

    Returns:
        字符放置列表
    """
    if config.path_type in PATH_TYPE_TO_PPTX_PRESET:
        # 标准预设路径：用弧线近似生成字符位置（供逐字符模式备用）
        if config.path_type in ("arc", "arch_up"):
            points = generate_arc_points(
                config.radius, config.start_angle, config.end_angle,
            )
        elif config.path_type == "wave":
            points = generate_wave_points(
                config.amplitude, config.wavelength, config.wavelength * 2,
            )
        else:
            # 其他预设：用弧线近似
            points = generate_arc_points(
                config.radius, config.start_angle, config.end_angle,
            )
    elif config.custom_path:
        points = parse_svg_path(config.custom_path)
    else:
        return []

    return layout_chars_on_path(text, points, font_size, config.char_spacing)
