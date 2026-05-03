"""外部图片导入工具

当 AI 通过外部 skill（MiniMax MCP、web-access 等）获取到图片时，
将图片复制到项目产出目录，以便 DSL YAML 引用。

用法：
    from office_suite.ai.media import import_media, collect_dsl_media

    # 导入单张图片
    dest = import_media("/tmp/generated_cover.jpg", "output/pages/")

    # 从 DSL 中自动收集所有外部图片
    collect_dsl_media("deck.yml", "output/pages/")
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# 支持的图片扩展名
IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".tif",
})

# URL 正则
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_url(source: str) -> bool:
    """判断是否为 URL"""
    return bool(_URL_RE.match(source))


def is_image_file(path: str | Path) -> bool:
    """判断是否为图片文件"""
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def _safe_filename(source: str, original_name: str | None = None) -> str:
    """生成安全的文件名

    优先使用 original_name；如果 source 是 URL 但没有可读文件名，
    则用 hash 生成唯一名称。
    """
    if original_name:
        return original_name

    parsed = urlparse(source)
    name = Path(parsed.path).name if parsed.path else ""
    if name and "." in name:
        return name

    # fallback: hash-based name
    h = hashlib.md5(source.encode()).hexdigest()[:12]
    return f"img_{h}.jpg"


def import_media(
    source: str | Path,
    target_dir: str | Path,
    *,
    filename: str | None = None,
    overwrite: bool = False,
) -> Path:
    """将外部图片复制到目标目录

    支持：
    - 本地文件路径（绝对/相对）
    - URL（http/https）—— 通过 urllib 下载
    - 已在目标目录中的文件 —— 直接返回路径（跳过复制）

    Args:
        source: 图片来源（路径或 URL）
        target_dir: 目标目录
        filename: 可选，指定保存的文件名
        overwrite: 是否覆盖已存在的文件

    Returns:
        目标文件的绝对路径

    Raises:
        FileNotFoundError: 本地源文件不存在
        ValueError: 不支持的来源类型
        RuntimeError: 下载失败
    """
    source_str = str(source)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 判断来源类型
    if is_url(source_str):
        return _download_url(source_str, target_dir, filename, overwrite)
    else:
        return _copy_local(Path(source_str), target_dir, filename, overwrite)


def _copy_local(
    src: Path,
    target_dir: Path,
    filename: str | None,
    overwrite: bool,
) -> Path:
    """复制本地文件到目标目录"""
    src = src.resolve()
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")
    if not src.is_file():
        raise ValueError(f"源路径不是文件: {src}")

    dest = target_dir / _safe_filename(str(src), filename or src.name)

    # 如果源已在目标目录中，直接返回
    if src.parent.resolve() == target_dir.resolve() and src.name == dest.name:
        logger.info("图片已在目标目录中，跳过复制: %s", src.name)
        return src

    if dest.exists() and not overwrite:
        logger.info("目标文件已存在，跳过: %s", dest.name)
        return dest.resolve()

    shutil.copy2(src, dest)
    logger.info("已复制: %s -> %s", src.name, dest)
    return dest.resolve()


def _download_url(
    url: str,
    target_dir: Path,
    filename: str | None,
    overwrite: bool,
) -> Path:
    """从 URL 下载图片到目标目录"""
    import urllib.request
    import urllib.error

    dest = target_dir / _safe_filename(url, filename)

    if dest.exists() and not overwrite:
        logger.info("目标文件已存在，跳过下载: %s", dest.name)
        return dest.resolve()

    try:
        urllib.request.urlretrieve(url, dest)
        logger.info("已下载: %s -> %s", url[:80], dest)
        return dest.resolve()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        if dest.exists():
            dest.unlink()
        raise RuntimeError(f"下载失败 ({url[:60]}): {exc}") from exc


def import_media_batch(
    sources: dict[str, str | Path],
    target_dir: str | Path,
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    """批量导入图片

    Args:
        sources: {语义名: 来源路径/URL} 映射
        target_dir: 目标目录
        overwrite: 是否覆盖

    Returns:
        {语义名: 目标路径} 映射
    """
    results: dict[str, Path] = {}
    for name, source in sources.items():
        try:
            dest = import_media(source, target_dir, filename=f"{name}{Path(str(source)).suffix}", overwrite=overwrite)
            results[name] = dest
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            logger.warning("跳过 %s: %s", name, exc)
    return results


def collect_dsl_media(
    dsl_path: str | Path,
    target_dir: str | Path,
    *,
    overwrite: bool = False,
) -> list[Path]:
    """从 DSL YAML 中提取所有外部图片引用并复制到目标目录

    扫描 DSL 中所有 source/src 字段，对于指向外部位置（不在 target_dir 中）
    的图片，复制到 target_dir。

    支持 deck.yml 的 pages: 引用——会递归扫描所有页面文件中的图片。

    Args:
        dsl_path: DSL YAML 文件路径（可以是 deck.yml 或单页 YAML）
        target_dir: 目标目录（通常是页面 YAML 文件所在目录）
        overwrite: 是否覆盖

    Returns:
        已导入的文件路径列表
    """
    import yaml

    dsl_path = Path(dsl_path).resolve()
    target_dir = Path(target_dir).resolve()

    with open(dsl_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return []

    # 递归收集所有图片引用（包括 pages 引用的子文件）
    all_refs = _collect_all_refs(raw, dsl_path.parent)
    imported: list[Path] = []

    for ref_path, base_dir in all_refs:
        if is_url(ref_path):
            try:
                dest = _download_url(ref_path, target_dir, None, overwrite)
                imported.append(dest)
            except RuntimeError as exc:
                logger.warning("跳过 URL 图片: %s", exc)
        else:
            src = Path(ref_path)
            if not src.is_absolute():
                src = (base_dir / src).resolve()

            if src.exists() and src.parent.resolve() != target_dir:
                try:
                    dest = _copy_local(src, target_dir, None, overwrite)
                    imported.append(dest)
                except (FileNotFoundError, ValueError) as exc:
                    logger.warning("跳过本地图片: %s", exc)
            elif src.exists():
                imported.append(src)

    if imported:
        logger.info("共导入 %d 张图片到 %s", len(imported), target_dir)
    else:
        logger.info("未发现需要导入的外部图片")

    return imported


def _collect_image_refs(obj: object) -> list[str]:
    """递归收集 dict/list 中所有 source/src 字段的值"""
    refs: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in ("source", "src") and isinstance(val, str) and val.strip():
                refs.append(val.strip())
            else:
                refs.extend(_collect_image_refs(val))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(_collect_image_refs(item))
    return refs


def _collect_all_refs(
    raw: dict, base_dir: Path
) -> list[tuple[str, Path]]:
    """递归收集所有图片引用，跟随 pages: 子文件引用

    Returns:
        [(image_ref, base_dir)] 列表，base_dir 为该引用所在的目录
    """
    import yaml

    results: list[tuple[str, Path]] = []

    # 收集当前文件中的图片引用
    for ref in _collect_image_refs(raw):
        results.append((ref, base_dir))

    # 跟踪 pages: 子文件引用
    page_refs = raw.get("pages") or raw.get("slides") or []
    for page_ref in page_refs:
        if isinstance(page_ref, str):
            page_path = (base_dir / page_ref).resolve()
            if page_path.exists():
                try:
                    with open(page_path, encoding="utf-8") as f:
                        page_raw = yaml.safe_load(f)
                    if page_raw:
                        for ref in _collect_image_refs(page_raw):
                            results.append((ref, page_path.parent))
                except Exception as exc:
                    logger.warning("跳过页面文件 %s: %s", page_path, exc)
        elif isinstance(page_ref, dict):
            for ref in _collect_image_refs(page_ref):
                results.append((ref, base_dir))

    return results


def update_dsl_image_paths(
    dsl_path: str | Path,
    target_dir: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """导入图片并更新 DSL 中的路径引用

    将 DSL 中所有外部图片引用复制到 target_dir，并将 source/src
    路径更新为相对于各自 YAML 文件目录的路径。

    支持 deck.yml 的 pages: 引用——会递归扫描并更新所有页面文件。

    Args:
        dsl_path: DSL YAML 文件路径（可以是 deck.yml 或单页 YAML）
        target_dir: 目标目录
        overwrite: 是否覆盖

    Returns:
        更新后的 DSL 文件路径
    """
    import yaml

    dsl_path = Path(dsl_path).resolve()
    target_dir = Path(target_dir).resolve()

    with open(dsl_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return dsl_path

    # 判断是 deck.yml（有 pages 引用）还是单页 YAML
    page_refs = raw.get("pages") or raw.get("slides") or []
    has_pages = any(isinstance(r, str) for r in page_refs)

    if has_pages:
        # deck.yml 模式：递归更新所有页面文件
        total_updated = 0
        for page_ref in page_refs:
            if not isinstance(page_ref, str):
                continue
            page_path = (dsl_path.parent / page_ref).resolve()
            if page_path.exists():
                count = _update_single_file(page_path, target_dir, overwrite)
                total_updated += count
        logger.info("共更新 %d 处图片路径（跨 %d 个页面文件）", total_updated, len([r for r in page_refs if isinstance(r, str)]))
    else:
        # 单页模式：直接更新
        count = _update_single_file(dsl_path, target_dir, overwrite)
        logger.info("已更新 %d 处图片路径引用", count)

    return dsl_path


def _update_single_file(
    file_path: Path,
    target_dir: Path,
    overwrite: bool,
) -> int:
    """更新单个 YAML 文件中的图片路径引用

    Returns:
        更新的路径数量
    """
    import yaml

    with open(file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return 0

    image_refs = _collect_image_refs(raw)
    path_map: dict[str, str] = {}

    for ref_path in image_refs:
        if is_url(ref_path):
            try:
                dest = _download_url(ref_path, target_dir, None, overwrite)
                path_map[ref_path] = dest.name
            except RuntimeError:
                pass
        else:
            src = Path(ref_path)
            if not src.is_absolute():
                src = (file_path.parent / src).resolve()
            if src.exists() and src.parent.resolve() != target_dir:
                try:
                    dest = _copy_local(src, target_dir, None, overwrite)
                    path_map[ref_path] = dest.name
                except (FileNotFoundError, ValueError):
                    pass

    if not path_map:
        return 0

    _replace_image_refs(raw, path_map)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    logger.info("已更新 %s: %d 处路径", file_path.name, len(path_map))
    return len(path_map)


def _replace_image_refs(obj: object, path_map: dict[str, str]) -> None:
    """递归替换 dict/list 中的图片路径"""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in ("source", "src") and isinstance(val, str):
                stripped = val.strip()
                if stripped in path_map:
                    obj[key] = path_map[stripped]
            else:
                _replace_image_refs(val, path_map)
    elif isinstance(obj, list):
        for item in obj:
            _replace_image_refs(item, path_map)


__all__ = [
    "import_media",
    "import_media_batch",
    "collect_dsl_media",
    "update_dsl_image_paths",
    "is_url",
    "is_image_file",
]
