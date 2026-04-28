"""Fake Provider 实现 — 用于确定性测试

不依赖网络，返回预设结果。
用于 MCP / AI / Skill provider 的单元测试和集成测试。
"""

from ..registry import ResourceResult


class FakeMCPCaller:
    """Fake MCP caller — 模拟 MCP 服务器响应"""

    def __init__(self, responses: dict[str, ResourceResult] | None = None):
        self._responses = responses or {}
        self._calls: list[dict] = []

    def register(self, server_name: str, response: ResourceResult):
        self._responses[server_name] = response

    def __call__(self, params: dict) -> ResourceResult:
        self._calls.append(params)
        server = params.get("_server", "")
        if server in self._responses:
            return self._responses[server]
        return ResourceResult(
            success=True,
            data=b"fake_mcp_image_bytes",
            mime_type="image/jpeg",
            source_used=f"mcp__{server}",
        )

    @property
    def call_count(self) -> int:
        return len(self._calls)


class FakeAICaller:
    """Fake AI caller — 模拟 AI 模型响应"""

    def __init__(self, response: ResourceResult | None = None):
        self._response = response
        self._calls: list[dict] = []

    def set_response(self, response: ResourceResult):
        self._response = response

    def __call__(self, request) -> ResourceResult:
        self._calls.append({"prompt": request.prompt, "model": request.model})
        if self._response:
            return self._response
        return ResourceResult(
            success=True,
            data="fake AI generated text",
            mime_type="text/plain",
            source_used="ai__text",
        )

    @property
    def call_count(self) -> int:
        return len(self._calls)


class FakeSkillExecutor:
    """Fake Skill executor — 模拟 Skill 执行"""

    def __init__(self, response: ResourceResult | None = None):
        self._response = response
        self._calls: list[dict] = []

    def set_response(self, response: ResourceResult):
        self._response = response

    def __call__(self, params: dict) -> ResourceResult:
        self._calls.append(params)
        if self._response:
            return self._response
        return ResourceResult(
            success=True,
            data=b"fake_skill_output_bytes",
            mime_type="image/png",
            source_used="skill__matplotlib",
        )

    @property
    def call_count(self) -> int:
        return len(self._calls)
