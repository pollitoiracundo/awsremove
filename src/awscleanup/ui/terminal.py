"""
Terminal utilities for 80s-style interface.
"""

import os
import sys
import termios
import tty
import time
import random
from typing import Tuple, List, Optional


class Terminal:
    """Terminal control utilities."""
    
    def __init__(self):
        self.width, self.height = self.get_terminal_size()
    
    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        """Get terminal dimensions."""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except Exception:
            return 80, 24  # fallback
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    @staticmethod
    def move_cursor(x: int, y: int):
        """Move cursor to position."""
        print(f'\033[{y};{x}H', end='')
    
    @staticmethod
    def hide_cursor():
        """Hide the cursor."""
        print('\033[?25l', end='')
    
    @staticmethod
    def show_cursor():
        """Show the cursor."""
        print('\033[?25h', end='')
    
    @staticmethod
    def save_cursor():
        """Save cursor position."""
        print('\033[s', end='')
    
    @staticmethod
    def restore_cursor():
        """Restore cursor position."""
        print('\033[u', end='')
    
    @staticmethod
    def get_key() -> str:
        """Get a single keypress."""
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                # Try to use cbreak mode for single character input
                if hasattr(tty, 'cbreak'):
                    tty.cbreak(fd)
                else:
                    # Fallback for systems without cbreak
                    tty.setraw(fd)
                
                key = sys.stdin.read(1)
                
                # Handle special keys (arrows, etc.)
                if key == '\033':  # ESC sequence
                    try:
                        key += sys.stdin.read(2)
                    except:
                        return 'ESCAPE'
                    
                    if key == '\033[A':
                        return 'UP'
                    elif key == '\033[B':
                        return 'DOWN'
                    elif key == '\033[C':
                        return 'RIGHT'
                    elif key == '\033[D':
                        return 'LEFT'
                    elif key == '\033[H':
                        return 'HOME'
                    elif key == '\033[F':
                        return 'END'
                elif key == '\n' or key == '\r':
                    return 'ENTER'
                elif key == '\x7f' or key == '\x08':
                    return 'BACKSPACE'
                elif key == '\x1b':
                    return 'ESCAPE'
                elif key == ' ':
                    return 'SPACE'
                elif key == '\t':
                    return 'TAB'
                elif ord(key) == 3:  # Ctrl+C
                    return 'CTRL_C'
                elif ord(key) == 17:  # Ctrl+Q
                    return 'CTRL_Q'
                
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (ImportError, AttributeError, OSError):
            # Fallback for systems without termios/tty support
            return input("Press Enter to continue: ").strip() or 'ENTER'


class RetroEffects:
    """80s-style visual effects."""
    
    @staticmethod
    def typewriter_print(text: str, delay: float = 0.03):
        """Print text with typewriter effect."""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    
    @staticmethod
    def matrix_rain(width: int, height: int, duration: float = 3.0):
        """Create matrix-style falling characters effect."""
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        
        # Initialize columns
        columns = []
        for _ in range(width):
            columns.append({
                'chars': [],
                'speed': random.uniform(0.1, 0.3),
                'last_update': time.time()
            })
        
        start_time = time.time()
        Terminal.hide_cursor()
        
        try:
            while time.time() - start_time < duration:
                Terminal.clear_screen()
                
                for col_idx, column in enumerate(columns):
                    current_time = time.time()
                    
                    # Add new characters at top
                    if random.random() < 0.1:
                        column['chars'].insert(0, {
                            'char': random.choice(chars),
                            'y': 0,
                            'brightness': 1.0
                        })
                    
                    # Update character positions
                    if current_time - column['last_update'] > column['speed']:
                        for char_data in column['chars']:
                            char_data['y'] += 1
                            char_data['brightness'] *= 0.95
                        
                        # Remove characters that fell off screen
                        column['chars'] = [c for c in column['chars'] if c['y'] < height]
                        column['last_update'] = current_time
                    
                    # Draw characters
                    for char_data in column['chars']:
                        if 0 <= char_data['y'] < height:
                            Terminal.move_cursor(col_idx + 1, char_data['y'] + 1)
                            brightness = max(0, min(1, char_data['brightness']))
                            if brightness > 0.7:
                                print(f'\033[92m{char_data["char"]}\033[0m', end='')
                            elif brightness > 0.4:
                                print(f'\033[32m{char_data["char"]}\033[0m', end='')
                            else:
                                print(f'\033[90m{char_data["char"]}\033[0m', end='')
                
                time.sleep(0.05)
        finally:
            Terminal.show_cursor()
    
    @staticmethod
    def scan_lines(width: int, height: int, duration: float = 2.0):
        """Create scan line effect."""
        start_time = time.time()
        Terminal.hide_cursor()
        
        try:
            while time.time() - start_time < duration:
                for y in range(height):
                    Terminal.move_cursor(1, y + 1)
                    print('\033[90m' + '█' * width + '\033[0m')
                    time.sleep(duration / height)
                    Terminal.move_cursor(1, y + 1)
                    print(' ' * width)
        finally:
            Terminal.show_cursor()
    
    @staticmethod
    def glitch_text(text: str, intensity: float = 0.1) -> str:
        """Add glitch effect to text."""
        if random.random() > intensity:
            return text
        
        glitch_chars = "!@#$%^&*(){}[]|\\:;\"'<>?/~`"
        result = ""
        
        for char in text:
            if char.isalnum() and random.random() < intensity:
                result += random.choice(glitch_chars)
            else:
                result += char
        
        return result