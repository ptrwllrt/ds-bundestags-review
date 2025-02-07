import os
import calendar
from datetime import date
import BundestagsAPy
from config import Config
from utils.utils import get_existing_ids, save_item_to_file

def get_month_ranges(start_year=2015, end_year=2024):
    """Generate start/end dates for each month in year range"""
    ranges = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            _, last_day = calendar.monthrange(year, month)
            ranges.append((
                date(year, month, 1),
                date(year, month, last_day)
            ))
    return ranges

def fetch_plenarprotokolle(api):
    """Fetch all protocols from 2015-2024 month by month"""
    existing_ids = get_existing_ids()
    all_data = []
    
    date_ranges = get_month_ranges(2015, 2024)
    total_months = len(date_ranges)
    
    for idx, (start_date, end_date) in enumerate(date_ranges, 1):
        print(f"\nProcessing {start_date.strftime('%B %Y')} ({idx}/{total_months})")
        
        try:
            data = api.bt_plenarprotokoll_text(
                start_date=start_date,
                end_date=end_date,
                max_results=100
            )
            
            new_items = [item for item in data if item.id not in existing_ids]
            for item in new_items:
                save_item_to_file(item)
                existing_ids.add(item.id)
            
            all_data.extend(new_items)
            print(f"Found {len(new_items)} new documents")
            
        except Exception as e:
            print(f"Error processing {start_date.strftime('%B %Y')}: {e}")
            continue
            
    return all_data

def download_protocols():
    """Download protocols from Bundestag API"""
    api = BundestagsAPy.Client(Config.API_KEY)  # Initialize the API client
    try:
        data = fetch_plenarprotokolle(api)
        for item in data:
            save_item_to_file(item)
        print(f"Successfully saved {len(data)} new protocols")
    except Exception as e:
        print(f"Error downloading protocols: {e}")