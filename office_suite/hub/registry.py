"""资源提供者注册表 — 统一管理所有资源来源

资源引用语法（设计方案第五章）：
  mcp__unsplash   → MCP 服务器获取
  ai__generate    → AI 生成
  skill__xxx      → 其他 Skill 产出
  file://path     → 本地文件
  data:...        → 内联数据

每个 Provider 注册自己能处理的 source 前缀，
Hub 解析 source 时按注册顺序查找匹配的 Provider。
"""

from dataclasses import dataclass, field
from typing import Any, Protocol
from pathlib import Path


class ResourceProvider(Protocol):
    """资源提供者接口"""
    name: str
    prefixes: list[str]  # 支持的 source 前缀

    def can_handle(self, source: str | dict) -> bool:
        """判断是否能处理该资源引用"""
        ...

    def fetch(self, source: str | dict, **kwargs) -> "ResourceResult":
        """获取资源"""
        ...


@dataclass
class ResourceResult:
    """资源获取结果"""
    success: bool
    data: Any = None              # 成功时的资源数据（bytes / Path / str）
    mime_type: str = ""           # MIME 类型
    source_used: str = ""         # 实际使用的 source
    fallback_used: bool = False   # 是否使用了降级
    fallback_reason: str = ""     # 降级原因
    error: str = ""               # 失败时的错误信息


class ResourceRegistry:
    """资源提供者注册表"""

    def __init__(self):
        self._providers: list[ResourceProvider] = []

    def register(self, provider: ResourceProvider):
        """注册资源提供者"""
        self._providers.append(provider)

    def resolve(self, source: str | dict, **kwargs) -> ResourceResult:
        """解析资源引用，返回获取结果

        降级策略链（设计方案第五章）：
        1. 主资源获取
        2. 缓存中的历史版本
        3. 占位符资源（带标记，后续可替换）
        4. 空白占位 + 警告日志

        匹配逻辑：
        - can_handle 且 fetch 成功 → 直接返回
        - can_handle 但 fetch 失败 → 返回该失败结果（不继续尝试）
        - 无任何 provider 匹配 → 降级占位符
        """
        matched_any = False

        for provider in self._providers:
            if provider.can_handle(source):
                matched_any = True
                try:
                    result = provider.fetch(source, **kwargs)
                    return result
                except Exception as e:
                    # Provider 异常，包装为失败结果返回
                    return ResourceResult(
                        success=False,
                        fallback_used=True,
                        fallback_reason=f"Provider {provider.name} 异常: {e}",
                        error=str(e),
                    )

        # 无 Provider 匹配 → 降级到占位符
        return ResourceResult(
            success=False,
            fallback_used=True,
            fallback_reason=f"无 Provider 能处理资源: {source}",
            error=f"No provider matched for: {source}",
        )

    def list_providers(self) -> list[str]:
        """列出所有已注册的 Provider 名称"""
        return [p.name for p in self._providers]
