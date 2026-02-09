# E-Commerce Price Tracker

A Python-based price tracking tool that monitors product prices on e-commerce websites and sends notifications when prices drop below your target.

## Features

- 📊 Track prices from multiple e-commerce sites
- 🔔 Email notifications when target price is reached
- 💾 Persistent storage of price history in SQLite
- 🔄 Configurable check intervals
- 🌐 Support for dynamic JavaScript-rendered pages using Selenium

## Setup Instructions

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser (for Selenium support)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/price-tracker.git
cd price-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment variables:
```bash
cp .env.example .env
# Edit .env with your email settings and target products
```

## Usage

### Basic Usage

```bash
python price_tracker.py
```

### Adding Products to Track

Edit the `products.json` file:

```json
[
  {
    "name": "Wireless Headphones",
    "url": "https://example.com/product/123",
    "target_price": 150.00,
    "selector": ".price-current"
  }
]
```

### Running as a Cron Job

To check prices every hour:

```bash
0 * * * * cd /path/to/price-tracker && python price_tracker.py >> logs/cron.log 2>&1
```

## Project Structure

```
price-tracker/
├── price_tracker.py      # Main tracker script
├── scraper.py            # Web scraping utilities
├── notifier.py           # Email notification module
├── database.py           # SQLite database operations
├── config.py             # Configuration loader
├── products.json         # Products to track
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Sample Output

```
🚀 Price Tracker Started - 2024-01-15 10:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checking: Wireless Headphones
Current Price: $179.99
Target Price: $150.00
Status: ⏳ Still above target

Checking: Gaming Laptop
Current Price: $899.99
Target Price: $950.00
Status: ✅ TARGET REACHED!
📧 Notification sent to user@example.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next check in: 60 minutes
```

## Price History View

```
Product: Gaming Laptop
Date              | Price    | Change
─────────────────────────────────────
2024-01-10 10:00  | $999.99  | - 
2024-01-12 10:00  | $949.99  | ↓ $50.00
2024-01-15 10:00  | $899.99  | ↓ $50.00 🔔
```

## Configuration

Edit `.env` file:

```env
# Email Settings (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Tracking Settings
CHECK_INTERVAL_MINUTES=60
DATABASE_PATH=prices.db
```

## Ethical Scraping

This tool respects robots.txt and includes delays between requests. Please:
- Check website's Terms of Service before scraping
- Don't overwhelm servers with frequent requests
- Use for personal tracking only

## License

MIT License - See LICENSE file for details
