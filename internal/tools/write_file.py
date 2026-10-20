#internal/tools/write_file.py
#第6章：write_file工具 —— 创建或整体覆盖写入文件
import json
import os

from internal.schema.message import ToolDefinition
from internal.tools.registry import BaseTool

class WriteFileTool(BaseTool):
    def __init__(self, work_dir: str):
        self._work_dir = work_dir

    def name(self) -> str:
        return "write_file"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="创建或覆盖写入一个文件。如果目录不存在会自动创建。请提供工作区的相对路径。",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "写入文件的路径，例如 src/main.py。"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的完整文件内容。"
                    },
                },
                "required": ["path", "content"],
            },
        )

    def execute(self, args: str) -> str:
        try:
            input_args = json.loads(args)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"参数解析失败: {e}") from e

        path = input_args.get("path", "")
        content = input_args.get("content", "")

        full_path = os.path.join(self._work_dir, path)

        #自动创建父目录
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"创建父目录失败: {e}") from e

        # 写入文件内容
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise RuntimeError(f"文件写入失败: {e}") from e

        return f"成功将内容写入文件：{path}"