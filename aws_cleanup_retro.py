#!/usr/bin/env python3
"""
AWS Resource Cleanup Tool - Retro Edition
Interactive 80s-style terminal interface for safely cleaning up AWS resources.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from awscleanup.core.application import AWSCleanupApp
from awscleanup.utils.cli import setup_argument_parser, validate_environment


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Validate environment
    validate_environment()
    
    # Create and run application
    app = AWSCleanupApp()
    
    # Override settings based on command line args
    if args.color_scheme:
        app.settings.ui_settings['color_scheme'] = args.color_scheme
        app.ui = type(app.ui)(args.color_scheme)
    
    if args.easter_eggs:
        app.settings.ui_settings['easter_eggs'] = True
    
    if args.no_splash:
        app.ui.show_splash_screen = lambda: None
    
    # Run the application
    app.run(profile=args.profile)


if __name__ == '__main__':
    main()