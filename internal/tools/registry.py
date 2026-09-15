from abc import ABC,abstractmethod
from internal.schema.message import ToolCall,ToolDefinition,ToolResult
class Registry(ABC):
    """工具注册中心接口（对应Go的interface）"""
    @abstractmethod
    def get_available_tools(self) -> list[ToolDefinition]:
        pass
    @abstractmethod
    def execute(self,call:ToolCall) -> ToolResult:
        pass