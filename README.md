# 🤖 AI Code Reviewer

**AI Code Reviewer** 是一个基于 Git Hook 的智能代码评审工具。它能在你执行 `git push` 前，自动提取代码变更并调用大模型（如 Gemini, DeepSeek, GPT-4）进行深度逻辑评审。如果发现严重漏洞，它将拦截你的提交。

## ✨ 特性

  * **智能过滤**：自动识别并跳过二进制文件（图片、模型、压缩包），节省 Token。
  * **正向/历史评审**：既能拦截 `push` 前的变更，也能针对特定的历史 `commit` 进行复盘。
  * **Git 原生集成**：一键注入 `pre-push` 钩子，无缝嵌入现有开发流。
  * **灵活配置**：类似 `git config` 的操作体验，支持自定义 API Base URL 和模型。
  * **流式输出**：评审建议逐字弹出，拒绝盲目等待。

## 🚀 快速开始

### 1\. 安装

直接通过 GitHub 安装最新版本：

```bash
pip install git+https://github.com/niechao136/ai_review.git
```

### 2\. 初始化配置

设置你的 API 信息（配置存储在 `~/.ai_review.json`）：

```bash
# 设置 API Key
ai-review config api_key your-secret-key

# 设置 API 代理地址 (支持 OpenAI 格式接口)
ai-review config base_url https://generativelanguage.googleapis.com/v1beta/openai/

# 设置使用的模型
ai-review config model gemini-2.5-flash

# [可选] 设置网络代理 (如需访问 Google Gemini 或 OpenAI)
ai-review config proxy http://127.0.0.1:1080
```

### 3\. 项目注入与移除

进入你的 Git 项目根目录：

```bash
# 默认注入 pre-push
ai-review init

# 全方位守护：同时注入 commit 和 push 拦截
ai-review init all

# [可选] 指定注入 pre-commit
ai-review init pre-commit

# 移除指定钩子，参数与 init 命令相同
ai-review remove pre-commit
```

-----

## 🛠️ 命令手册

| 命令       | 说明                  | 示例                               |
|:---------|:--------------------|:---------------------------------|
| `config` | 管理全局配置              | `ai-review config [key] [value]` |
| `init`   | 为当前项目安装/更新 Git Hook | `ai-review init [hook_type]`     |
| `remove` | 从当前项目移除 Git Hook 配置 | `ai-review remove [hook_type]`   |
| `review` | **核心：** 执行代码评审      | `ai-review review [commit ID]`   |

### 🔍 深度使用 `review` 指令

`review` 命令非常灵活，支持以下三种场景：

1. **自动拦截 (Git Hook)**：
    - **Push 拦截**：执行 git push 时，评审 HEAD 提交。若被拦截，推送中止。*注：若一次推送多个 commit，目前版本仅审计最顶层的 commit。*
    - **Commit 拦截**：若安装了 pre-commit 钩子，将在提交前评审 暂存区 (Staged) 代码。

2. **评审暂存区 (手动)**：
    如果你想在提交前手动检查当前已 git add 的变更：

    ```bash
    # 评审暂存区
    ai-review review --staged
    ```

3. **评审历史特定提交 (复盘)**：
    你可以针对某个特定的 `commit ID` 进行评审：

    ```bash
    # 评审指定提交的变更
    ai-review review 9852a8ce
    ```

    *注：评审指定提交时，系统会自动对比该提交及其父节点 (`ref^`) 的差异。*

-----

## 🔍 评审维度

AI 将从以下五个维度审视你的代码：

1.  **逻辑正确性**：边界处理、空指针、业务闭环。
2.  **性能优化**：循环嵌套、资源释放、冗余查询。
3.  **安全隐患**：SQL 注入、硬编码密钥、权限漏洞。
4.  **代码规范**：命名清晰度、DRY 原则、可读性。
5.  **最终决策**：给出 `PASS` 或 `BLOCK` 指令。

## 💡 开发者贴士

  * **跳过评审**：如果你急于推送且确信代码没问题，可以使用 `git push --no-verify` 绕过钩子。
  * **卸载提示**：如果你打算彻底卸载本工具，可以运行 `ai-review remove` 以清理 Hook 脚本。

## 📄 开源协议

[MIT License](LICENSE)