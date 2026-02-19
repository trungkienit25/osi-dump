# osi-dump v2

A robust OpenStack data extraction and reporting tool. Rewritten with Clean Architecture, Pydantic, and Typer.

## Features

- **Efficiency**: Uses Two-Phase Fetch caching to avoid N+1 query problems.
- **Resilience**: Granular error handling ensures partial failures (e.g., one instance) don't crash the whole dump.
- **Unified Output**: Generates a single Excel file with multiple sheets (`osi_dump_report.xlsx`).
- **Flexible Delivery**: Supports sending reports to Telegram and S3.
- **Modern CLI**: User-friendly interface with progress spinners and rich formatting.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd osi-dump
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install .
    ```

## Configuration

### 1. Application Config (`config.json`)
Create a copy of `config.example.json` and adjust the settings:
```bash
cp config.example.json config.json
```
- Enable/Disable specific resources in the `"resources"` section.
- Configure delivery methods (Telegram, S3) in the `"output"` section.

### 2. Authentication (`clouds.yaml`)
Create a copy of `clouds.yaml.example` and fill in your OpenStack credentials:
```bash
cp clouds.yaml.example clouds.yaml
```

## Usage

Run the tool using the CLI:

```bash
# Basic usage
python -m osi_dump.cli --config config.json --auth clouds.yaml

# Verbose logging
python -m osi_dump.cli --config config.json --auth clouds.yaml -v

# Custom output directory
python -m osi_dump.cli --config config.json --auth clouds.yaml --output ./my-reports
```

The tool will generate `osi_dump_report.xlsx` in the specified output directory.
