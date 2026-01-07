import sys
import threading
from datetime import datetime
from typing import Optional, List
from enum import Enum
from colorama import Fore, Style, init

# Initialize colorama for Windows support
init(autoreset=True)

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    SUCCESS = 4
    ERROR = 5
    CRITICAL = 6

class TreeLogger:
    """
    Flux Style Logger (Redesigned Visuals)
    Maintains exact API compatibility with previous version.
    """
    
    def __init__(self, level: LogLevel = LogLevel.DEBUG, prefix: str = "Ryzen"):
        self.level = level
        self.prefix = prefix # Kept for compatibility, though distinct columns are used now
        self.write_lock = threading.Lock()
        
        # Colors (Kept for compatibility if you access them externally)
        self.RESET = Style.RESET_ALL
        self.WHITE = Fore.WHITE
        self.GRAY = Style.DIM
        self.MAGENTA = Fore.MAGENTA
        self.BRIGHT_MAGENTA = Fore.MAGENTA + Style.BRIGHT
        self.PINK = Fore.MAGENTA
        self.RED = Fore.RED
        self.GREEN = Fore.GREEN
        self.YELLOW = Fore.YELLOW
        self.BLUE = Fore.BLUE
        self.CYAN = Fore.CYAN
        self.ORANGE = Fore.RED + Style.BRIGHT # Approx
        self.PURPLE = Fore.MAGENTA
        
        # New Visual Assets
        self.PIPE = "│" 
        self.BRANCH_MARKER = "├──"
        self.LAST_BRANCH_MARKER = "└──"
        
        # Theme Configuration
        self.THEME = {
            'info':     {'icon': '•', 'color': Fore.BLUE, 'label': 'INFO'},
            'success':  {'icon': '✓', 'color': Fore.GREEN, 'label': 'DONE'},
            'error':    {'icon': '✕', 'color': Fore.RED, 'label': 'FAIL'},
            'warning':  {'icon': '⚠', 'color': Fore.YELLOW, 'label': 'WARN'},
            'input':    {'icon': '?', 'color': Fore.MAGENTA, 'label': 'INPUT'},
            'debug':    {'icon': '○', 'color': Fore.BLACK + Style.BRIGHT, 'label': 'DEBUG'},
            'critical': {'icon': '☠', 'color': Fore.RED + Style.BRIGHT, 'label': 'CRIT'},
            'process':  {'icon': '⟳', 'color': Fore.CYAN, 'label': 'WORK'},
            'action':   {'icon': '»', 'color': Fore.WHITE, 'label': 'EXEC'},
        }

    def _get_time(self) -> str:
        """Returns a dimmed timestamp string"""
        return f"{Fore.BLACK}{Style.BRIGHT}{datetime.now().strftime('%H:%M:%S')}{self.RESET}"

    def _should_log(self, message_level: LogLevel) -> bool:
        return message_level.value >= self.level.value

    def _write(self, message: str, color: str = ""):
        """Thread-safe write to stdout"""
        with self.write_lock:
            if color:
                print(f"{color}{message}{Style.RESET_ALL}")
            else:
                print(message)
            sys.stdout.flush()

    def _truncate(self, text: str, max_length: int = 50) -> str:
        """Truncate text if it's too long"""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def _format_line(self, theme_key: str, message: str, value_color: str = Fore.WHITE) -> str:
        """Internal formatter for the Column/Pipe style"""
        theme = self.THEME.get(theme_key, self.THEME['info'])
        color = theme['color']
        label = theme['label'].center(5)
        icon = theme['icon']
        
        # Apply truncation to the message
        truncated_message = self._truncate(message)
        
        return (
            f"{self._get_time()} {self.GRAY}{self.PIPE}{self.RESET} "
            f"{color}{Style.BRIGHT}{label}{self.RESET} "
            f"{self.GRAY}{self.PIPE}{self.RESET} "
            f"{color}{icon}{self.RESET} {value_color}{truncated_message}"
        )

    # === Main status messages ===
    
    def status(self, action: str, result: str, result_color: str = None):
        """
        Log a main status line.
        Redesigned to: TIME | EXEC | Action -> Result
        """
        if result_color is None:
            result_color = self.GREEN
        
        msg = f"{self.WHITE}{action} -> {result_color}{result}"
        self._write(self._format_line('action', msg))

    def waiting(self, message: str):
        """Log a waiting/processing status"""
        self._write(self._format_line('process', f"{message}...", value_color=self.CYAN))

    def question(self, message: str):
        """Log an input/question prompt"""
        self._write(self._format_line('input', message))

    # === Tree-style detail messages ===

    def tree(self, items: List[tuple], indent: int = 2):
        """
        Log multiple items in tree format.
        Adapts the column style to the tree.
        """
        # Spacers to align tree under the message column
        # Timestamp (8) + " | " (3) + Label (5) + " | " (3) = 19 chars approx
        timestamp_spacer = " " * 8
        label_spacer = " " * 5     
        prefix_padding = f"{timestamp_spacer} {self.GRAY}{self.PIPE}{self.RESET} {label_spacer} {self.GRAY}{self.PIPE}{self.RESET}"
        
        for i, item in enumerate(items):
            label = item[0]
            value = item[1]
            color = item[2] if len(item) > 2 else self.WHITE
            
            is_last = (i == len(items) - 1)
            connector = self.LAST_BRANCH_MARKER if is_last else self.BRANCH_MARKER
            
            # The tree connects strictly under the message area
            output = (
                f"{prefix_padding}   "
                f"{self.GRAY}{connector}{self.RESET} "
                f"{self.WHITE}{label}: {color}{value}{self.RESET}"
            )
            self._write(output)

    def branch(self, label: str, value: str, is_last: bool = False, color: str = None, indent: int = 2):
        """Log a single tree branch item"""
        if color is None:
            color = self.WHITE
            
        # Re-use tree logic for single item
        self.tree([(label, value, color)], indent)

    # === Standard log levels ===

    def info(self, message: str):
        if self._should_log(LogLevel.INFO):
            self._write(self._format_line('info', message))

    def success(self, message: str):
        if self._should_log(LogLevel.SUCCESS):
            self._write(self._format_line('success', message))

    def warning(self, message: str):
        if self._should_log(LogLevel.WARNING):
            self._write(self._format_line('warning', message))

    def error(self, message: str):
        if self._should_log(LogLevel.ERROR):
            self._write(self._format_line('error', message))

    def debug(self, message: str):
        if self._should_log(LogLevel.DEBUG):
            self._write(self._format_line('debug', message, value_color=Fore.BLACK + Style.BRIGHT))

    def critical(self, message: str):
        if self._should_log(LogLevel.CRITICAL):
            self._write(self._format_line('critical', message))

    def process(self, message: str):
        self._write(self._format_line('process', message, value_color=self.CYAN))

    def action(self, message: str):
        self._write(self._format_line('action', message))

    def failure(self, message: str):
        self.error(message)

    def ask(self, message: str):
        self.question(message)

    # === Token generation specific ===

    def token_generated(self, token: str, gen_time: float, display_name: str = None,
                        captcha_time: float = None, humanize_time: float = None, 
                        verify_time: float = None, total_time: float = None, 
                        status: str = "Email Verified"):
        """
        Log a complete token generation result in the new tree format.
        """
        # 1. Main header line
        self.status("Generating Token", "Token Generated!", self.GREEN + Style.BRIGHT)
        
        # 2. Prepare data for tree
        # Mask token
        if len(token) > 10:
            masked_token = f"{token[:6]}***{token[-4:]}"
        else:
            masked_token = token[:4] + "***"
        
        items = [("Token", masked_token, self.MAGENTA)]
        
        if display_name is not None:
            items.append(("Display Name", display_name, self.CYAN))
        if gen_time is not None:
            items.append(("Generation Time", f"{gen_time:.2f}s", self.WHITE))
        if captcha_time is not None:
            items.append(("hCaptcha Time", f"{captcha_time:.2f}s", self.WHITE))
        if humanize_time is not None:
            items.append(("Humanize Time", f"{humanize_time:.2f}s", self.WHITE))
        if verify_time is not None:
            items.append(("Verify Time", f"{verify_time:.2f}s", self.WHITE))
        if total_time is not None:
            items.append(("Total Time", f"{total_time:.2f}s", self.WHITE))
        
        items.append(("Status", status, self.GREEN))
        
        # 3. Call tree renderer
        self.tree(items)


# Global logger instance
log = TreeLogger()


# Backward compatible Logger class
class Logger(TreeLogger):
    """Backward compatible Logger class"""
    def __init__(self, level: LogLevel = LogLevel.DEBUG):
        super().__init__(level=level, prefix="NEXUS")
