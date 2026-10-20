import logging
from abc import ABC, abstractmethod
from internal.schema.message import ToolCall, ToolDefinition, ToolResult
log = logging.getLogger(__name__)
class BaseTool(ABC):
    @abstractmethod
    def name(self) -> str:
        pass
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass
    @abstractmethod
    def execute(self, args: str) -> str:
        """args为原始JSON字符串,由工具自行解析;执行失败时抛出异常(对应Go的返回error)"""
        pass
class Registry(ABC):
    """工具注册中心接口"""
    @abstractmethod
    def register(self, tool: BaseTool):
        """注册工具"""
        pass
    @abstractmethod
    def get_available_tools(self) -> list[ToolDefinition]:
        """获取可用工具列表"""
        pass
    @abstractmethod
    def execute(self, call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass
class RegistryImpl(Registry):
    """工具注册中心实现"""
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        name = tool.name()
        if name in self._tools:
            log.info(" [Warning] 工具 '%s' 已经被注册，将被覆盖。", name)
        self._tools[name] = tool
        log.info(" [Registry] 成功挂载工具：%s", name)

    def get_available_tools(self) -> list[ToolDefinition]:
        return [tool.definition() for tool in self._tools.values()]

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if not tool:
            err_msg = f"Error:系统中不存在名为'{call.name}'的工具。"
            return ToolResult(
                tool_call_id=call.id,
                output=err_msg,
                is_error=True,
            )
        # 统一的异常兜底：工具内部抛出的任何异常都转换为 is_error 的观察结果，
        # 反馈给模型让它自行纠错，而不是让整个引擎崩溃。
        try:
            output = tool.execute(call.arguments)
        except Exception as e:
            return ToolResult(
                tool_call_id=call.id,
                output=f"Error executing {call.name}: {e}",
                is_error=True,
            )
        return ToolResult(
            tool_call_id=call.id,
            output=output,
            is_error=False,
        )


def new_registry() -> Registry:
    """对应 Go 版的 NewRegistry 构造函数"""
    return RegistryImpl()