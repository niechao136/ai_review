import sys
import httpx

from openai import OpenAI
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam
from rich.markup import escape

from .config import load_full_config
from .core import get_clean_diff
from .prompts import SYSTEM_PROMPT
from .report import ensure_gitignore, save_review_report
from .types import ReviewMode, DiffStatus
from .utils import console


def review_code(ref: str = "HEAD", mode: ReviewMode = ReviewMode.COMMIT):
    """
    核心评审逻辑：集成配置加载、Diff 提取、AI 调用及决策拦截。

    Args:
        ref: Git 引用（提交 ID、分支或 Tag）。
        mode: 评审代码模式：评审提交、评审暂存区 (Staged)、评审本地修改
    """
    # 1. 加载配置并进行合法性校验
    config = load_full_config()
    api_key = config.get("api_key")
    base_url = config.get("base_url")
    model = config.get("model")

    # 必须配置 Base URL 和 Model 才能继续执行
    if not base_url:
        console.print("[red]❌ 错误: 未配置 Base Url。请运行 `ai-review config base_url <your_url>`[/red]")
        sys.exit(1)

    if not model:
        console.print("[red]❌ 错误: 未配置 Model。请运行 `ai-review config model <your_model>`[/red]")
        sys.exit(1)

    # 2. 调用核心模块提取经过过滤的文本 Diff
    console.print("[cyan]🔍 正在提取 Git 变更并进行智能过滤...[/cyan]")
    diff_content, flag = get_clean_diff(ref=ref, mode=mode)

    # get_clean_diff 返回失败，则直接退出
    if flag == DiffStatus.FAILED:
        console.print(diff_content)
        sys.exit(1)

    # get_clean_diff 返回跳过，则跳过评审
    if flag == DiffStatus.SKIP:
        console.print(diff_content)
        return

    # 3. 网络代理配置处理
    proxy_url = config.get("proxy")
    if proxy_url:
        # 如果配置了代理，初始化 httpx 客户端以支持代理转发
        http_client = httpx.Client(proxy=proxy_url)
        console.print(f"[dim]🌐 使用代理: {proxy_url}[/dim]")
    else:
        http_client = None

    # 4. 初始化 OpenAI 兼容协议客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )

    console.print(f"[bold green]🤖 AI ({model}) 正在评审中...[/bold green]\n")

    try:
        # 封装符合 OpenAI API 标准的消息格式
        system: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
        user: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": f"请评审以下 Git Diff 变更：\n\n{diff_content}"
        }

        # 发起流式请求
        response = client.chat.completions.create(
            model=model,
            messages=[system, user],
            stream=True
        )

        full_response = ""
        console.print("-" * 50)

        # 5. 流式处理 AI 响应结果并实时打印到控制台
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                console.print(content, end="")

        console.print("\n" + "-" * 50)

        # 6. 决策解析与 Git 拦截逻辑
        # 检查 AI 回复的最后几行是否包含预设的决策指令
        last_lines = full_response.strip().splitlines()[-3:]
        decision_text = "".join(last_lines).upper()

        if "[DECISION: BLOCK]" in decision_text:
            # 发现严重隐患，返回非零状态码，这将阻止 git 命令的继续执行
            console.print("\n[bold red]🚫 AI 评审未通过：AI 评估认为当前变更存在严重隐患。[/bold red]")
            sys.exit(1)
        elif "[DECISION: PASS]" in decision_text:
            # 评审通过，允许 Git 操作继续
            console.print("\n[bold green]✨ AI 评审通过：代码质量达标，准予继续后续操作。[/bold green]")
        else:
            # 如果 AI 未遵循预定义格式给出决策，默认不拦截但给予风险提示
            console.print("\n[yellow]⚠️ 提示：AI 未给出明确的拦截指令，请自行判断。[/yellow]")


        ensure_gitignore()

        saved_path = save_review_report(full_response)

        if saved_path:
            console.print(f"[dim]📝 报告已存至: {saved_path}[/dim]")

    except Exception as e:
        # 捕获网络、API 调用或权限等异常情况
        console.print(f"[red]❌ AI 调用失败: {escape(str(e))}[/red]")
        sys.exit(1)