#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.logging import RichHandler
import logging
from dotenv import load_dotenv

# Setup rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

# Get root directory (parent of _utils)
ROOT_DIR = Path(__file__).parent.parent.absolute()
ENV_FILE = ROOT_DIR / '.env'

# Load environment variables from parent directory's .env
if ENV_FILE.exists():
    logger.info(f"Loading environment variables from {ENV_FILE}")
    load_dotenv(ENV_FILE)
else:
    logger.warning(f"No .env file found at {ENV_FILE}")

def get_available_snapshots(snapshots_dir: Path) -> List[str]:
    """Get list of available snapshot files in the snapshots directory."""
    if not snapshots_dir.exists():
        return []
    return [f.name for f in snapshots_dir.glob('*.json')]

def get_user_selection(prompt: str, default: Optional[str] = None, options: Optional[List[str]] = None) -> Optional[str]:
    """Get user selection with optional default and list of options."""
    if options:
        print("\nAvailable options:")
        for i, option in enumerate(options, 1):
            prefix = '»' if option == default else ' '
            print(f" {prefix} {option}")
    
    if default:
        response = input(f"{prompt} (default: {default}): ").strip()
        return response if response else default
    else:
        response = input(f"{prompt} (empty to skip): ").strip()
        return response if response else None

def setup_manager_config(comfy_path: str, config_source: Optional[str] = None, skip_prompt: bool = False) -> None:
    """Copy ComfyUI-Manager configuration."""
    target_dir = Path(comfy_path) / "user" / "default" / "ComfyUI-Manager"
    target_file = target_dir / "config.ini"
    
    logger.info(f"Received config_source: {config_source}")
    
    if skip_prompt:
        if not config_source:
            logger.info("No ComfyUI-Manager config.ini specified, skipping configuration")
            return
        source_path = Path(os.path.expanduser(config_source))
        logger.info(f"Checking skip-prompt path: {source_path}")
        if not source_path.is_file():
            logger.info(f"ComfyUI-Manager config.ini not found at {source_path}, skipping configuration")
            return
    else:
        # In interactive mode, use config_source as default if provided
        source_path = None
        if config_source:
            default_path = os.path.expanduser(config_source)
            logger.info(f"Checking interactive default path: {default_path}")
            if Path(default_path).is_file():
                logger.info(f"Found default ComfyUI-Manager config.ini at: {default_path}")
                source_path = Path(default_path)
            else:
                logger.warning(f"Default config.ini not found at: {default_path}")
        
        if not source_path:
            logger.info("No default ComfyUI-Manager config.ini found")
            response = get_user_selection("Enter path to ComfyUI-Manager config.ini")
            if response:
                source_path = Path(os.path.expanduser(response))
        
        if not source_path:
            logger.info("Skipping ComfyUI-Manager configuration")
            return
        
        if not source_path.is_file():
            logger.warning(f"Config.ini file not found at {source_path}")
            return
    
    # Create target directory and copy config
    target_dir.mkdir(parents=True, exist_ok=True)
    if target_file.exists():
        logger.info(f"Removing existing config.ini at {target_file}")
        target_file.unlink()
    
    shutil.copy2(source_path, target_file)
    logger.info(f"Copied ComfyUI-Manager config.ini to {target_file}")

def restore_snapshot(comfy_path: str, snapshot_path: Optional[str] = None, skip_prompt: bool = False) -> None:
    """Restore ComfyUI snapshot using comfy node restore-snapshot."""
    if skip_prompt:
        if not snapshot_path:
            logger.info("No snapshot specified, skipping restore")
            return
        source_path = Path(os.path.expanduser(snapshot_path))
        if not source_path.is_file():
            logger.info(f"Snapshot {source_path} not found, skipping restore")
            return
    else:
        # Get available snapshots from the snapshots directory
        snapshots_dir = Path(comfy_path) / "user" / "default" / "ComfyUI-Manager" / "snapshots"
        available_snapshots = get_available_snapshots(snapshots_dir)
        
        # In interactive mode, use snapshot_path as default if provided
        source_path = None
        if snapshot_path:
            default_path = os.path.expanduser(snapshot_path)
            if available_snapshots:
                response = get_user_selection(
                    "Select snapshot to restore",
                    default=os.path.basename(default_path),
                    options=available_snapshots
                )
                if response:
                    source_path = snapshots_dir / response
            else:
                response = get_user_selection(
                    "Enter path to snapshot file",
                    default=default_path
                )
                if response:
                    source_path = Path(os.path.expanduser(response))
        else:
            if available_snapshots:
                response = get_user_selection(
                    "Select snapshot to restore",
                    options=available_snapshots
                )
                if response:
                    source_path = snapshots_dir / response
            else:
                response = get_user_selection("Enter path to snapshot file")
                if response:
                    source_path = Path(os.path.expanduser(response))
        
        if not source_path:
            logger.info("Skipping snapshot restore")
            return
        
        if not source_path.is_file():
            logger.warning(f"Snapshot file not found at {source_path}")
            return
    
    # Restore snapshot using comfy node
    try:
        logger.info(f"Restoring snapshot from {source_path}")
        subprocess.run(['comfy', 'node', 'restore-snapshot', str(source_path)], check=True)
        logger.info("Snapshot restored successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restore snapshot: {e}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Manage ComfyUI-Manager configuration and snapshots'
    )
    
    parser.add_argument('--comfy-path', required=True, help='Path to ComfyUI workspace')
    parser.add_argument('--manager-config', help='Path to ComfyUI-Manager config.ini')
    parser.add_argument('--snapshot', help='Path to snapshot file to restore')
    parser.add_argument('--skip-prompt', action='store_true', help='Skip interactive prompts')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Log environment variables for debugging
    logger.info("Environment variables:")
    logger.info(f"MANAGER_CONFIG: {os.getenv('MANAGER_CONFIG')}")
    logger.info(f"SNAPSHOT_PATH: {os.getenv('SNAPSHOT_PATH')}")
    logger.info(f"COMFY_PATH: {os.getenv('COMFY_PATH')}")
    
    # Setup manager configuration
    setup_manager_config(args.comfy_path, args.manager_config, args.skip_prompt)
    
    # Handle snapshot restore if requested
    restore_snapshot(args.comfy_path, args.snapshot, args.skip_prompt)

if __name__ == "__main__":
    main() 