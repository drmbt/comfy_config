#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Optional

def setup_symlinks(comfy_path: str, project_root: Path) -> None:
    """Set up symlinks between project directories and ComfyUI workspace.
    
    Args:
        comfy_path: Path to ComfyUI workspace
        project_root: Path to project root directory
    """
    if not comfy_path:
        raise ValueError("ComfyUI workspace path not provided")
    
    comfy_path = os.path.expanduser(comfy_path)
    print(f"Setting up symlinks for ComfyUI workspace at: {comfy_path}")
    
    # Main directories to link
    dirs_to_link = ["input", "output", "models"]
    _setup_directory_symlinks(comfy_path, project_root, dirs_to_link)
    
    # Handle user/default settings
    _setup_settings_symlinks(comfy_path, project_root)

def _setup_directory_symlinks(comfy_path: str, project_root: Path, dirs: List[str]) -> None:
    """Create symlinks for main directories."""
    for dir_name in dirs:
        target = Path(comfy_path) / dir_name
        source = project_root / dir_name
        
        # Remove existing symlink/directory
        if target.exists() or target.is_symlink():
            print(f"Removing existing {target}")
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        
        # Create symlink if source exists
        if source.is_dir():
            print(f"Creating symlink for {dir_name}")
            target.symlink_to(source, target_is_directory=True)
        else:
            print(f"Warning: Source directory {source} does not exist")

def _setup_settings_symlinks(comfy_path: str, project_root: Path) -> None:
    """Set up symlinks for settings files and workflows."""
    user_default_target = Path(comfy_path) / "user" / "default"
    user_default_source = project_root / "user" / "default"
    
    # Create target directory
    user_default_target.mkdir(parents=True, exist_ok=True)
    
    # Handle workflows directory
    workflows_source = user_default_source / "workflows"
    workflows_target = user_default_target / "workflows"
    
    if workflows_source.is_dir():
        if workflows_target.exists() or workflows_target.is_symlink():
            print(f"Removing existing {workflows_target}")
            if workflows_target.is_dir() and not workflows_target.is_symlink():
                shutil.rmtree(workflows_target)
            else:
                workflows_target.unlink()
        
        print("Creating symlink for user/default/workflows")
        workflows_target.symlink_to(workflows_source, target_is_directory=True)
    else:
        print("Warning: Workflows directory does not exist in source")
    
    # Handle settings files
    settings_files = ["comfy.settings.json", "jnodes.settings.json"]
    for settings_file in settings_files:
        source_file = user_default_source / settings_file
        target_file = user_default_target / settings_file
        
        if source_file.is_file():
            if target_file.exists() or target_file.is_symlink():
                print(f"Removing existing {target_file}")
                target_file.unlink()
            
            print(f"Creating symlink for user/default/{settings_file}")
            target_file.symlink_to(source_file)
        else:
            print(f"Warning: Settings file {settings_file} does not exist in source")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments for standalone usage."""
    parser = argparse.ArgumentParser(
        description='Set up symlinks between project directories and ComfyUI workspace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up symlinks using current directory as project root
  %(prog)s --comfy-path /path/to/comfy
  
  # Set up symlinks with specific project root
  %(prog)s --comfy-path /path/to/comfy --project-root /path/to/project
"""
    )
    
    parser.add_argument(
        '--comfy-path',
        required=True,
        help='Path to ComfyUI workspace'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Path to project root directory (default: current directory)'
    )
    
    return parser.parse_args()

def main():
    """Main function for standalone usage."""
    try:
        args = parse_args()
        setup_symlinks(args.comfy_path, args.project_root)
        print("Symlink setup completed successfully!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 