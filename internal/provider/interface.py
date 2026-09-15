from abc import ABC,abstractmethod
from internal.schema.message import ToolDefinition
class LLMProvider(ABC):
    """LLMProvider定义了与大模型通信的统一接口（对应Go的interface)"""
    @abstractmethod
    def generate(self,messages:list[Message],avaiable_tools:list[ToolDefinition]|None) -> Message:
        """generate接受了当前上下文历史和可调用工具列表，返回模型响应"""
        pass