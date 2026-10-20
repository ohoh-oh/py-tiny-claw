import logging
import os
import sys
from internal.engine.loop import AgentEngine
from internal.provider.openai import new_deepseek_provider
from internal.tools.bash import BashTool
from internal.tools.edit_file import EditFileTool
from internal.tools.read_file import ReadFileTool
from internal.tools.registry import new_registry
from internal.tools.write_file import WriteFileTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                    datefmt="%Y/%m/%d %H:%M:%S")


def main():
    if not os.getenv("DEEPSEEK_API_KEY"):
        sys.exit("请先导出 DEEPSEEK_API_KEY 环境变量")

    work_dir = os.getcwd()
    llm_provider = new_deepseek_provider()
    registry = new_registry()
    registry.register(ReadFileTool(work_dir))
    registry.register(WriteFileTool(work_dir))
    registry.register(BashTool(work_dir))
    registry.register(EditFileTool(work_dir))  # 挂载 Edit 工具

    # 开启慢思考模式
    eng = AgentEngine(llm_provider, registry, work_dir, False)
    prompt = prompt = """
请按顺序完成以下操作，每一步都使用对应的工具：
1. 用 write_file 创建 calc.py，内容是一个函数 add(a, b) 返回 a + b，并在文件末尾 print(add(2, 3))
2. 用 bash 执行 python calc.py
3. 用 edit_file 把 return a + b 改成 return a * b
4. 用 read_file 读取 calc.py 确认修改成功
5. 再用 bash 执行一次 python calc.py，告诉我两次输出分别是多少
"""

    try:
        eng.run(prompt)
    except Exception as e:
        sys.exit(f"引擎运行崩溃: {e}")


if __name__ == "__main__":
    main()