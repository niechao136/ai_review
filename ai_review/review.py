import sys
import httpx

from openai import OpenAI
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam

from .config import load_full_config
from .core import get_clean_diff
from .prompts import SYSTEM_PROMPT
from .utils import console


def review_code(ref: str):
    # 1. 加载配置
    config = load_full_config()
    api_key = config.get("api_key")
    base_url = config.get("base_url")
    model = config.get("model")

    if not base_url:
        console.print("[red]❌ 错误: 未配置 Base Url。请运行 `ai-review config base_url <your_url>`[/red]")
        sys.exit(1)

    if not model:
        console.print("[red]❌ 错误: 未配置 Model。请运行 `ai-review config model <your_model>`[/red]")
        sys.exit(1)

    # 2. 获取经过智能过滤的 Diff
    console.print("[cyan]🔍 正在提取 Git 变更并进行智能过滤...[/cyan]")
    diff_content, success = get_clean_diff(ref=ref)

    if not success:
        console.print(f"[red]{diff_content}[/red]")
        sys.exit(1)

    if not diff_content or diff_content.strip() == "":
        console.print("[yellow]分段中未发现需要评审的文本变更，跳过。[/yellow]")
        return

    # 加入代理配置
    proxy_url = config.get("proxy")
    if proxy_url:
        http_client = httpx.Client(proxy=proxy_url)
        console.print(f"[dim]🌐 使用代理: {proxy_url}[/dim]")
    else:
        http_client = None
    # 3. 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )

    # 4. 调用 AI 进行评审
    console.print(f"[bold green]🤖 AI ({model}) 正在评审中...[/bold green]\n")

    try:
        system: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
        user: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": f"请评审以下 Git Diff 变更：\n\n{diff_content}"
        }
        response = client.chat.completions.create(
            model=model,
            messages=[system, user],
            stream=True  # 开启流式传输，体验更好
        )

        # 使用 Rich 实现流式 Markdown 渲染
        full_response = ""
        console.print("-" * 50)

        # 简单的流式打印效果
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                console.print(content, end="")

        console.print("\n" + "-" * 50)

        last_lines = full_response.strip().splitlines()[-3:]
        decision_text = "".join(last_lines).upper()
        if "[DECISION: BLOCK]" in decision_text:
            console.print("\n[bold red]🚫 Git Push 已拦截：AI 评估认为当前变更存在严重隐患。[/bold red]")
            # 强制退出，返回非零状态码，Git 会停止 push
            sys.exit(1)
        elif "[DECISION: PASS]" in decision_text:
            console.print("\n[bold green]✨ AI 评审通过，准予推送。[/bold green]")
        else:
            # 兜底逻辑：如果 AI 没按格式说话，默认允许通过，但给个警告
            console.print("\n[yellow]⚠️ 提示：AI 未给出明确的拦截指令，请自行判断。[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ AI 调用失败: {e}[/red]")
        sys.exit(1)