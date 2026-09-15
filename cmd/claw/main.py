import logging
import os
import sys
from internal.engine.loop import AgentEgine
from internal.provider.interface import LLMProvider
from internal.schema.message import (Message,ROLE_ASSISTANT,ToolCall,ToolResult,
)
from internal.tools.registry import Registry
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s",
datefmt="%Y/%m/%d %H:%M:%S")
class MockProvider(LLMProvider):
    def __init__(self):
        self.turn = 0
    def generate(self, msgs, _tools):
        self.turn += 1
        if self.turn == 1:
            return Message(role=ROLE_ASSISTANT,content="让我来看看当前目录下有什么文" \
            "件。",tool_calls=[ToolCall(id="call_123",name="bash",arguments='{"command":"ls -la"}'),],)
        return Message(role=ROLE_ASSISTANT,content="我看到了文件列表，里面包含main.py,任务完成！",)
class MockRegistry(Registry):
    def get_available_tools(self):
        return []
    def execute(self,call:ToolCall) -> ToolResult:
        return ToolResult(tool_call_id=call.id,output="-rw-r--r--  1 user group 234 Oct 24 10:00 main.py\n",is_error=False,)
def main():
        work_dir = os.getcwd()
        p = MockProvider()
        r = MockRegistry()
        eng = AgentEgine(p,r,work_dir)
        try:
            eng.run("你帮我查看当前目录的文件")
        except Exception as e:
            sys.exit(f"引擎崩溃：{e}")
if __name__ == "__main__":
        main()  