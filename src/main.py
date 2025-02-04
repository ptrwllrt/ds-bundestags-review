import os
import csv
import BundestagsAPy
from datetime import datetime, date, timedelta
import calendar

# Define expected CSV columns
CSV_COLUMNS = [
    'id', 'dokumentart', 'typ', 'vorgangsbezug_anzahl', 'dokumentnummer', 
    'wahlperiode', 'herausgeber', 'pdf_hash', 'aktualisiert', 'vorgangsbezug',
    'fundstelle', 'text',
     'titel', 'datum'
]

def get_existing_ids(output_dir='output'):
    """Get list of already downloaded protocol IDs"""
    if not os.path.exists(output_dir):
        return set()
    return {f.split('.')[0] for f in os.listdir(output_dir) if f.endswith('.csv')}

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
            
            # Filter and save new items
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

def extract_data_row(item):
    """Extract fields from API response into CSV format"""
    row = []
    for column in CSV_COLUMNS:
        if column == 'vorgangsbezug':
            #print('vorgangsbezug', item.vorgangsbezug)
            #print('#####')
            hans = ''
            # TODO unsure what todo with this
            # Handle list of Vorgangsbezug objects
            #refs = getattr(item, column, [])
            #value = '; '.join(f"{ref.id}: {ref.titel}" for ref in refs)
        elif column == 'fundstelle':
            # Handle Fundstelle object
            fundstelle = getattr(item, column, None)
            value = fundstelle.pdf_url if fundstelle else ''
        elif column == 'datum':
            # Get date from Fundstelle object
            fundstelle = getattr(item, 'fundstelle', None)
            value = fundstelle.datum if fundstelle else ''
        else:
            # Get direct attributes
            value = getattr(item, column, '')
        row.append(value)
    return row

def save_item_to_file(item, output_dir='output'):
    """Save single item to CSV file named by its ID"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get ID for filename
        item_id = getattr(item, 'id', 'unknown')
        filename = os.path.join(output_dir, f"{item_id}.csv")
        
        # Write single row CSV
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            row = extract_data_row(item)
            writer.writerow(row)
            
    except Exception as e:
        print(f"Error saving item {item_id}: {e}")

def main():
    api_key = "I9FKdCn.hbfefNWCY336dL6x62vfwNKpoN2RZ1gp21"  # Replace with your actual API key
    api = BundestagsAPy.Client(api_key)  # Initialize the API client
    try:
        data = fetch_plenarprotokolle(api)
        for item in data:
            save_item_to_file(item)
        print(f"Successfully saved {len(data)} new protocols")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()