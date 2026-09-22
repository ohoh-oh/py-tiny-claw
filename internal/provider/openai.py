import os
import openai
from internal.schema.message import (
    Message,
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    ToolCall,
    ToolDefinition,
)


class OpenAIProvider:
    def __init__(self, client: openai.OpenAI, model: str):
        self.client = client
        self.model = model

    def generate(self, msgs: list[Message], available_tools: list[ToolDefinition] | None) -> Message:
        # 1. 把内部统一格式的消息翻译为 OpenAI Chat Completions 的格式
        openai_msgs = []
        for msg in msgs:
            if msg.role == ROLE_SYSTEM:
                openai_msgs.append({"role": "system", "content": msg.content})
            elif msg.role == ROLE_USER:
                if msg.tool_call_id != "":
                    # 工具执行结果在 OpenAI 协议中是独立的 "tool" 角色消息
                    openai_msgs.append({
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                    })
                else:
                    openai_msgs.append({"role": "user", "content": msg.content})
            elif msg.role == ROLE_ASSISTANT:
                ast_param: dict = {"role": "assistant"}
                if msg.content != "":
                    ast_param["content"] = msg.content
                if len(msg.tool_calls) > 0:
                    tool_calls = []
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                # OpenAI 协议中 arguments 本身就是 JSON 字符串
                                "arguments": tc.arguments,
                            },
                        })
                    ast_param["tool_calls"] = tool_calls
                openai_msgs.append(ast_param)

        # 2. 翻译工具定义为 OpenAI Function Calling 格式
        openai_tools = []
        for tool_def in available_tools or []:
            params_schema = tool_def.input_schema if isinstance(tool_def.input_schema, dict) else {}
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": params_schema,
                },
            })

        params = {
            "model": self.model,
            "messages": openai_msgs,
        }
        if openai_tools:
            params["tools"] = openai_tools

        try:
            resp = self.client.chat.completions.create(**params)
        except Exception as e:
            raise RuntimeError(f"DeepSeek API 调用失败: {e}") from e

        if len(resp.choices) == 0:
            raise RuntimeError("DeepSeek API 返回了空的 choices")

        # 3. 把 DeepSeek 返回的消息翻译为内部统一格式
        choice = resp.choices[0].message
        result_msg = Message(role=ROLE_ASSISTANT, content=choice.content or "")
        for tc in choice.tool_calls or []:
            if getattr(tc, "type", None) == "function":
                result_msg.tool_calls.append(
                    ToolCall(
                        id=getattr(tc, "id", ""),
                        name=getattr(tc.function, "name", ""),
                        arguments=getattr(tc.function, "arguments", ""),
                    )
                )
        return result_msg


def new_deepseek_provider(model: str | None = None) -> OpenAIProvider:
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 DEEPSEEK_API_KEY")

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    resolved_model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    return OpenAIProvider(client, resolved_model)


# 兼容旧命名，避免历史调用点失效
def new_zhipu_openai_provider(model: str | None = None) -> OpenAIProvider:
    return new_deepseek_provider(model=model)