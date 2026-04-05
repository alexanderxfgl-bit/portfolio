# Alex Smith — AI Automation Engineer

Freelance AI automation engineer specializing in LLM integration, workflow automation, chatbot development, and data pipeline engineering. Available for hire on [Upwork](https://www.upwork.com/) and via email.

---

## Portfolio Projects

A collection of professional projects showcasing web scraping, API integration, AI automation, and data processing skills.

## 📁 Projects Overview

### 1. AI Chatbot Engine (`ai-chatbot-engine/`)
A production-ready conversational AI engine with multi-provider LLM support, conversation memory, and tool-use capabilities.

**Key Skills Demonstrated:**
- Multi-provider LLM integration (OpenAI, Anthropic, Gemini, local models)
- Function/tool calling with extensible plugin system
- FastAPI REST API with streaming (SSE)
- Persistent conversation memory with SQLAlchemy
- JWT authentication and rate limiting
- Async Python architecture

**Tech Stack:** Python, FastAPI, SQLAlchemy, LiteLLM, Pydantic

---

### 2. AI Workflow Automation Engine (`ai-workflow-automation/`)
A YAML-driven framework for building AI-powered business workflow automations with LLM decision nodes, conditional routing, and webhook integrations.

**Key Skills Demonstrated:**
- YAML-based workflow DSL design
- Async Python architecture with asyncio
- LLM-powered decision nodes
- Webhook integrations and API orchestration
- Human-in-the-loop approval patterns
- Plugin/extension architecture

**Tech Stack:** Python, PyYAML, LiteLLM, aiohttp, Pydantic

---

### 3. E-Commerce Price Tracker (`price-tracker/`)
A production-ready price monitoring system that tracks product prices across e-commerce websites.

**Key Skills Demonstrated:**
- Web scraping with BeautifulSoup and requests
- SQLite database management
- Email notifications
- Configuration management
- Error handling and logging
- GitHub Actions CI/CD

**Tech Stack:** Python, BeautifulSoup4, requests, SQLite, python-dotenv

**Quick Start:**
```bash
cd price-tracker
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
python price_tracker.py
```

---

### 2. API Integration Demo (`api-integration-demo/`)
A comprehensive demonstration of REST API consumption with multiple authentication methods and best practices.

**Key Skills Demonstrated:**
- REST API design patterns
- OAuth2, API Key, and Bearer token authentication
- Rate limiting and retry logic
- Pagination handling
- Error handling and logging
- Unit testing with pytest
- GitHub Actions CI/CD

**Tech Stack:** Python, requests, pyyaml, pytest, responses

**Quick Start:**
```bash
cd api-integration-demo
pip install -r requirements.txt
export GITHUB_TOKEN=your_token_here  # Optional
python demo.py
```

---

### 3. Data Cleaning & Transformation Tool (`data-cleaning-tool/`)
A powerful pandas-based tool for cleaning, transforming, and analyzing messy datasets.

**Key Skills Demonstrated:**
- Advanced pandas operations
- Data type conversions
- Missing value handling
- Outlier detection
- Text standardization
- Email validation
- Data profiling and reporting

**Tech Stack:** Python, pandas, numpy, openpyxl, phonenumbers

**Quick Start:**
```bash
cd data-cleaning-tool
pip install -r requirements.txt
python clean_data.py
```

---

## 🎯 Portfolio Highlights

### Code Quality
- Clean, modular architecture
- Type hints and docstrings
- Comprehensive error handling
- Logging throughout
- PEP 8 compliant

### Testing
- Unit tests with pytest
- Mock-based testing for APIs
- Sample data included
- GitHub Actions workflows

### Documentation
- Detailed README files
- Setup instructions
- Usage examples
- Sample outputs

---

## 📊 Project Structure

```
portfolio/
├── price-tracker/
│   ├── price_tracker.py      # Main tracker script
│   ├── products.json         # Product configurations
│   ├── requirements.txt      # Dependencies
│   ├── .env.example          # Environment template
│   ├── README.md            # Documentation
│   ├── LICENSE              # MIT License
│   ├── sample_output.txt    # Example output
│   └── .github/workflows/   # CI/CD configuration
│
├── api-integration-demo/
│   ├── api_client.py        # Main API client
│   ├── demo.py              # Demo script
│   ├── requirements.txt     # Dependencies
│   ├── README.md           # Documentation
│   ├── LICENSE             # MIT License
│   ├── sample_output.txt   # Example output
│   ├── tests/              # Unit tests
│   └── .github/workflows/  # CI/CD configuration
│
└── data-cleaning-tool/
    ├── clean_data.py       # Main cleaning script
│   ├── sample_data/        # Sample datasets
│   ├── requirements.txt    # Dependencies
│   ├── README.md          # Documentation
│   ├── LICENSE            # MIT License
│   ├── sample_output.txt  # Example output
│   └── tests/             # Unit tests
```

---

## 🚀 Getting Started

Each project can be run independently:

1. **Clone the repository**
   ```bash
   git clone https://github.com/alexanderxfgl-bit/portfolio.git
   cd portfolio
   ```

2. **Choose a project and follow its README**
   
   Each project has its own setup instructions in its README.md file.

---

## 📈 Skills Showcased

| Skill | Chatbot Engine | Price Tracker | API Demo | Data Cleaner |
|-------|:---:|:---:|:---:|:---:|
| LLM/AI Integration | ✅ | - | - | - |
| Tool/Function Calling | ✅ | - | - | - |
| REST API | ✅ | - | ✅ | - |
| Web Scraping | - | ✅ | ✅ | - |
| API Integration | ✅ | - | ✅ | - |
| Data Processing | - | - | - | ✅ |
| Authentication | ✅ | - | ✅ | - |
| Database/SQLite | ✅ | ✅ | - | - |
| Error Handling | ✅ | ✅ | ✅ | ✅ |
| Testing | ✅ | - | ✅ | ✅ |
| CI/CD | - | ✅ | ✅ | - |

---

## 📄 License

All projects are released under the MIT License. See individual project LICENSE files for details.

---

## 👤 Contact

- GitHub: [@alexanderxfgl-bit](https://github.com/alexanderxfgl-bit)
- Email: alexanderxfgl@gmail.com

---

*Built with ❤️ using Python*
