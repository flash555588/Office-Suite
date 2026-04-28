"""资源解析器 — 将 IR 节点中的资源引用解析为实际资源

架构位置：
  IR 节点 (source="mcp__unsplash?query=nature")
    → [本文件] ResourceResolver.resolve()
    → ResourceResult (bytes/Path/None)
    → 渲染器使用

降级链（4 级）：
  1. 缓存命中 → 直接返回
  2. Provider 获取 → 成功则写入缓存
  3. 占位符标记 → fallback_used=True
  4. 空结果 + warning 日志

重试策略：
  - 可重试错误（网络超时、连接拒绝）自动重试 max_retries 次
  - 不可重试错误（资源不存在、权限不足）直接失败
  - 重试间隔：base_delay * 2^attempt（指数退避）
"""

import logging
import json
import time
from pathlib import Path
from typing import Any

from .registry import ResourceRegistry, ResourceResult
from .cache import ResourceCache
from .providers.local_provider import LocalFileProvider
from .providers.inline_provider import InlineDataProvider

logger = logging.getLogger(__name__)

# 可重试的错误关键词
RETRYABLE_ERRORS = frozenset([
    "timeout", "timed out", "connection refused", "connection reset",
    "connection error", "network", "temporary", "503", "502", "429",
    "rate limit", "throttle", "retry",
])


def is_retryable(error: str) -> bool:
    """判断错误是否可重试"""
    error_lower = error.lower()
    return any(kw in error_lower for kw in RETRYABLE_ERRORS)


def create_default_registry() -> ResourceRegistry:
    """创建默认的资源注册表（内置 Provider）"""
    registry = ResourceRegistry()
    registry.register(LocalFileProvider())
    registry.register(InlineDataProvider())
    return registry


class ResourceResolver:
    """资源解析器 — 在渲染前解析 IR 节点中的资源引用

    使用方式：
        resolver = ResourceResolver()
        result = resolver.resolve("file://logo.png")
        result = resolver.resolve({"mcp__unsplash": {"query": "nature"}})
    """

    def __init__(
        self,
        registry: ResourceRegistry | None = None,
        cache: ResourceCache | None = None,
        max_retries: int = 2,
        base_delay: float = 0.1,
    ):
        self.registry = registry or create_default_registry()
        self.cache = cache or ResourceCache()
        self.max_retries = max_retries
        self.base_delay = base_delay

    def resolve(self, source: str | dict, **kwargs) -> ResourceResult:
        """解析资源引用

        降级链：
        1. 缓存命中 → 直接返回（cache_hit=True）
        2. Provider 获取成功 → 写入缓存，返回结果
        3. Provider 获取失败 → 返回占位符（fallback_used=True）
        4. source 为 None → 立即返回失败结果 + warning 日志

        重试：
        - 可重试错误自动重试 max_retries 次（指数退避）
        - 不可重试错误直接失败
        """
        if source is None:
            logger.warning("[ResourceResolver] source 为 None，跳过解析")
            return ResourceResult(
                success=False,
                fallback_used=True,
                fallback_reason="source 为 None",
            )

        # 生成缓存键
        # 标量类型直接 str()；结构化数据用 json.dumps(sort_keys=True) 保证键顺序无关
        if isinstance(source, (str, int, float, bool)):
            cache_key = str(source)
        else:
            try:
                cache_key = json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            except TypeError:
                cache_key = str(source)

        # 若 kwargs 非空，将其追加到 key 中避免同 source 不同选项的碰撞
        if kwargs:
            try:
                kwargs_part = json.dumps(kwargs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                cache_key = f"{cache_key}|{kwargs_part}"
            except TypeError:
                cache_key = f"{cache_key}|{str(kwargs)}"

        # 1. 缓存命中
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("[ResourceResolver] 缓存命中: %s", cache_key)
            return cached

        # 2. Provider 获取（带重试）
        result = self._fetch_with_retry(source, **kwargs)

        if result.success:
            # 写入缓存
            self.cache.put(cache_key, result)
            logger.debug("[ResourceResolver] 资源已获取并缓存: %s", cache_key)
        else:
            # 3. 降级：占位符
            result.fallback_used = True
            if not result.fallback_reason:
                result.fallback_reason = "资源获取失败"
            # 4. warning 日志
            logger.warning(
                "[ResourceResolver] 资源获取失败，使用占位符: %s — %s",
                cache_key,
                result.fallback_reason,
            )

        return result

    def _fetch_with_retry(self, source: str | dict, **kwargs) -> ResourceResult:
        """带重试的资源获取

        可重试错误：网络超时、连接拒绝、限流等
        不可重试错误：资源不存在、参数错误、未配置 caller
        """
        last_result = None

        for attempt in range(self.max_retries + 1):
            result = self.registry.resolve(source, **kwargs)

            if result.success:
                return result

            last_result = result

            # 判断是否可重试
            if not is_retryable(result.error):
                logger.debug(
                    "[ResourceResolver] 不可重试错误，直接失败: %s",
                    result.error,
                )
                return result

            # 还有重试次数
            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt)
                logger.debug(
                    "[ResourceResolver] 重试 %d/%d，等待 %.2fs: %s",
                    attempt + 1,
                    self.max_retries,
                    delay,
                    result.error,
                )
                time.sleep(delay)

        return last_result

    def resolve_for_image(self, source: str | dict, base_dir: Path | None = None) -> ResourceResult:
        """专门解析图片资源"""
        return self.resolve(source, base_dir=base_dir or Path.cwd())

    @property
    def cache_stats(self):
        """返回缓存统计信息"""
        return self.cache.stats
