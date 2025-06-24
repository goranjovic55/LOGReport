import re

def filter_telnet_output(text: str) -> str:
    """
    Filters telnet output from automation debugger sessions
    by removing control characters, mode transitions, and overlapping fragments
    """
    # Step 1: Remove terminal control sequences
    # This includes ANSI escape codes and other control characters
    text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
    
    # Step 2: Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # Step 3: Remove specific mode transition artifacts
    text = re.sub(r'\~\d+~\d+~', ' ', text)
    
    # Step 4: Remove overlapping command artifacts
    # This regex handles "commandtextitoggleure" patterns
    text = re.sub(r'[a-zA-Z]+texitoggleure', '', text)
    
    # Step 5: Clean up remaining tildes and distorted characters
    text = re.sub(r'[~]+', ' ', text)
    text = re.sub(r'(\w)\1{2,}', r'\1', text)  # Remove character repeats
    
    # Step 6: Remove empty parentheses and brackets
    text = re.sub(r'\[[\s]*\]', '', text)
    text = re.sub(r'\([\s]*\)', '', text)
    
    # Step 7: Replace common garbage strings
    garbage_patterns = [
        r'toggleure',
        r'texitoggle',
        r'exitoggleure',
        r'printstructure',
        r'Editor changed to (INSERT|REPLACE) mode',
        r'[\d]+[a-z]%'
    ]
    
    for pattern in garbage_patterns:
        text = re.sub(pattern, '', text)
    
    # Step 8: Final cleanup
    text = text.replace('>', '')  # Remove stray prompts
    text = re.sub(r'[ ]{2,}', ' ', text)  # Remove extra spaces
    return text.strip()
