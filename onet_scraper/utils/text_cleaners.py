
def clean_article_content(content_list: list[str]) -> str:
    """
    Cleans the raw content list by removing boilerplate, scams, and handling whitespace.
    """
    if not content_list:
        return ""
        
    full_content = "\n".join(content_list)
    
    # Normalize text
    clean_content = full_content.replace('\xa0', ' ')
    
    # Filter out known boilerplates
    scam_phrases = [
        "Dołącz do Premium",
        "i odblokuj wszystkie funkcje", 
        "dla materiałów Premium",
        "Onet Premium",
        "Kliknij tutaj",
        "Zobacz także",
        "redakcja", # Often at the end
        "Źródło:"
    ]
    
    # Cutoff markers - stop reading if we hit these
    cutoff_markers = [
        "Dołącz do Premium",
        "i odblokuj wszystkie funkcje",
        "Zobacz także",
        "Onet Premium"
    ]
    
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
