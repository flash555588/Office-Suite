"""P5 测试套件：Hub 与资源系统完善

覆盖：
1. ResourceCache 专用测试（hit/miss/TTL/LRU/stats）
2. Fake Provider 测试（MCP/AI/Skill）
3. MCPProvider + FakeMCPCaller 集成测试
4. AIProvider + FakeAICaller 集成测试
5. SkillProvider + FakeSkillExecutor 集成测试
6. 重试机制测试
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from office_suite.hub.registry import ResourceRegistry, ResourceResult
from office_suite.hub.resolver import ResourceResolver, create_default_registry, is_retryable
from office_suite.hub.cache import ResourceCache, CacheStats
from office_suite.hub.providers.local_provider import LocalFileProvider
from office_suite.hub.providers.inline_provider import InlineDataProvider
from office_suite.hub.providers.mcp_provider import MCPProvider
from office_suite.hub.providers.ai_provider import AIProvider, AIRequest
from office_suite.hub.providers.skill_provider import SkillProvider, SkillDef
from office_suite.hub.providers.fake_providers import FakeMCPCaller, FakeAICaller, FakeSkillExecutor


_pass_count = 0
_fail_count = 0


def check(name: str, condition: bool, detail: str = ""):
    global _pass_count, _fail_count
    if condition:
        _pass_count += 1
        print(f"  PASS  {name}")
    else:
        _fail_count += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


def section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


# ============================================================
# 1. ResourceCache 专用测试
# ============================================================

def test_cache_hit_miss():
    section("1.1 Cache hit/miss")

    cache = ResourceCache(max_size=8)

    # miss
    result = cache.get("key1")
    check("未命中返回 None", result is None)
    check("miss 计数 +1", cache.stats.misses == 1)

    # put + hit
    cache.put("key1", "value1", mime_type="text/plain")
    result = cache.get("key1")
    check("命中返回数据", result == "value1")
    check("hit 计数 +1", cache.stats.hits == 1)
    check("total = hits + misses", cache.stats.total == 2)
    check("hit_rate = 0.5", abs(cache.stats.hit_rate - 0.5) < 0.01)


def test_cache_ttl():
    section("1.2 Cache TTL 过期")

    cache = ResourceCache()

    # TTL=0.05s 的条目
    cache.put("fast", "data", ttl=0.05)
    check("未过期时可命中", cache.get("fast") == "data")

    time.sleep(0.06)
    check("过期后 miss", cache.get("fast") is None)
    check("过期条目不在 __contains__", "fast" not in cache)


def test_cache_lru_eviction():
    section("1.3 Cache LRU 驱逐")

    cache = ResourceCache(max_size=3)

    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    # 访问 a 使其变为最近使用
    cache.get("a")

    # 添加 d，应驱逐最久未使用的 b
    cache.put("d", 4)

    check("a 仍存在", cache.get("a") == 1)
    check("b 被驱逐", cache.get("b") is None)
    check("c 仍存在", cache.get("c") == 3)
    check("d 已加入", cache.get("d") == 4)
    check("驱逐计数 = 1", cache.stats.evictions == 1)


def test_cache_invalidate():
    section("1.4 Cache 手动失效")

    cache = ResourceCache()
    cache.put("k", "v")
    check("存在", cache.get("k") == "v")

    cache.invalidate("k")
    check("失效后 miss", cache.get("k") is None)

    cache.put("x", 1)
    cache.put("y", 2)
    cache.clear()
    check("clear 后 len=0", len(cache) == 0)


def test_cache_contains():
    section("1.5 Cache __contains__")

    cache = ResourceCache()
    cache.put("item", "val", ttl=0.05)
    check("未过期在 __contains__", "item" in cache)

    time.sleep(0.06)
    check("过期后不在 __contains__", "item" not in cache)
    check("不存在的 key", "ghost" not in cache)


def test_cache_update_existing():
    section("1.6 Cache 更新已有 key")

    cache = ResourceCache(max_size=2)
    cache.put("k", "old")
    cache.put("k", "new", mime_type="text/html")
    check("更新后返回新值", cache.get("k") == "new")
    check("长度不变", len(cache) == 1)


# ============================================================
# 2. Fake Provider 测试
# ============================================================

def test_fake_mcp_caller():
    section("2.1 FakeMCPCaller")

    caller = FakeMCPCaller()
    result = caller({"_server": "unsplash", "query": "nature"})
    check("默认返回 success", result.success)
    check("返回 bytes 数据", isinstance(result.data, bytes))
    check("call_count = 1", caller.call_count == 1)

    # 自定义响应
    custom = ResourceResult(success=True, data="custom", mime_type="text/plain")
    caller.register("pexels", custom)
    result2 = caller({"_server": "pexels"})
    check("自定义响应", result2.data == "custom")


def test_fake_ai_caller():
    section("2.2 FakeAICaller")

    caller = FakeAICaller()
    req = AIRequest(prompt="test", model="auto")
    result = caller(req)
    check("默认返回 success", result.success)
    check("默认返回文本", result.data == "fake AI generated text")
    check("call_count = 1", caller.call_count == 1)

    # 自定义响应
    custom = ResourceResult(success=True, data=b"img_bytes", mime_type="image/png")
    caller.set_response(custom)
    result2 = caller(AIRequest(prompt="image"))
    check("自定义响应", result2.data == b"img_bytes")


def test_fake_skill_executor():
    section("2.3 FakeSkillExecutor")

    executor = FakeSkillExecutor()
    result = executor({"data": [1, 2, 3]})
    check("默认返回 success", result.success)
    check("call_count = 1", executor.call_count == 1)

    # 失败响应
    fail = ResourceResult(success=False, error="skill failed")
    executor.set_response(fail)
    result2 = executor({})
    check("失败响应", not result2.success)


# ============================================================
# 3. MCPProvider + Fake Caller 集成测试
# ============================================================

def test_mcp_provider_with_fake():
    section("3. MCPProvider + FakeMCPCaller")

    provider = MCPProvider()
    caller = FakeMCPCaller()
    provider.set_caller("unsplash", caller)

    # can_handle
    check("mcp__unsplash 可处理", provider.can_handle("mcp__unsplash"))
    check("mcp:pexels 可处理", provider.can_handle("mcp:pexels"))
    check("dict 可处理", provider.can_handle({"mcp": "unsplash"}))
    check("普通字符串不可处理", not provider.can_handle("file://test"))

    # fetch 字符串
    result = provider.fetch("mcp__unsplash", query="nature")
    check("fetch success", result.success)
    check("caller 被调用", caller.call_count == 1)

    # fetch dict
    result2 = provider.fetch({"mcp": "unsplash", "query": "city"})
    check("dict fetch success", result2.success)

    # 未注册的 caller
    result3 = provider.fetch("mcp__unknown_server")
    check("未注册 caller 失败", not result3.success)
    check("有 fallback_reason", result3.fallback_reason != "")

    # list_servers
    check("list_servers", provider.list_servers() == ["unsplash"])


# ============================================================
# 4. AIProvider + Fake Caller 集成测试
# ============================================================

def test_ai_provider_with_fake():
    section("4. AIProvider + FakeAICaller")

    provider = AIProvider()
    caller = FakeAICaller()
    provider.set_caller("text", caller)

    # can_handle
    check("ai__text 可处理", provider.can_handle("ai__text"))
    check("ai:image 可处理", provider.can_handle("ai:image"))
    check("dict 可处理", provider.can_handle({"ai": "text"}))
    check("普通字符串不可处理", not provider.can_handle("file://test"))

    # fetch 字符串
    result = provider.fetch("ai__text", prompt="write something")
    check("fetch success", result.success)
    check("caller 被调用", caller.call_count == 1)

    # fetch dict
    result2 = provider.fetch({"ai": "text", "prompt": "hello"})
    check("dict fetch success", result2.success)

    # 未注册的能力
    result3 = provider.fetch("ai__image", prompt="a cat")
    check("未注册能力失败", not result3.success)
    check("有 fallback_reason", result3.fallback_reason != "")

    # 推断能力
    check("推断 image", provider._infer_capability(AIRequest(prompt="a photo of cat")) == "image")
    check("推断 chart", provider._infer_capability(AIRequest(prompt="bar chart")) == "chart")
    check("推断 icon", provider._infer_capability(AIRequest(prompt="logo design")) == "icon")
    check("推断 text", provider._infer_capability(AIRequest(prompt="write a report")) == "text")

    # list_capabilities
    check("list_capabilities", provider.list_capabilities() == ["text"])


# ============================================================
# 5. SkillProvider + Fake Executor 集成测试
# ============================================================

def test_skill_provider_with_fake():
    section("5. SkillProvider + FakeSkillExecutor")

    provider = SkillProvider()
    executor = FakeSkillExecutor()

    # 注册 skill
    skill = SkillDef(name="matplotlib", description="Chart generator", capabilities=["chart"])
    provider.register_skill(skill)
    provider.set_executor("matplotlib", executor)

    # can_handle
    check("skill__matplotlib 可处理", provider.can_handle("skill__matplotlib"))
    check("skill:chart 可处理", provider.can_handle("skill:chart"))
    check("dict 可处理", provider.can_handle({"skill": "matplotlib"}))
    check("普通字符串不可处理", not provider.can_handle("file://test"))

    # fetch
    result = provider.fetch("skill__matplotlib", data={"values": [1, 2, 3]})
    check("fetch success", result.success)
    check("executor 被调用", executor.call_count == 1)

    # 未注册的 skill
    result2 = provider.fetch("skill__unknown")
    check("未注册 skill 失败", not result2.success)
    check("有 fallback_reason", "未注册" in result2.fallback_reason)

    # 注册但未设置 executor
    provider.register_skill(SkillDef(name="no_exec"))
    result3 = provider.fetch("skill__no_exec")
    check("无 executor 失败", not result3.success)

    # list/get skill
    check("list_skills 有 2 个", len(provider.list_skills()) == 2)
    check("get_skill 存在", provider.get_skill("matplotlib") is not None)
    check("get_skill 不存在", provider.get_skill("ghost") is None)


# ============================================================
# 6. 重试机制测试
# ============================================================

def test_retry_on_retryable_error():
    section("6.1 可重试错误自动重试")

    attempt_count = 0

    class FlakyProvider:
        name = "flaky"
        prefixes = ["flaky:"]

        def can_handle(self, source):
            return isinstance(source, str) and source.startswith("flaky:")

        def fetch(self, source, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                return ResourceResult(
                    success=False,
                    error="connection timeout",
                )
            return ResourceResult(success=True, data="recovered")

    registry = ResourceRegistry()
    registry.register(FlakyProvider())
    resolver = ResourceResolver(registry=registry, max_retries=3, base_delay=0.01)

    result = resolver.resolve("flaky:test")
    check("最终成功", result.success)
    check("重试了 2 次", attempt_count == 3)


def test_no_retry_on_non_retryable_error():
    section("6.2 不可重试错误直接失败")

    attempt_count = 0

    class FailProvider:
        name = "fail"
        prefixes = ["fail:"]

        def can_handle(self, source):
            return isinstance(source, str) and source.startswith("fail:")

        def fetch(self, source, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            return ResourceResult(
                success=False,
                error="resource not found",
            )

    registry = ResourceRegistry()
    registry.register(FailProvider())
    resolver = ResourceResolver(registry=registry, max_retries=3, base_delay=0.01)

    result = resolver.resolve("fail:test")
    check("不可重试错误直接失败", not result.success)
    check("只尝试 1 次", attempt_count == 1)


def test_retry_exhausted():
    section("6.3 重试次数耗尽")

    attempt_count = 0

    class AlwaysFailProvider:
        name = "always_fail"
        prefixes = ["af:"]

        def can_handle(self, source):
            return isinstance(source, str) and source.startswith("af:")

        def fetch(self, source, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            return ResourceResult(success=False, error="connection refused")

    registry = ResourceRegistry()
    registry.register(AlwaysFailProvider())
    resolver = ResourceResolver(registry=registry, max_retries=2, base_delay=0.01)

    result = resolver.resolve("af:test")
    check("重试耗尽后失败", not result.success)
    check("共尝试 3 次", attempt_count == 3)
    check("有 fallback_used", result.fallback_used)


def test_is_retryable():
    section("6.4 is_retryable 判断")

    check("timeout 可重试", is_retryable("connection timeout"))
    check("connection refused 可重试", is_retryable("Connection refused"))
    check("429 可重试", is_retryable("HTTP 429 rate limit"))
    check("503 可重试", is_retryable("Service unavailable 503"))
    check("not found 不可重试", not is_retryable("resource not found"))
    check("permission 不可重试", not is_retryable("permission denied"))
    check("空字符串不可重试", not is_retryable(""))


# ============================================================
# 7. Resolver + Fake Provider 集成测试
# ============================================================

def test_resolver_with_mcp_fake():
    section("7.1 Resolver + MCP Fake 集成")

    mcp = MCPProvider()
    caller = FakeMCPCaller()
    mcp.set_caller("unsplash", caller)

    registry = ResourceRegistry()
    registry.register(LocalFileProvider())
    registry.register(InlineDataProvider())
    registry.register(mcp)

    resolver = ResourceResolver(registry=registry, max_retries=0)

    # MCP 资源
    result = resolver.resolve("mcp__unsplash", query="nature")
    check("MCP 资源获取成功", result.success)
    check("caller 被调用", caller.call_count == 1)

    # 二次获取走缓存
    result2 = resolver.resolve("mcp__unsplash", query="nature")
    check("缓存命中", caller.call_count == 1)  # 不应再次调用


def test_resolver_fallback_with_fake():
    section("7.2 Resolver 降级链")

    mcp = MCPProvider()
    # 不设置 caller，MCP 会失败

    registry = ResourceRegistry()
    registry.register(mcp)

    resolver = ResourceResolver(registry=registry, max_retries=0)
    result = resolver.resolve("mcp__unsplash")
    check("无 caller 时降级", not result.success)
    check("fallback_used=True", result.fallback_used)
    check("有 fallback_reason", result.fallback_reason != "")


# ============================================================
# 8. 缓存键一致性测试
# ============================================================

def test_cache_key_consistency():
    section("8. 缓存键一致性")

    resolver = ResourceResolver()

    # dict 顺序无关
    r1 = resolver.resolve({"type": "chart", "values": [1, 2]})
    r2 = resolver.resolve({"values": [1, 2], "type": "chart"})
    # 两者都应失败（无 provider），但应走同一缓存路径
    check("dict 顺序无关（fallback 一致）", r1.fallback_used == r2.fallback_used)

    # kwargs 参与键生成
    cache = ResourceCache()
    cache.put("key|{\"a\":1}", "val1")
    cache.put("key|{\"b\":2}", "val2")
    check("不同 kwargs 不同键", cache.get("key|{\"a\":1}") == "val1")
    check("不同 kwargs 不同键 2", cache.get("key|{\"b\":2}") == "val2")


# ============================================================
# 9. 完整注册表测试
# ============================================================

def test_full_registry():
    section("9. 完整注册表（5 个 Provider）")

    mcp = MCPProvider()
    mcp.set_caller("test", FakeMCPCaller())
    ai = AIProvider()
    ai.set_caller("text", FakeAICaller())
    skill = SkillProvider()
    skill.register_skill(SkillDef(name="test"))
    skill.set_executor("test", FakeSkillExecutor())

    registry = ResourceRegistry()
    registry.register(LocalFileProvider())
    registry.register(InlineDataProvider())
    registry.register(mcp)
    registry.register(ai)
    registry.register(skill)

    providers = registry.list_providers()
    check("5 个 Provider 已注册", len(providers) == 5, f"got {len(providers)}")
    check("顺序正确", providers == ["local_file", "inline_data", "mcp", "ai", "skill"])

    # 各类型资源
    check("本地文件可解析", registry.resolve(str(PROJECT_ROOT / "tests")).success)
    check("内联数据可解析", registry.resolve("data:text/plain;base64,SGVsbG8=").success)
    check("MCP 可解析", registry.resolve("mcp__test").success)
    check("AI 可解析", registry.resolve("ai__text", prompt="hi").success)
    check("Skill 可解析", registry.resolve("skill__test").success)


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  Office Suite 4.0 — P5 Hub 与资源系统测试")
    print("=" * 60)

    # Cache 专用测试
    test_cache_hit_miss()
    test_cache_ttl()
    test_cache_lru_eviction()
    test_cache_invalidate()
    test_cache_contains()
    test_cache_update_existing()

    # Fake Provider 测试
    test_fake_mcp_caller()
    test_fake_ai_caller()
    test_fake_skill_executor()

    # MCP/AI/Skill + Fake 集成
    test_mcp_provider_with_fake()
    test_ai_provider_with_fake()
    test_skill_provider_with_fake()

    # 重试机制
    test_retry_on_retryable_error()
    test_no_retry_on_non_retryable_error()
    test_retry_exhausted()
    test_is_retryable()

    # Resolver 集成
    test_resolver_with_mcp_fake()
    test_resolver_fallback_with_fake()

    # 缓存键
    test_cache_key_consistency()

    # 完整注册表
    test_full_registry()

    print(f"\n{'=' * 60}")
    print(f"  结果:  PASS={_pass_count}  FAIL={_fail_count}")
    print(f"{'=' * 60}")

    return _fail_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
