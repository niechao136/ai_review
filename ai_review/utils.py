import sys
import io
from rich.console import Console

# --- 1. 标准输出流 (Standard Stream) 包装处理 ---

# 针对 Windows 环境进行字符编码强制修正
# 解决旧版 Windows 控制台（CMD/PowerShell）不支持 UTF-8 导致 ✅、❌ 等 Emoji 报错崩溃的问题
if sys.platform == "win32":
    # 检查当前 stdout 是否已处于正确的 UTF-8 包装状态，避免重复操作
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding.lower() != 'utf-8':
        # 重新包装 sys.stdout：
        # - 使用 .buffer 直接操作底层字节流
        # - 强制使用 utf-8 编码
        # - errors="replace" 确保遇到无法渲染的字符时以替代符显示，而非抛出 UnicodeEncodeError
        # - line_buffering=True 保证输出实时刷新
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )

    # 对标准错误流 sys.stderr 执行相同的 UTF-8 包装逻辑
    if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )

# --- 2. 初始化 Rich Console 对象 ---

# 基于修复后的标准流初始化终端渲染引擎
console = Console(
    # 在 Windows 平台强制启用终端模式，以确保在 PyCharm、VSCode 等 IDE 的集成控制台中能正确渲染颜色
    force_terminal=True if sys.platform == "win32" else None,

    # 显式指定 Rich 使用经过 UTF-8 包装后的 sys.stdout 流进行输出
    file=sys.stdout,

    # 针对旧版本 Windows 控制台（如 Win7/Win10 早期版本）启用兼容模式，处理特定的转义字符渲染
    legacy_windows=True if sys.platform == "win32" else None
)