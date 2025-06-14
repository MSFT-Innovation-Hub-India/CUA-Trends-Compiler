# Trends Compiler AI Assistant

An intelligent trends exploration and compilation system that uses Azure OpenAI's Responses API with Computer Use capabilities and Playwright automation to systematically explore and compile trend information from Pinterest.

## 🚀 Features

- **AI-Powered Automation**: Uses Azure OpenAI's Computer Use capabilities to navigate websites autonomously
- **Trend Exploration**: Systematically searches and analyzes trend items on Pinterest
- **Image Analysis**: Detailed analysis of visual trends, colors, patterns, and design elements
- **Content Extraction**: Automatically clicks "Read more" links to get complete content
- **Markdown Compilation**: Organizes findings into well-structured markdown reports
- **Azure Blob Storage Integration**: Saves compiled reports to Azure Blob Storage using MCP
- **Real-time Progress Tracking**: Live updates during the exploration process
- **Interactive UI**: User-friendly Streamlit interface

## 🏗️ Architecture

The system consists of several key components:

### Core Components

1. **`trends_crawler.py`**: Main automation engine using Azure OpenAI Responses API
2. **`streamlit_app.py`**: Web interface for user interaction
3. **`common/`**: Shared utilities for computer automation
   - `local_playwright.py`: Playwright browser automation
   - `computer.py`: Computer use interface
   - `utils.py`: Utility functions

### Integration Points

- **Azure OpenAI Responses API**: For AI-driven automation
- **Model Context Protocol (MCP)**: For Azure Blob Storage operations
- **Playwright**: For web browser automation
- **Streamlit**: For the user interface

## 📋 Prerequisites

- Python 3.8+
- Azure OpenAI subscription with Computer Use model access
- Azure Storage Account (for MCP integration)
- MCP Server setup for Azure Blob Storage

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd trends-compiler-cua-mcp
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**:
```bash
playwright install
```

4. **Configure environment variables**:
Copy `.env.sample` to `.env` and update with your values:
```bash
cp .env.sample .env
```

Edit `.env`:
```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
MODEL_NAME=your-computer-use-model-name
MODEL_NAME2=your-regular-model-name
AZURE_API_VERSION=2024-12-01-preview

# Web Scraping URL (Pinterest)
web_crawl_url=https://www.pinterest.com

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:3000
```

## 🚀 Usage

### Starting the Application

1. **Start the MCP Server** (if using Azure Blob Storage):
```bash
# Follow your MCP server setup instructions
```

2. **Run the Streamlit app**:
```bash
streamlit run streamlit_app.py
```

3. **Open your browser** and navigate to `http://localhost:8501`

### Using the Interface

1. **Enter a trend topic** (e.g., "sustainable fashion", "minimalist design")
2. **Set the number of items** to analyze (1-10)
3. **Click "Start Trend Exploration"** to begin AI automation
4. **Monitor progress** in real-time
5. **Review compiled trends** once complete
6. **Save to Azure Blob Storage** by selecting a container

### How It Works

The system follows this workflow:

1. **Navigation**: AI navigates to Pinterest using computer use
2. **Search**: Finds and uses the search bar to look for your trend topic
3. **Systematic Analysis**: For each trend item:
   - Clicks on the item to open detail page
   - Analyzes images for visual trends and design elements
   - Extracts text descriptions
   - Clicks "Read more" links for complete content
   - Compiles information with clear formatting
   - Returns to search results for next item
4. **Compilation**: Organizes all findings into a structured markdown report
5. **Storage**: Optionally saves the report to Azure Blob Storage

## 📊 Output Format

Each trend item is compiled with this structure:

```markdown
## Trend Item [Number]: [Descriptive Title]

### Visual Analysis
[Detailed description of images/visuals, colors, patterns, styles]

### Description
[Text content and descriptions found on the page]

### Key Trend Insights
[AI analysis of what trends this represents]

---
```

## 🔧 Configuration

### Azure OpenAI Models

- **Computer Use Model**: Required for web automation (e.g., `gpt-4o-computer-use-preview`)
- **Regular Model**: For text processing and analysis

### MCP Server Setup

The system uses Model Context Protocol for Azure Blob Storage operations. Ensure your MCP server supports:
- `list_containers`: List available storage containers
- `upload_blob`: Upload content to blob storage

### Playwright Configuration

The system uses Playwright for browser automation:
- Runs in non-headless mode for debugging
- Display size: 1024x768
- Supports safety checks and URL validation

## 🛡️ Safety Features

- **URL Validation**: Checks against blocklisted URLs
- **Safety Checks**: Automated acknowledgment for safe trend exploration
- **Error Handling**: Robust error handling throughout the automation process
- **Progress Tracking**: Real-time monitoring of the exploration process

## 📁 Project Structure

```
trends-compiler-cua-mcp/
├── streamlit_app.py           # Main UI application
├── trends_crawler.py          # Core automation engine
├── requirements.txt           # Python dependencies
├── .env.sample               # Environment variables template
├── # Trends Compiler - Computer Use Agent (CUA) with Azure OpenAI

This application uses Azure OpenAI's Computer Use Ability (CUA) model to automatically search for and analyze latest trends on any topic by controlling a web browser.

## Features

- **Automated Browser Control**: Uses Playwright to control a Chromium browser
- **AI-Powered Navigation**: Leverages Azure OpenAI's CUA model to intelligently navigate web pages
- **Trend Analysis**: Searches for and analyzes image-based trend content
- **Secure Authentication**: Uses Azure Managed Identity for secure API access
- **Configurable**: Customizable search parameters and crawling limits

## Prerequisites

1. **Azure OpenAI Resource** with Computer Use Ability (CUA) enabled
2. **Python 3.8+**
3. **Playwright** browser dependencies

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and update with your Azure OpenAI details:

```bash
cp .env.example .env
```

Update the following variables in `.env`:
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI resource endpoint
- `MODEL_NAME`: Your CUA-enabled model name (e.g., `gpt-4o-with-canvas`)
- `AZURE_API_VERSION`: API version that supports CUA (e.g., `2024-12-01-preview`)

### 4. Azure Authentication

This application uses Azure Managed Identity for authentication. Ensure you're logged in with Azure CLI:

```bash
az login
```

## Usage

Run the application with a search query:

```bash
python app.py --query "AI trends 2024"
```

### Command Line Options

- `--query` or `-q`: The search query for trends (required)

### Example Commands

```bash
# Search for AI trends
python app.py --query "artificial intelligence trends 2024"

# Search for fashion trends
python app.py --query "fashion trends spring 2024"

# Search for technology trends
python app.py --query "emerging technology trends"
```

## How It Works

1. **Browser Launch**: Opens a Chromium browser using Playwright
2. **Initial Navigation**: Navigates to the configured search engine (default: Google)
3. **AI-Powered Search**: Uses Azure OpenAI CUA model to:
   - Identify the search box
   - Type the user's query
   - Press Enter to search
4. **Image Analysis**: For each of the first N image results (configurable):
   - Clicks on the image link
   - Analyzes and describes the content
   - Navigates back to search results
   - Proceeds to the next image
5. **Completion**: Returns control after processing all specified images

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint | - | Yes |
| `MODEL_NAME` | CUA-enabled model name | - | Yes |
| `AZURE_API_VERSION` | API version supporting CUA | - | Yes |
| `web_crawl_url` | Starting URL for searches | https://www.google.com | No |
| `max_pages_for_crawling` | Max number of image pages to visit | 3 | No |

### Computer Use Model Instructions

The application includes comprehensive instructions for the AI agent:

- Browser control capabilities (keyboard, mouse, screenshots)
- Task-specific guidance for trend searching
- Step-by-step process for image link analysis
- Completion criteria and control handover

## Architecture

```
app.py                          # Main application entry point
├── LocalPlaywrightComputer     # Browser automation interface
├── Azure OpenAI CUA Client     # AI model integration
└── Computer Action Executor    # Action parsing and execution

common/
├── computer.py                 # Computer interface protocol
├── local_playwright.py         # Playwright implementation
└── utils.py                    # Utility functions
```

## Security Features

- **Managed Identity Authentication**: No hardcoded credentials
- **Secure Token Management**: Uses Azure credential providers
- **Browser Security**: Configured with appropriate security settings
- **Error Handling**: Comprehensive exception handling and logging

## Troubleshooting

### Common Issues

1. **Browser Launch Failed**
   - Ensure Playwright browsers are installed: `playwright install chromium`
   - Check system dependencies for Chromium

2. **Authentication Errors**
   - Verify Azure CLI login: `az login`
   - Check Azure OpenAI resource permissions

3. **Model Errors**
   - Ensure your model supports Computer Use Ability (CUA)
   - Verify the API version supports CUA features

4. **Screenshot Issues**
   - Check display settings and screen resolution
   - Ensure adequate system memory for browser operations

### Debugging

Enable verbose logging by setting environment variables:

```bash
export DEBUG=1
export PLAYWRIGHT_DEBUG=1
```

## Limitations

- Maximum 10 iterations per session (configurable via `ITERATIONS`)
- Requires internet connection for web searching
- Browser automation may be affected by website changes
- CUA model responses depend on screenshot quality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with proper error handling
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to:
- **Azure OpenAI**: Check Azure OpenAI documentation
- **Playwright**: See Playwright documentation
- **Application**: Open an issue in this repository                 # This file
└── common/                   # Shared utilities
    ├── __init__.py
    ├── computer.py           # Computer use interface
    ├── local_playwright.py   # Playwright automation
    └── utils.py              # Utility functions
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure Azure credentials are properly configured
2. **Model Access**: Verify access to Computer Use preview models
3. **MCP Connection**: Check MCP server is running and accessible
4. **Playwright Issues**: Run `playwright install` to ensure browsers are installed

### Debug Mode

The system includes detailed logging:
- AI messages and responses
- Computer actions being executed
- Screenshot capture confirmations
- Error messages with stack traces

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Azure OpenAI team for Computer Use capabilities
- Playwright team for browser automation
- Streamlit team for the excellent UI framework
- Model Context Protocol for seamless integrations