#internal/tools/bash.py
#第6章：bash工具 —— Agent最强大的"万能手"，可以任意执行 shell 命令
import json
import os
import shutil
import subprocess

from internal.schema.message import ToolDefinition
from internal.tools.registry import BaseTool


class BashTool(BaseTool):
    def __init__(self, work_dir: str):
        self._work_dir = work_dir

    def name(self) -> str:
        return "bash"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="在工作区执行任意的 bash 命令。支持链式命令（如&&）。返回标准输出（stdout）和标准错误（stderr）。",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 bash 命令，例如 ls -l /path/to/dir。",
                    },
                },
                "required": ["command"],
            },
        )

    def _build_shell_command(self, command: str):
        if os.name == "nt":
            pwsh = shutil.which("pwsh") or shutil.which("powershell")
            if pwsh:
                normalized = command.strip()
                normalized = normalized.replace("&&", ";")
                normalized = normalized.replace("pwd", "(Get-Location).Path")
                normalized = normalized.replace("ls -la", "Get-ChildItem -Force")
                normalized = normalized.replace("ls -l", "Get-ChildItem")
                normalized = normalized.replace("ls ", "Get-ChildItem ")
                normalized = normalized.replace("cat ", "Get-Content ")
                normalized = normalized.replace("echo ", "Write-Output ")
                if "find " in normalized and " -name " in normalized:
                    # 例: find . -name "server.py" -> Get-ChildItem -Recurse -Filter server.py
                    import re
                    match = re.search(r'find\s+([^\s]+)\s+-name\s+"?([^"]+)"?', normalized)
                    if match:
                        directory, name = match.groups()
                        normalized = f"Get-ChildItem -Recurse -Filter '{name}' '{directory}' -Force | Select-Object -ExpandProperty FullName"
                return [pwsh, "-NoProfile", "-Command", normalized]
            return ["cmd", "/c", command]
        bash = shutil.which("bash")
        if bash:
            return [bash, "-c", command]
        return ["sh", "-c", command]

    def execute(self, args: str) -> str:
        try:
            input_args = json.loads(args)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"参数解析失败: {e}") from e

        command = input_args.get("command", "")
        shell_cmd = self._build_shell_command(command)

        # 30秒超时保护，防止模型执行的命令把引擎挂死
        try:
            proc = subprocess.run(
                shell_cmd,
                cwd=self._work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired as e:
            partial = (e.stdout or "") + (e.stderr or "")
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            return partial + "\n[警告：命令执行超时（30s），已被系统强制终止。]"

        output_str = proc.stdout + proc.stderr

        if proc.returncode != 0:
            return f"执行报错：exit status {proc.returncode}\n输出：\n{output_str}"
        if output_str == "":
            return "[命令执行成功，无终端输出。]"

        MAX_LEN = 8000
        if len(output_str) > MAX_LEN:
            return f"{output_str[:MAX_LEN]}\n\n...[终端输出过长,已被系统截断至前{MAX_LEN}字节]..."
        return output_str