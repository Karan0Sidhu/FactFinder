import os
import json
import xml.etree.ElementTree as ET
import spacy
from tqdm import tqdm  # Progress bar library
import sys
from datetime import datetime
import logging

# Set up logging for errors only
def setup_error_logging(stderr_folder):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file = os.path.join(stderr_folder, f"stderr_{timestamp}.log")
    logger = logging.getLogger(f"error_logger_{timestamp}")
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Define namespaces to handle XML namespaces properly
namespaces = {
    'xlink': 'http://www.w3.org/1999/xlink',
    'mml': 'http://www.w3.org/1998/Math/MathML'
}

# Load Spacy model globally to ensure it's not loaded multiple times
nlp = spacy.load("en_ner_bc5cdr_md")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_CHUNK_SIZE = 25000
THRESHOLD = 1.25

def TagCount(text, threshold):
    """
    Counts the number of 'CHEMICAL' entities in the first 5000 characters of the text.
    """
    # Process only the first 5000 characters
    chunk = text[:MAX_CHUNK_SIZE]
    doc = nlp(chunk)
    chemical_count = sum(1 for ent in doc.ents if ent.label_ == "CHEMICAL" or ent.label_ == "DISEASE")
    return min(chemical_count, threshold)


def extract_text(element):
    """
    Extracts and concatenates text from an XML element and its sub-elements.
    """
    if element is None:
        return ''
    return ''.join(element.itertext())

def parse_xml_file(file_path, logger):
    """
    Parses an XML file to extract the article title, abstract, and body text.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        article_title = extract_text(root.find('.//title'))
        abstract = extract_text(root.find('.//abstract'))
        body = extract_text(root.find('.//body'))
        del tree, root
        return {
            'title': article_title,
            'abstract': abstract,
            'body': body
        }
    except ET.ParseError as e:
        logger.error(f"ParseError in file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in file {file_path}: {e}")
        return None

def filter_articles(article_data):
    """
    Filters articles based on a dynamic threshold of tagged entities.
    """
    text = article_data['title'] + ' ' + article_data['abstract'] + ' ' + article_data['body']
    word_count = len(text.split())
    ### -------------------------------------> theshold at 1.25% of MAX_CHUNK_SIZE <-------------------------------------- ###
    if word_count < MAX_CHUNK_SIZE:
        dynamic_threshold = (THRESHOLD / 100) * word_count
    else:
        dynamic_threshold = (THRESHOLD /100) * MAX_CHUNK_SIZE
    
    count = TagCount(text, dynamic_threshold)
    return count >= dynamic_threshold

def process_file(file_name, output_folder, logger):
    """
    Process a single file and return the result.
    """
    try:
        result = parse_xml_file(file_name, logger)
        if result and filter_articles(result):
            # Correct JSON file naming
            article_file_name = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(file_name))[0]}.json")
            with open(article_file_name, 'w') as f:
                json.dump(result, f, indent=4)
            return True
    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
    return False

def parse_xml_folder(folder_path, output_folder, stderr_folder):
    """
    Parses a folder of XML files, filters the articles, and saves the results.
    """
    logger = setup_error_logging(stderr_folder)

    # Initialize the progress bar
    total_files = sum([len(files) for r, d, files in os.walk(folder_path) if any(file.endswith('.xml') for file in files)])
    with tqdm(total=total_files, desc="Processing files") as pbar:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    process_file(file_path, output_folder, logger)
                    pbar.update(1)

def main(folder_path, output_folder, stderr_folder):
    """
    Main function to parse XML files, filter them, and save the results.
    """
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(stderr_folder, exist_ok=True)
    parse_xml_folder(folder_path, output_folder, stderr_folder)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python memo.py <path_to_xml_folder> <path_to_output_folder> <path_to_stderr_folder>")
        sys.exit(1)
    folder_path = sys.argv[1]
    output_folder = sys.argv[2]
    stderr_folder = sys.argv[3]
    main(folder_path, output_folder, stderr_folder)
