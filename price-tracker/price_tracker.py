#!/usr/bin/env python3
"""
E-Commerce Price Tracker
Monitors product prices and sends notifications when target prices are reached.
"""

import os
import json
import sqlite3
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Represents a product to track."""
    name: str
    url: str
    target_price: float
    selector: str
    current_price: Optional[float] = None
    last_checked: Optional[datetime] = None


class Database:
    """Handles SQLite database operations for price history."""
    
    def __init__(self, db_path: str = "prices.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    target_price REAL NOT NULL,
                    selector TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def save_price(self, product_name: str, price: float):
        """Save a price reading to history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO price_history (product_name, price) VALUES (?, ?)",
                (product_name, price)
            )
            conn.commit()
    
    def get_price_history(self, product_name: str, limit: int = 10) -> List[dict]:
        """Get price history for a product."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT price, checked_at FROM price_history 
                   WHERE product_name = ? 
                   ORDER BY checked_at DESC LIMIT ?""",
                (product_name, limit)
            )
            return [dict(row) for row in cursor.fetchall()]


class PriceScraper:
    """Scrapes prices from e-commerce websites."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        })
    
    def scrape_price(self, url: str, selector: str) -> Optional[float]:
        """
        Scrape price from a product page.
        
        Args:
            url: Product page URL
            selector: CSS selector for price element
            
        Returns:
            Price as float, or None if scraping failed
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            price_elem = soup.select_one(selector)
            
            if not price_elem:
                logger.warning(f"Price element not found with selector: {selector}")
                return None
            
            price_text = price_elem.get_text().strip()
            price = self._parse_price(price_text)
            
            logger.info(f"Found price: ${price}")
            return price
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price text to float."""
        # Remove currency symbols and whitespace
        import re
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle European format (1.234,56)
        if ',' in price_clean and '.' in price_clean:
            if price_clean.rfind(',') > price_clean.rfind('.'):
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Could be decimal separator or thousands separator
            if len(price_clean.split(',')[-1]) == 2:
                price_clean = price_clean.replace(',', '.')
            else:
                price_clean = price_clean.replace(',', '')
        
        return float(price_clean)


class Notifier:
    """Sends price drop notifications."""
    
    def __init__(self):
        self.enabled = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.to_email = os.getenv('NOTIFICATION_EMAIL', self.email)
    
    def send_notification(self, product: Product):
        """Send price drop notification via email."""
        if not self.enabled or not all([self.email, self.password]):
            logger.info("Notifications disabled or not configured")
            print(f"\n{'='*50}")
            print(f"🔔 PRICE DROP ALERT!")
            print(f"Product: {product.name}")
            print(f"Current Price: ${product.current_price:.2f}")
            print(f"Target Price: ${product.target_price:.2f}")
            print(f"URL: {product.url}")
            print(f"{'='*50}\n")
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.to_email
            msg['Subject'] = f"🔔 Price Drop Alert: {product.name}"
            
            body = f"""
Price Drop Alert!

Product: {product.name}
Current Price: ${product.current_price:.2f}
Target Price: ${product.target_price:.2f}
You Save: ${product.target_price - product.current_price:.2f}

Product URL: {product.url}

Happy Shopping!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Notification sent to {self.to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


class PriceTracker:
    """Main price tracker orchestrator."""
    
    def __init__(self, products_file: str = "products.json"):
        self.products_file = products_file
        self.db = Database()
        self.scraper = PriceScraper()
        self.notifier = Notifier()
        self.products: List[Product] = []
    
    def load_products(self):
        """Load products from JSON file."""
        if not Path(self.products_file).exists():
            # Create sample products file
            sample_products = [
                {
                    "name": "Sample Wireless Headphones",
                    "url": "https://example.com/product/123",
                    "target_price": 150.00,
                    "selector": ".price"
                }
            ]
            with open(self.products_file, 'w') as f:
                json.dump(sample_products, f, indent=2)
            logger.info(f"Created sample products file: {self.products_file}")
        
        with open(self.products_file) as f:
            data = json.load(f)
            self.products = [Product(**p) for p in data]
        
        logger.info(f"Loaded {len(self.products)} products to track")
    
    def check_prices(self):
        """Check all product prices."""
        print(f"\n🚀 Price Tracker Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        for product in self.products:
            print(f"\n📦 Checking: {product.name}")
            
            price = self.scraper.scrape_price(product.url, product.selector)
            
            if price is None:
                print("   ⚠️  Failed to retrieve price")
                continue
            
            product.current_price = price
            product.last_checked = datetime.now()
            
            # Save to database
            self.db.save_price(product.name, price)
            
            print(f"   💰 Current Price: ${price:.2f}")
            print(f"   🎯 Target Price: ${product.target_price:.2f}")
            
            if price <= product.target_price:
                print(f"   ✅ TARGET REACHED!")
                self.notifier.send_notification(product)
            else:
                diff = price - product.target_price
                print(f"   ⏳ Still ${diff:.2f} above target")
            
            # Get price history
            history = self.db.get_price_history(product.name, 5)
            if len(history) > 1:
                prev_price = history[1]['price']
                change = price - prev_price
                change_pct = (change / prev_price) * 100
                if change != 0:
                    direction = "📉" if change < 0 else "📈"
                    print(f"   {direction} Change from last check: ${change:+.2f} ({change_pct:+.1f}%)")
        
        print("\n" + "=" * 50)
        print(f"✅ Check complete. Next run: Manual or scheduled\n")
    
    def show_price_history(self, product_name: Optional[str] = None):
        """Display price history for products."""
        if product_name:
            products = [p for p in self.products if p.name == product_name]
        else:
            products = self.products
        
        for product in products:
            print(f"\n📊 Price History: {product.name}")
            print("-" * 50)
            
            history = self.db.get_price_history(product.name, 20)
            if not history:
                print("   No history available")
                continue
            
            prev_price = None
            for record in history:
                price = record['price']
                date = record['checked_at']
                
                if prev_price:
                    change = price - prev_price
                    change_str = f"{'↓' if change < 0 else '↑'} ${abs(change):.2f}"
                else:
                    change_str = "-"
                
                indicator = "🔔" if price <= product.target_price else "  "
                print(f"   {date} | ${price:>8.2f} | {change_str:>12} {indicator}")
                prev_price = price


def main():
    """Main entry point."""
    tracker = PriceTracker()
    tracker.load_products()
    tracker.check_prices()
    
    # Uncomment to show price history
    # tracker.show_price_history()


if __name__ == "__main__":
    main()
