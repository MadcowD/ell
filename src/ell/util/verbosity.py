import sys
import hashlib
import shutil
import textwrap
from typing import Dict, Tuple, List, Any, Optional
from colorama import Fore, Style, init
from ell.types import Message
from ell.configurator import config
import logging
from functools import lru_cache

from ell.types.message import LMP

# Initialize colorama
init(autoreset=True)

# Define colors and styles
ELL_COLORS = {k: v for k, v in vars(Fore).items() if k not in ['RESET', 'BLACK', 'LIGHTBLACK_EX']}
BOLD = Style.BRIGHT
UNDERLINE = '\033[4m'
RESET = Style.RESET_ALL
SYSTEM_COLOR = Fore.CYAN
USER_COLOR = Fore.GREEN
ASSISTANT_COLOR = Fore.YELLOW
PIPE_COLOR = Fore.BLUE

# Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def compute_color(invoking_lmp: LMP) -> str:
    """Compute and cache a consistent color for a given LMP."""
    name_hash = hashlib.md5(invoking_lmp.__name__.encode()).hexdigest()
    color_index = int(name_hash, 16) % len(ELL_COLORS)
    return list(ELL_COLORS.values())[color_index]

def format_arg(arg: Any, max_length: int = 8) -> str:
    """Format an argument for display with customizable max length."""
    str_arg = str(arg)
    return f"{Fore.MAGENTA}{str_arg[:max_length]}..{Style.RESET_ALL}" if len(str_arg) > max_length else f"{Fore.MAGENTA}{str_arg}{Style.RESET_ALL}"

def format_kwarg(key: str, value: Any, max_length: int = 8) -> str:
    """Format a keyword argument for display with customizable max length."""
    return f"{Style.DIM}{key}{Style.RESET_ALL}={Fore.MAGENTA}{str(value)[:max_length]}..{Style.RESET_ALL}"

def get_terminal_width() -> int:
    """Get the terminal width, defaulting to 80 if it can't be determined."""
    try:
        return shutil.get_terminal_size((80, 20)).columns
    except Exception:
        logger.warning("Unable to determine terminal size. Defaulting to 80 columns.")
        return 80

def wrap_text_with_prefix(text: str, width: int, prefix: str, subsequent_prefix: str, text_color: str) -> List[str]:
    """Wrap text while preserving the prefix and color for each line."""
    paragraphs = text.split('\n')
    wrapped_paragraphs = [textwrap.wrap(p, width=width - len(prefix)) for p in paragraphs]
    wrapped_lines = [line for paragraph in wrapped_paragraphs for line in paragraph]
    result = [f"{prefix}{RESET}{wrapped_lines[0]}{RESET}" if wrapped_lines else f"{prefix}{text_color}{RESET}"]
    result.extend([f"{subsequent_prefix}{RESET}{line}{RESET}" for line in wrapped_lines[1:]])
    return result

def print_wrapped_messages(messages: List[Message], max_role_length: int, color: str, wrap_width: Optional[int] = None):
    """Print wrapped messages with proper indentation, customizable wrap width, and consistent ASCII piping."""
    terminal_width = get_terminal_width()
    prefix = f"{PIPE_COLOR}│   "
    role_prefix = ' ' * (max_role_length + 2)
    subsequent_prefix = f"{PIPE_COLOR}│   {role_prefix}"
    wrapping_width = wrap_width or (terminal_width - len(prefix))

    for i, message in enumerate(messages):
        role = message.role
        text = message.content[0].text or "" # TODO: message repr
        role_color = SYSTEM_COLOR if role == "system" else USER_COLOR if role == "user" else ASSISTANT_COLOR
        
        role_line = f"{prefix}{role_color}{role.rjust(max_role_length)}: {RESET}"
        wrapped_lines = wrap_text_with_prefix(text, wrapping_width - len(role_prefix), '', subsequent_prefix, role_color)
        
        print(f"{role_line}{wrapped_lines[0]}")
        for line in wrapped_lines[1:]:
            print(line)
        
        if i < len(messages) - 1:
            print(f"{PIPE_COLOR}│{RESET}")

def model_usage_logger_pre(
    invoking_lmp: LMP,
    lmp_args: Tuple,
    lmp_kwargs: Dict,
    lmp_hash: str,
    messages: List[Message],
    color: str = "",
    arg_max_length: int = 8
):
    """Log model usage before execution with customizable argument display length and ASCII box."""
    color = color or compute_color(invoking_lmp)
    formatted_args = [format_arg(arg, arg_max_length) for arg in lmp_args]
    formatted_kwargs = [format_kwarg(key, lmp_kwargs[key], arg_max_length) for key in lmp_kwargs]
    formatted_params = ', '.join(formatted_args + formatted_kwargs)
    
    terminal_width = get_terminal_width()
    
    logger.info(f"Invoking LMP: {invoking_lmp.__name__} (hash: {lmp_hash[:8]})")
    
    print(f"{PIPE_COLOR}╔{'═' * (terminal_width - 2)}╗{RESET}")
    print(f"{PIPE_COLOR}║ {color}{BOLD}{UNDERLINE}{invoking_lmp.__name__}{RESET}{color}({formatted_params}){RESET}")
    print(f"{PIPE_COLOR}╠{'═' * (terminal_width - 2)}╣{RESET}")
    print(f"{PIPE_COLOR}║ {BOLD}Prompt:{RESET}")
    print(f"{PIPE_COLOR}╟{'─' * (terminal_width - 2)}╢{RESET}")

    max_role_length = max(len("assistant"), max(len(message.role) for message in messages))
    print_wrapped_messages(messages, max_role_length, color)

def model_usage_logger_post_start(color: str = "", n: int = 1):
    """Log the start of model output with ASCII box."""
    terminal_width = get_terminal_width()
    print(f"{PIPE_COLOR}╟{'─' * (terminal_width - 2)}╢{RESET}")
    print(f"{PIPE_COLOR}║ {BOLD}Output{f'[0 of {n}]' if n > 1 else ''}:{RESET}")
    print(f"{PIPE_COLOR}╟{'─' * (terminal_width - 2)}╢{RESET}")
    print(f"{PIPE_COLOR}│   {ASSISTANT_COLOR}assistant: {RESET}", end='')
    sys.stdout.flush()

from contextlib import contextmanager

@contextmanager
def model_usage_logger_post_intermediate(color: str = "", n: int = 1):
    """Context manager to log intermediate model output without wrapping, only indenting if necessary."""
    terminal_width = get_terminal_width()
    prefix = f"{PIPE_COLOR}│   "
    subsequent_prefix = f"{PIPE_COLOR}│   {' ' * (len('assistant: '))}"
    chars_printed = len(subsequent_prefix)

    def log_stream_chunk(stream_chunk: str, is_refusal: bool = False):
        nonlocal chars_printed
        if stream_chunk:
            lines = stream_chunk.split('\n')
            for i, line in enumerate(lines):
                if chars_printed + len(line) > terminal_width - 6:
                    print()
                    if i == 0:
                        print(subsequent_prefix, end='')
                        chars_printed = len(prefix)
                    else:
                        print(subsequent_prefix, end='')
                        chars_printed = len(subsequent_prefix)
                    print(line.lstrip(), end='')
                else:
                    print(line, end='')
                chars_printed += len(line)

                if i < len(lines) - 1:
                    print()
                    print(subsequent_prefix, end='')
                    chars_printed = len(subsequent_prefix)  # Reset for new line
            sys.stdout.flush()

    try:
        yield log_stream_chunk
    finally:
        pass
def model_usage_logger_post_end():
    """Log the end of model output with ASCII box closure."""
    terminal_width = get_terminal_width()
    print(f"\n{PIPE_COLOR}╚{'═' * (terminal_width - 2)}╝{RESET}")

def set_log_level(level: str):
    """Set the logging level."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    logger.setLevel(numeric_level)

# Example usage
# set_log_level('DEBUG')