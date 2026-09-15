import logging
from internal.provider.interface import LLMProvider
from internal.schema.message import Message,ROLE_SYSTEM,ROLE_USER
from internal.tools.registry import Registry
log = logging.getLogger(__name__)
class AgentEgine:
    """Agent引擎：持有Provider(大脑与registry(手脚)，并锁定一个工作区目录。)"""
    def __init__(self,provider:LLMProvider,registry:Registry,work_dir:str):
        self.provider = provider
        self.registry = registry
        self.work_dir = work_dir
    def run(self,user_promt:str) -> None:
        log.info("[Engine]引擎启动，锁定工作区：%s",self.work_dir)
        context_history:list[Message] = [Message(role = ROLE_SYSTEM,content="you are py-tiny-claw,an expert coding assistant.You have full" \
        "access to tools in the workspace.",),Message(role = ROLE_USER,content = user_promt,),]
        turn_count = 0
        while True:
            turn_count += 1
            log.info("===============[Turn %d]开始===============",turn_count)
            available_tools = self.registry.get_available_tools()
            log.info("[Engine]正在思考(reasoning)...")
            try:
                response_msg = self.provider.generate(context_history,available_tools)
            except Exception as e:
                raise RuntimeError(f"模型生成失败：{e}")from e
            context_history.append(response_msg)
            if response_msg.content != "":
                print(f"模型：{response_msg.content}")
            if len(response_msg.tool_calls) == 0:
                log.info("[Engine]任务完成，退出循环。")
                break
            log.info("[Engine]模型请求调用%d个工具...",len(response_msg.tool_calls))
            for tool_call in response_msg.tool_calls:
                log.info("->执行工具：%s,参数：%s",tool_call.name,tool_call.arguments)
                result = self.registry.execute(tool_call)
                if result.is_error:
                    log.info("->×工具执行报错:%s",result.output)
                else:
                    log.info("->√工具执行成功（返回%d字节)",len(result.output))
                    observation_msg = Message(role=ROLE_USER,content=result.output,tool_call_id=tool_call.id,)
                    context_history.append(observation_msg)
