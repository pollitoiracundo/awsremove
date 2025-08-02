"""
Color schemes and ANSI color codes for retro terminal UI.
"""

from enum import Enum


class Color:
    """ANSI color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class ColorScheme:
    """Color scheme definitions."""
    
    def __init__(self, name: str):
        self.name = name
    
    @property
    def header(self) -> str:
        return Color.BRIGHT_CYAN + Color.BOLD
    
    @property
    def menu_title(self) -> str:
        return Color.BRIGHT_YELLOW + Color.BOLD
    
    @property
    def menu_item(self) -> str:
        return Color.BRIGHT_WHITE
    
    @property
    def menu_selected(self) -> str:
        return Color.BG_CYAN + Color.BLACK + Color.BOLD
    
    @property
    def menu_disabled(self) -> str:
        return Color.BRIGHT_BLACK
    
    @property
    def accent(self) -> str:
        return Color.BRIGHT_MAGENTA
    
    @property
    def success(self) -> str:
        return Color.BRIGHT_GREEN
    
    @property
    def warning(self) -> str:
        return Color.BRIGHT_YELLOW
    
    @property
    def error(self) -> str:
        return Color.BRIGHT_RED
    
    @property
    def info(self) -> str:
        return Color.BRIGHT_BLUE
    
    @property
    def border(self) -> str:
        return Color.BRIGHT_CYAN


class NeonScheme(ColorScheme):
    """Neon 80s color scheme."""
    
    def __init__(self):
        super().__init__("neon")
    
    @property
    def header(self) -> str:
        return Color.BRIGHT_MAGENTA + Color.BOLD
    
    @property
    def menu_selected(self) -> str:
        return Color.BG_MAGENTA + Color.BRIGHT_WHITE + Color.BOLD
    
    @property
    def accent(self) -> str:
        return Color.BRIGHT_CYAN


class MatrixScheme(ColorScheme):
    """Matrix green color scheme."""
    
    def __init__(self):
        super().__init__("matrix")
    
    @property
    def header(self) -> str:
        return Color.BRIGHT_GREEN + Color.BOLD
    
    @property
    def menu_title(self) -> str:
        return Color.BRIGHT_GREEN + Color.BOLD
    
    @property
    def menu_selected(self) -> str:
        return Color.BG_GREEN + Color.BLACK + Color.BOLD
    
    @property
    def accent(self) -> str:
        return Color.GREEN
    
    @property
    def border(self) -> str:
        return Color.BRIGHT_GREEN


class ClassicScheme(ColorScheme):
    """Classic terminal colors."""
    
    def __init__(self):
        super().__init__("classic")
    
    @property
    def header(self) -> str:
        return Color.WHITE + Color.BOLD
    
    @property
    def menu_title(self) -> str:
        return Color.WHITE + Color.BOLD
    
    @property
    def menu_selected(self) -> str:
        return Color.REVERSE + Color.BOLD
    
    @property
    def accent(self) -> str:
        return Color.WHITE


def get_color_scheme(scheme_name: str) -> ColorScheme:
    """Get color scheme by name."""
    schemes = {
        'neon': NeonScheme(),
        'matrix': MatrixScheme(),
        'classic': ClassicScheme(),
    }
    return schemes.get(scheme_name, NeonScheme())