from typing import List, Dict
import os
from pathlib import Path

class LogProcessor:
    def __init__(self):
        self.supported_ext = ('.log', '.txt', '.text')
        
    def process_directory(self, dir_path: str) -> List[Dict]:
        """Process all log files recursively"""
        path = Path(dir_path)
        processed_files = []
        
        # Recursive walk through directory
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_ext:
                processed_files.append(self.process_file(file_path))
        
        return processed_files

    def process_file(self, filepath: Path) -> Dict:
        """Process single log file"""
        try:
            return {
                'filename': filepath.name,
                'path': str(filepath.parent),
                'content': self._read_content(filepath)
            }
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return {
                'filename': filepath.name,
                'path': str(filepath.parent),
                'content': [f"ERROR READING FILE: {str(e)}"]
            }
    
    def _read_content(self, filepath: Path) -> List[str]:
        """Read file with encoding fallback"""
        encodings = ['utf-8', 'ascii', 'latin-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not read {filepath} with any supported encoding")