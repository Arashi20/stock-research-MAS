# Testing News tool and Stock data tool
# This script runs basic tests to ensure the tools are functioning correctly.
from tools.stock_data_tool import fetch_stock_data
from tools.news_tool import fetch_recent_news

# Test stock data
print("Testing Stock Data Tool...")
stock_result = fetch_stock_data("TSLA")
if stock_result['success']:
    print(f"✅ Got data for {stock_result['company_name']}")
    print(f"   Current Price: ${stock_result['current_price']}")
    print(f"   P/E Ratio: {stock_result['pe_ratio']}")
else:
    print(f"❌ Error: {stock_result['error']}")

print("\n" + "="*50 + "\n")

# Test news tool
print("Testing News Tool...")
news_result = fetch_recent_news("TSLA", "Tesla")
if news_result['success']:
    print(f"✅ Found {news_result['total_articles']} articles")
    if news_result['articles']:
        print(f"   Latest: {news_result['articles'][0]['title']}")
else:
    print(f"❌ Error: {news_result['error']}")

# Output will be printed to console indicating success or failure of each tool.