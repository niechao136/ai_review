# 🤖 AI Code Reviewer

[](https://www.python.org/)
[](https://www.google.com/search?q=LICENSE)

**AI Code Reviewer** 是一个基于 Git Hook 的智能代码评审工具。它能在你执行 `git push` 前，自动提取代码变更并调用大模型（如 DeepSeek, GPT-4）进行深度逻辑评审。如果发现严重漏洞，它将化身“硬核架构师”拦截你的提交。

## ✨ 特性

  * **智能过滤**：自动识别并跳过二进制文件（图片、模型、压缩包）及超大文本，节省 Token。
  * **架构师级评审**：不仅看语法，更关注逻辑错误、安全隐患、性能瓶颈及代码整洁度。
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

设置你的 API Key 和模型信息（配置将加密存储在 `~/.ai_reviewer.json`）：

```bash
# 设置 API Key (输入时会隐藏)
ai-review config api_key sk-xxxxxx

# 设置 API 代理地址 (默认为 DeepSeek)
ai-review config base_url https://api.deepseek.com

# 设置使用的模型
ai-review config model deepseek-chat
```

### 3\. 项目注入

进入你的 Git 项目根目录，启用自动评审：

```bash
ai-review init
```

此操作会在 `.git/hooks/pre-push` 中添加调用指令。

## 🛠️ 命令手册

| 命令       | 说明               | 示例                              |
|:---------|:-----------------|:--------------------------------|
| `config` | 管理全局配置           | `ai-review config model gpt-4o` |
| `init`   | 为当前项目安装 Git Hook | `ai-review init`                |
| `review` | 手动触发代码评审         | `ai-review review`              |

## 🔍 评审维度

AI 将从以下五个维度审视你的代码：

1.  **逻辑正确性**：边界处理、空指针、业务闭环。
2.  **性能优化**：循环嵌套、资源释放、冗余查询。
3.  **安全隐患**：SQL 注入、硬编码密钥、权限漏洞。
4.  **代码规范**：命名清晰度、DRY 原则、可读性。
5.  **最终决策**：给出 `PASS` 或 `BLOCK` 指令。

## 💡 开发者贴士

  * **跳过评审**：如果你急于推送且确信代码没问题，可以使用 `git push --no-verify` 绕过钩子。
  * **本地调试**：如果你想修改源码，建议使用可编辑模式安装：
    ```bash
    git clone https://github.com/niechao136/ai_review.git
    cd ai_review
    pip install -e .
    ```

## 📄 开源协议

[MIT License](LICENSE)
