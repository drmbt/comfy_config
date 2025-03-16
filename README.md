# Comfy Config

A comprehensive configuration and management tool for ComfyUI installations and workflows.

## Features

- ComfyUI installation and workspace management
- Custom node management and dependency resolution
- Model management and automatic downloads
- Workflow conversion and execution
- Configuration management and environment setup

## Installation

```bash
pip install -r requirements.txt
```

## Core Dependencies

The core functionality requires:
- Python >= 3.9
- python-dotenv >= 1.0.0
- typer >= 0.9.0
- comfy-cli
- rich >= 13.0.0
- requests >= 2.31.0

## Optional Features

### Workflow Conversion (`workflow_to_api_json.py`)

The workflow conversion utility requires additional dependencies for browser automation:

```bash
pip install 'playwright>=1.41.0'
playwright install
```

This utility converts ComfyUI workflow JSON files into their API format equivalent using browser automation. The installation of Playwright is only necessary if you plan to use the workflow conversion feature.

#### Usage

Basic conversion:
```bash
python workflow_to_api_json.py --workflow input.json --output output.json
```

With automatic dependency installation (no prompts):
```bash
python workflow_to_api_json.py --workflow input.json --output output.json --skip-prompt
```

Additional options:
- `--show-browser`: Show browser window during conversion
- `--verbose`: Show detailed logs
- `--skip-downloads`: Skip downloading workflow models
- `--skip-prompt`: Skip all confirmation prompts
- `--port`: Specify ComfyUI server port (default: 8188)
- `--timeout`: Set operation timeout in seconds
- `--run`: Run the converted workflow after conversion

## Environment Setup

The tool supports various environment configurations through a `.env` file:

```env
COMFY_PATH=/path/to/comfyui
WORKSPACE_DIR=/path/to/workspace
INPUT_DIR=/path/to/input
OUTPUT_DIR=/path/to/output
```

## Project Structure

```
comfy_config/
├── README.md
├── requirements.txt
├── comfy_config.py          # Main configuration manager
└── _utils/
    └── workflow_to_api_json.py  # Workflow conversion utility
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License Type] - See LICENSE file for details 