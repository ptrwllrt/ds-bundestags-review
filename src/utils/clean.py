import os
import pandas as pd
from utils.utils import clean_transcript

def process_csv_files(input_dir='output', output_dir='output_cleaned'):
    """Process all CSV files and create cleaned versions"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove previously created files in the output directory
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    for file in csv_files:
        try:
            print(f"Processing {file}...")
            df = pd.read_csv(os.path.join(input_dir, file))
            
            transcript = type('', (), {})()
            transcript.text = df['text'].iloc[0]
            transcript.datum = df['datum'].iloc[0]
            
            df_cleaned = clean_transcript(transcript)
            
            output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_cleaned.csv")
            df_cleaned.to_csv(output_file, index=False)
            print(f"Saved cleaned {file}")
            
        except Exception as e:
            print(f"Error processing {file}: {e}")