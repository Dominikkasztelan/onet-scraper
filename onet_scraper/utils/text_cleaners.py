import json
from pathlib import Path

from typing import Dict, List

def load_cleaning_rules() -> Dict[str, List[str]]:
    """
    Loads cleaning rules from resources/cleaning_rules.json
    """
    try:
        current_dir = Path(__file__).parent
        # Go up one level to onet_scraper, then to resources
        config_path = current_dir.parent / 'resources' / 'cleaning_rules.json'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️ Failed to load cleaning rules: {e}")
        return {"scam_phrases": [], "cutoff_markers": []}

# Load rules once on module import
RULES = load_cleaning_rules()

def clean_article_content(content_list: list[str]) -> str:
    """
    Cleans the raw content list by removing boilerplate, scams, and handling whitespace.
    """
    if not content_list:
        return ""
        
    full_content = "\n".join(content_list)
    
    # Normalize text
    clean_content = full_content.replace('\xa0', ' ')
    
    # Filter out known boilerplates from Config
    scam_phrases = RULES.get("scam_phrases", [])
    
    # Cutoff markers - stop reading if we hit these
    cutoff_markers = RULES.get("cutoff_markers", [])
    
    for marker in cutoff_markers:
        if marker in clean_content:
            clean_content = clean_content.split(marker)[0]
    
    # Remove other junk lines
    lines = clean_content.split('\n')
    filtered_lines = []
    for line in lines:
        # Skip lines containing scam phrases (double check after split)
        if any(phrase in line for phrase in scam_phrases):
            continue
        # Skip lines that are just whitespace
        if not line.strip():
            continue
        # Skip very short lines that might be artifacts (unless they look like subheaders?)
        if len(line.strip()) < 3: 
            continue
        filtered_lines.append(line)
    
    return "\n".join(filtered_lines).strip()
