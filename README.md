# Web Scraping Portfolio Projects

A collection of professional Python projects showcasing web scraping, API integration, and data processing skills.

## 📁 Projects Overview

### 1. E-Commerce Price Tracker (`price-tracker/`)
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
   git clone https://github.com/yourusername/portfolio.git
   cd portfolio
   ```

2. **Choose a project and follow its README**
   
   Each project has its own setup instructions in its README.md file.

---

## 📈 Skills Showcased

| Skill | Price Tracker | API Demo | Data Cleaner |
|-------|--------------|----------|--------------|
| Web Scraping | ✅ | ✅ | - |
| API Integration | - | ✅ | - |
| Data Processing | - | - | ✅ |
| Authentication | - | ✅ | - |
| Database/SQLite | ✅ | - | - |
| Error Handling | ✅ | ✅ | ✅ |
| Testing | - | ✅ | ✅ |
| CI/CD | ✅ | ✅ | - |

---

## 📄 License

All projects are released under the MIT License. See individual project LICENSE files for details.

---

## 👤 Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Name](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

*Built with ❤️ using Python*
