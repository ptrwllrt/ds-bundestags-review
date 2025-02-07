import os
import csv
import BundestagsAPy
import click
from datetime import datetime, date, timedelta
import calendar
import pandas as pd
import re
from config import Config

class Config:
    API_KEY = os.getenv('API_KEY')
    INPUT_DIR = os.getenv('INPUT_DIR', 'output')  # default if not set
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output_cleaned')  # default if not set

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

# data cleaning

def filter_stenography_part(text):
    try:
        start = re.search(r'\bSitzung\b.*?\beröffn|\beröffn*?\bSitzung\b', text, re.IGNORECASE | re.DOTALL).span()[0]
        #start = re.search(r'Die Sitzung ist eröffnet.|Ich eröffne die Sitzung|Sitzung eröffnet',text).span()[0] #this is always in the first line of the opening of the session
    except AttributeError:
        start = re.search(r'Bitte nehmen Sie Platz.',text).span()[0] #sometimes the opening is not in the text, then we have to use this as a fallback
    #second to last new line character before the end of the stenographic transcript
    start = text[:start].rfind('\n',start-500,start)
    start = text[:start].rfind('\n',start-500,start)+1
    end = re.search(r'\(Schluss[\w\s]*: \d{1,2}.\d{1,2} Uhr\)',text).span()[0] #this is always the end of the stenographic transcript
    return text[start:end]

def get_speech_positions(text):
    #speeches always start with the name of the speaker and the party in brackets, e.g. Annalena Baerbock (BÜNDNIS 90/DIE GRÜNEN):
    parties = [r'\(CDU/CSU\):\n',r'\(SPD\):\n',r'\(AfD\):\n',r'\(FDP\):\n',r'\(DIE LINKE\):\n',r'\(BÜNDNIS 90/DIE GRÜNEN\):\n']
    end_pattern = re.compile(r'\nVizepräsident\w{0,2}\s[\w\s.-]+:\n|\nPräsident\w{0,2}\s[\w\s.-]+:\n')
    speeches = {}
    for party in parties:
        pattern = re.compile(party)
        starts = []
        for m in re.finditer(pattern,text):
            start = m.span()[0]
            start = text[:start].rfind('\n',start-500,start)
            starts.append(start)
        #find end
        spans = []
        for s in starts:
            end = re.search(end_pattern,text[s:]).span()[0]+s
            spans.append((s,end))
        party_text = party.replace(r'\(','').replace(r'\):','').replace(r'\n','').strip()
        speeches[party_text] = spans
    return speeches

def get_speeches(text,positions):
    speeches = {}
    for party in positions.keys():
        party_speeches = []
        for start,end in positions[party]:
            party_speeches.append(text[start:end])
        speeches[party] = party_speeches
    return speeches

def clean_speech(speech):
    speaker = speech[1:].split('\n')[0]
    speech = speech.replace(speaker,'')
    speaker = speaker.split('(')[0].strip()
    #remove any statements not by the speaker (in paranthesis, e.g. applause)
    speech = re.sub(r'\([^\)]+\)','',speech)
    #replace newline characters
    speech = speech.replace('\n',' ').strip()
    return (speaker,speech)

def build_dataframe(speeches):
    data = []
    for party in speeches.keys():
        for speaker,speech in speeches[party]:
            data.append([party,speaker,speech])
    return pd.DataFrame(data,columns=['party','speaker','speech'])

def clean_transcript(transcript):
    text = transcript.text.replace("\xa0",' ')
    text = filter_stenography_part(text)
    positions = get_speech_positions(text)
    speeches = get_speeches(text,positions)
    clean_speeches = {}
    for party in speeches.keys():
        clean_speeches[party] = [clean_speech(s) for s in speeches[party]]
    df = build_dataframe(clean_speeches)
    df['date'] = transcript.datum
    return df

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

def process_csv_files(input_dir='output', output_dir='output_cleaned'):
    """Process all CSV files and create cleaned versions"""
    os.makedirs(output_dir, exist_ok=True)
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    for file in csv_files:
        try:
            print(f"Processing {file}...")
            df = pd.read_csv(os.path.join(input_dir, file))
            
            transcript = type('', (), {})()
            transcript.text = df['text'].iloc[0]
            transcript.datum = df['datum'].iloc[0]
            
            tmp_df = clean_transcript(transcript)
            df = df.drop(0)
            df_cleaned = pd.concat([df, tmp_df], ignore_index=True)
            
            output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_cleaned.csv")
            df_cleaned.to_csv(output_file, index=False)
            print(f"Saved cleaned {file}")
            
        except Exception as e:
            print(f"Error processing {file}: {e}")

def main():
    cli()

@click.group()
def cli():
    """Bundestag Protocol Processing Tool"""
    pass

@cli.command()
def download():
    """Download protocols from Bundestag API"""
    click.echo("Downloading protocols...")
    download_protocols()

@cli.command()
def clean():
    """Clean and process downloaded protocols"""
    click.echo("Processing CSV files...")
    process_csv_files()

if __name__ == "__main__":
    main()