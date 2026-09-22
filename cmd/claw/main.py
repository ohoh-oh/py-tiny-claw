import logging
import os
import sys
from internal.engine.loop import AgentEngine
from internal.provider.openai import new_deepseek_provider
from internal.schema.message import ToolCall, ToolDefinition, ToolResult
from internal.tools.registry import Registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
log = logging.getLogger(__name__)


class MockRegistry(Registry):
    def get_available_tools(self):
        return [
            ToolDefinition(
                name="get_weather",
                description="获取指定城市的当前天气情况。",
                input_schema={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ]

    def execute(self, call: ToolCall) -> ToolResult:
        log.info("  -> [Mock 工具执行] 获取 %s 的天气中...", call.name)
        return ToolResult(
            tool_call_id=call.id,
            output="API 返回：今天是晴天，气温 25 度。",
            is_error=False,
        )


def main():
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("请先导出 DEEPSEEK_API_KEY 环境变量")

    work_dir = os.getcwd()
    llm_provider = new_deepseek_provider()
    registry = MockRegistry()
    eng = AgentEngine(llm_provider, registry, work_dir, True)
    prompt = "我想去北京跑步，帮我查查天气适合吗？"

    try:
        eng.run(prompt)
    except Exception as e:
        sys.exit(f"引擎运行崩溃: {e}")


if __name__ == "__main__":
    main()