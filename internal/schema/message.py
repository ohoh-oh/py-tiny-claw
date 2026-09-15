from dataclasses import dataclass,field
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
@dataclass
class ToolCall:
    """模型发起的一次工具调用请求。arguments保持为原始JSON字符串（对应Go的json.RawMessage,
    由个工具自行解析"""
    id:str = ""
    name:str = ""
    arguments:str = ""
@dataclass
class Message:
    """一条上下文消息。tool_calls仅在assistant消息中出现;tool_call_id仅在承载工具执行结果的
    user消息中出现。"""
    role:str = ""
    content:str = ""
    tool_calls:list[ToolCall] = field(default_factory = list)
    tool_call_id:str = ""
@dataclass
class ToolResult:
    """一次工具执行的结果。"""
    tool_call_id:str = ""
    output:str = ""
    is_error:bool = False
@dataclass
class ToolDefinition:
    """暴露给模型的工具定义（名称 + 描述 + JSON Schema 入参约束）。"""     
    name:str = ""
    description:str = ""
    input_schema:dict | None = None