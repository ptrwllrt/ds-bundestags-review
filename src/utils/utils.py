import os
import re
import pandas as pd

CSV_COLUMNS = [
    'id', 'dokumentart', 'typ', 'vorgangsbezug_anzahl', 'dokumentnummer', 
    'wahlperiode', 'herausgeber', 'pdf_hash', 'aktualisiert', 'vorgangsbezug',
    'fundstelle', 'text', 'titel', 'datum'
]

def get_existing_ids(output_dir='output'):
    """Get list of already downloaded protocol IDs"""
    if not os.path.exists(output_dir):
        return set()
    return {f.split('.')[0] for f in os.listdir(output_dir) if f.endswith('.csv')}

def extract_data_row(item):
    """Extract fields from API response into CSV format"""
    row = []
    for column in CSV_COLUMNS:
        if column == 'vorgangsbezug':
            value = ''
        elif column == 'fundstelle':
            fundstelle = getattr(item, column, None)
            value = fundstelle.pdf_url if fundstelle else ''
        elif column == 'datum':
            fundstelle = getattr(item, 'fundstelle', None)
            value = fundstelle.datum if fundstelle else ''
        else:
            value = getattr(item, column, '')
        row.append(value)
    return row

def save_item_to_file(item, output_dir='output'):
    """Save single item to CSV file named by its ID"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        item_id = getattr(item, 'id', 'unknown')
        filename = os.path.join(output_dir, f"{item_id}.csv")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            row = extract_data_row(item)
            writer.writerow(row)
    except Exception as e:
        print(f"Error saving item {item_id}: {e}")

def filter_stenography_part(text):
    try:
        start = re.search(r'\bSitzung\b.*?\beröffn|\beröffn*?\bSitzung\b', text, re.IGNORECASE | re.DOTALL).span()[0]
    except AttributeError:
        start = re.search(r'Bitte nehmen Sie Platz.',text).span()[0]
    start = text[:start].rfind('\n',start-500,start)
    start = text[:start].rfind('\n',start-500,start)+1
    end = re.search(r'\(Schluss[\w\s]*: \d{1,2}.\d{1,2} Uhr\)',text).span()[0]
    return text[start:end]

def get_speech_positions(text):
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
    speech = re.sub(r'\([^\)]+\)','',speech)
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