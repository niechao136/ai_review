import typer
from typing import Optional
from .config import config_cli
from .init import init_cli
from .review import review_code

app = typer.Typer()

@app.command()
def init():
    """将 AI 评审钩子注入到当前项目的 .git 文件夹下"""
    init_cli()


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="配置项名称 (如 api_key, model)"),
    value: Optional[str] = typer.Argument(None, help="要设置的值"),
    list_all: bool = typer.Option(False, "--list", "-l", help="列出所有配置")
):
    """管理配置信息，用法类似 git config"""
    config_cli(key=key, value=value, list_all=list_all)


@app.command()
def review(
    ref: str = typer.Argument("HEAD", help="要检查的提交 ID、分支名或 Tag（默认为最后一次提交 HEAD）")
):
    """
    🚀 核心指令：执行 AI 自动代码评审。
    支持对比指定提交：ai-review review <commit_id>

    逻辑流程:
    1. 自动提取 Git 变更：对比 commit_id 与 commit_id^ 。
    2. 智能过滤：剔除二进制文件、大文件及 node_modules 等干扰项。
    3. 调用 AI：将清理后的 Diff 发送至配置的大模型 (如 DeepSeek/GPT)。
    4. 风险评估：解析 AI 回复中的 [DECISION] 指令。

    拦截机制:
    若 AI 返回 [DECISION: BLOCK]，则程序以状态码 1 退出，从而拦截 Git Push。
    """
    review_code(ref)