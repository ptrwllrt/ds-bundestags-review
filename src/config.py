from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    API_KEY = os.getenv('API_KEY')
    INPUT_DIR = os.getenv('INPUT_DIR', 'output')  # default if not set
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output_cleaned')  # default if not set