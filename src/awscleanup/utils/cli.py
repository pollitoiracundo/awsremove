"""
Command line interface utilities.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def check_aws_cli() -> bool:
    """Check if AWS CLI is available."""
    try:
        subprocess.run(['aws', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description='AWS Resource Cleanup Tool - Retro Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Interactive mode
  %(prog)s --profile my-dev          # Use specific profile
  %(prog)s --dry-run                 # Dry run mode
  %(prog)s --regions us-east-1       # Specific regions only
  %(prog)s --color-scheme matrix     # Matrix color scheme

Color Schemes:
  neon     - Neon 80s style (default)
  matrix   - Matrix green
  classic  - Classic terminal colors
        """
    )
    
    parser.add_argument(
        '--profile',
        help='AWS profile to use'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--regions',
        nargs='+',
        help='Specific regions to scan (default: all)'
    )
    
    parser.add_argument(
        '--color-scheme',
        choices=['neon', 'matrix', 'classic'],
        default='neon',
        help='Color scheme for the interface (default: neon)'
    )
    
    parser.add_argument(
        '--no-splash',
        action='store_true',
        help='Skip the splash screen'
    )
    
    parser.add_argument(
        '--easter-eggs',
        action='store_true',
        help='Enable easter eggs'
    )
    
    return parser


def validate_environment() -> None:
    """Validate the environment before running."""
    if not check_aws_cli():
        print("❌ AWS CLI not found. Please install and configure AWS CLI first.")
        print("\nInstallation instructions:")
        print("  pip install awscli")
        print("  aws configure")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher is required.")
        sys.exit(1)