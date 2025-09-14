#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console Manager - 统一的控制台管理工具

这个模块提供了统一的控制台管理功能，安全处理Rich Console的live变量，
避免在不同agent之间出现兼容性错误。
"""

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from typing import Optional, Any, Callable
import threading
from contextlib import contextmanager

class SafeConsoleManager:
    """安全的控制台管理器
    
    提供统一的控制台操作接口，安全处理live变量，避免跨agent的兼容性问题。
    """
    
    def __init__(self):
        """初始化控制台管理器"""
        self._console = Console()
        self._live_stack = []
        self._lock = threading.Lock()
    
    @property
    def console(self) -> Console:
        """获取控制台实例"""
        return self._console
    
    def print(self, *args, **kwargs):
        """安全的打印方法"""
        self._console.print(*args, **kwargs)
    
    def print_panel(self, content: str, title: str = None, border_style: str = "blue"):
        """打印面板"""
        if title:
            panel = Panel.fit(content, title=title, border_style=border_style)
        else:
            panel = Panel.fit(content, border_style=border_style)
        self._console.print(panel)
    
    def print_markdown(self, content: str):
        """打印Markdown内容"""
        self._console.print(Markdown(content))
    
    def prompt_ask(self, message: str, **kwargs) -> str:
        """安全的输入提示"""
        with self._pause_live():
            return Prompt.ask(message, **kwargs)
    
    def confirm_ask(self, message: str, default: bool = True) -> bool:
        """安全的确认提示"""
        with self._pause_live():
            return Confirm.ask(message, default=default)
    
    @contextmanager
    def _pause_live(self):
        """暂停当前的live显示"""
        with self._lock:
            paused_lives = []
            
            # 安全地获取并暂停所有活跃的live显示
            if hasattr(self._console, '_live_stack') and self._console._live_stack:
                for live in self._console._live_stack:
                    if live and hasattr(live, 'is_started') and live.is_started:
                        live.stop()
                        paused_lives.append(live)
            
            try:
                yield
            finally:
                # 重新启动之前暂停的live显示
                for live in reversed(paused_lives):
                    if live and hasattr(live, 'start'):
                        try:
                            live.start()
                        except Exception:
                            # 忽略重启失败的情况
                            pass
    
    def safe_live_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """安全地执行需要暂停live的操作
        
        Args:
            operation: 要执行的操作函数
            *args: 操作函数的位置参数
            **kwargs: 操作函数的关键字参数
            
        Returns:
            操作函数的返回值
        """
        with self._pause_live():
            return operation(*args, **kwargs)
    
    def get_current_live(self) -> Optional[Live]:
        """安全地获取当前的live实例"""
        try:
            if (hasattr(self._console, '_live_stack') and 
                self._console._live_stack and 
                len(self._console._live_stack) > 0):
                return self._console._live_stack[-1]
        except (AttributeError, IndexError):
            pass
        return None
    
    def is_live_active(self) -> bool:
        """检查是否有活跃的live显示"""
        live = self.get_current_live()
        return live is not None and hasattr(live, 'is_started') and live.is_started
    
    @contextmanager
    def managed_live(self, renderable, **kwargs):
        """管理的live上下文
        
        Args:
            renderable: 要显示的内容
            **kwargs: Live的其他参数
        """
        live = Live(renderable, console=self._console, **kwargs)
        try:
            live.start()
            yield live
        finally:
            if live.is_started:
                live.stop()

# 全局控制台管理器实例
_global_console_manager: Optional[SafeConsoleManager] = None

def get_console_manager() -> SafeConsoleManager:
    """获取全局控制台管理器实例"""
    global _global_console_manager
    if _global_console_manager is None:
        _global_console_manager = SafeConsoleManager()
    return _global_console_manager

def get_safe_console() -> Console:
    """获取安全的控制台实例"""
    return get_console_manager().console

# 便捷函数
def safe_print(*args, **kwargs):
    """安全的打印函数"""
    get_console_manager().print(*args, **kwargs)

def safe_print_panel(content: str, title: str = None, border_style: str = "blue"):
    """安全的面板打印函数"""
    get_console_manager().print_panel(content, title, border_style)

def safe_print_markdown(content: str):
    """安全的Markdown打印函数"""
    get_console_manager().print_markdown(content)

def safe_prompt_ask(message: str, **kwargs) -> str:
    """安全的输入提示函数"""
    return get_console_manager().prompt_ask(message, **kwargs)

def safe_confirm_ask(message: str, default: bool = True) -> bool:
    """安全的确认提示函数"""
    return get_console_manager().confirm_ask(message, default)

def safe_live_operation(operation: Callable, *args, **kwargs) -> Any:
    """安全地执行需要暂停live的操作"""
    return get_console_manager().safe_live_operation(operation, *args, **kwargs)