# Filenamer - PDF Intelligent Renaming Tool

Automatically rename PDF files based on their content using Ollama LLM.

## Recent Changes

### Configuration File Support
- Added `filenamer_config.yaml` for customizing behavior
- Configure model, temperature, max characters, duplicate limit, and prompt
- Custom config files supported via `--config` flag

### Verbose Mode
- Added `-v/--verbose` flag for detailed debug output
- Debug messages now only appear when verbose mode is enabled
- Helps troubleshoot issues without cluttering normal output

### Improved Date Handling
- Prompt now explicitly handles documents without dates
- Files with dates: `YYYY-MM-DD_COMPANY-SUBJECT.pdf`
- Files without dates: `COMPANY-SUBJECT.pdf`

## Usage

### Basic Usage
```bash
filenamer file.pdf
filenamer directory/
```

### With Verbose Output
```bash
filenamer -v file.pdf
filenamer --verbose directory/
```

### With Custom Config
```bash
filenamer -c my_config.yaml file.pdf
filenamer --config /path/to/config.yaml directory/
```

## Configuration File

The default config file is `filenamer_config.yaml` in the script directory.

### Example Configuration:
```yaml
# LLM Settings
model: "llama3.1"
temperature: 0
max_characters: 128000

# File Processing Settings
duplicate_index_limit: 99

# Prompt Template
prompt: |
  [Your custom prompt here]
  Use {pdf} placeholder for document content

# Example filenames for reference
example_filenames:
  - "2025-04-15_Microsoft-QuarterlyReport.pdf"
  - "Microsoft-ProductBrochure.pdf"
```

## Dependencies

- PyMuPDF (fitz)
- ollama
- PyYAML

Install with:
```bash
uv pip install PyMuPDF ollama PyYAML
```

## Wrapper Script

The `filenamer` bash script automatically:
- Checks if Ollama is running and starts it if needed
- Converts relative paths to absolute paths
- Runs the Python script with uv
