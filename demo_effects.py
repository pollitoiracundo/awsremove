#!/usr/bin/env python3
"""
Demo script to showcase retro terminal effects.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from awscleanup.ui.terminal import Terminal, RetroEffects
from awscleanup.ui.colors import get_color_scheme, Color


def main():
    """Demo the retro effects."""
    terminal = Terminal()
    colors = get_color_scheme("neon")
    
    print(f"{colors.header}🌈 AWS CLEANUP TOOL - RETRO EFFECTS DEMO 🌈{Color.RESET}")
    print()
    
    # Typewriter effect
    print(f"{colors.accent}Demonstrating typewriter effect:{Color.RESET}")
    RetroEffects.typewriter_print("Welcome to the 80s, dude! This is totally radical! 🕹️", 0.05)
    time.sleep(1)
    
    # Glitch effect
    print(f"\n{colors.accent}Demonstrating glitch effect:{Color.RESET}")
    original_text = "System status: All systems nominal"
    for i in range(5):
        glitched = RetroEffects.glitch_text(original_text, 0.3)
        print(f"\r{colors.error}{glitched}{Color.RESET}", end="", flush=True)
        time.sleep(0.2)
    print(f"\r{colors.success}{original_text}{Color.RESET}")
    time.sleep(1)
    
    # Color scheme demo
    schemes = ["neon", "matrix", "classic"]
    print(f"\n{colors.accent}Color schemes available:{Color.RESET}")
    for scheme_name in schemes:
        scheme = get_color_scheme(scheme_name)
        print(f"  {scheme.header}● {scheme_name.upper()}{Color.RESET} - " +
              f"{scheme.accent}Accent{Color.RESET} | " +
              f"{scheme.success}Success{Color.RESET} | " +
              f"{scheme.warning}Warning{Color.RESET} | " +
              f"{scheme.error}Error{Color.RESET}")
    
    print(f"\n{colors.info}Matrix rain effect in 3 seconds...{Color.RESET}")
    time.sleep(3)
    
    # Matrix rain effect
    RetroEffects.matrix_rain(terminal.width, terminal.height, 5.0)
    
    terminal.clear_screen()
    print(f"{colors.success}Demo complete! Ready to clean some cloud resources! ☁️{Color.RESET}")
    print(f"{colors.info}Run './aws_cleanup_retro.py' to start the real application.{Color.RESET}")


if __name__ == "__main__":
    main()