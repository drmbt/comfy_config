#!/usr/bin/env python3
import sys
import shutil
import argparse
from pathlib import Path
from typing import Optional

def setup_manager_config(comfy_path: str, project_root: Path) -> None:
    """Set up ComfyUI-Manager configuration.
    
    Args:
        comfy_path: Path to ComfyUI workspace
        project_root: Path to project root directory
    """
    # Handle ComfyUI-Manager config.ini
    manager_config_source = project_root / "user" / "default" / "ComfyUI-Manager" / "config.ini"
    manager_config_target = Path(comfy_path) / "user" / "default" / "ComfyUI-Manager" / "config.ini"
    
    if manager_config_source.is_file():
        # Create target directory
        manager_config_target.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file/symlink
        if manager_config_target.exists() or manager_config_target.is_symlink():
            print(f"Removing existing {manager_config_target}")
            manager_config_target.unlink()
        
        print("Creating symlink for ComfyUI-Manager/config.ini")
        manager_config_target.symlink_to(manager_config_source)
    else:
        print("Warning: ComfyUI-Manager config.ini does not exist in source")

def handle_snapshot(project_root: Path) -> None:
    """Handle snapshot.json file.
    
    Args:
        project_root: Path to project root directory
    """
    snapshot_source = project_root / "snapshot.json"
    snapshot_target_dir = project_root / "ComfyUI-Manager" / "user" / "default" / "snapshots"
    
    if snapshot_source.is_file():
        # Create target directory
        snapshot_target_dir.mkdir(parents=True, exist_ok=True)
        
        print("Copying snapshot.json to ComfyUI-Manager snapshots directory")
        shutil.copy2(snapshot_source, snapshot_target_dir / "snapshot.json")
    else:
        print("Warning: snapshot.json does not exist in source directory")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments for standalone usage."""
    parser = argparse.ArgumentParser(
        description='Manage ComfyUI-Manager configuration and snapshots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up manager config using current directory as project root
  %(prog)s --comfy-path /path/to/comfy
  
  # Set up manager config and handle snapshot
  %(prog)s --comfy-path /path/to/comfy --project-root /path/to/project --snapshot
  
  # Only handle snapshot
  %(prog)s --project-root /path/to/project --snapshot-only
"""
    )
    
    parser.add_argument(
        '--comfy-path',
        help='Path to ComfyUI workspace (required unless --snapshot-only is used)'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Path to project root directory (default: current directory)'
    )
    parser.add_argument(
        '--snapshot',
        action='store_true',
        help='Handle snapshot.json file'
    )
    parser.add_argument(
        '--snapshot-only',
        action='store_true',
        help='Only handle snapshot.json file, skip manager config setup'
    )
    
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not args.snapshot_only and not args.comfy_path:
        print("Error: --comfy-path is required unless --snapshot-only is used", file=sys.stderr)
        sys.exit(1)

def main():
    """Main function for standalone usage."""
    try:
        args = parse_args()
        validate_args(args)
        
        if not args.snapshot_only:
            setup_manager_config(args.comfy_path, args.project_root)
        
        if args.snapshot or args.snapshot_only:
            handle_snapshot(args.project_root)
            
        print("Manager utilities completed successfully!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 