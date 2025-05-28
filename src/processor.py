from typing import List, Dict
import os
from pathlib import Path

class LogProcessor:
    def __init__(self):
        self.supported_ext = ('.log', '.txt', '.text')
        
    def get_folder_hierarchy(self, base_path: str, files: List[str]) -> Dict:
        """Organize files by folder structure"""
        structure = {}
        for file_path in files:
            parts = Path(file_path).relative_to(base_path).parts
            current_level = structure
            # Navigate through folder structure
            for part in parts[:-1]:  # Skip filename part
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = file_path  # Add filename at leaf level
        return structure

    def process_directory(self, dir_path: str) -> List[Dict]:
        """Process files with folder structure"""
        path = Path(dir_path)
        files = [
            str(f) for f in path.rglob('*')
            if f.is_file() and f.suffix.lower() in self.supported_ext
        ]
        
        hierarchy = self.get_folder_hierarchy(dir_path, files)
        return self._process_hierarchy(hierarchy)
    
    def _process_hierarchy(self, node: Dict, path: str = "") -> List[Dict]:
        """Recursively process folder structure"""
        result = []
        for name, item in node.items():
            if isinstance(item, dict):
                # Folder node - create chapter
                result.append({
                    'type': 'chapter',
                    'level': path.count('/') + 1,
                    'name': name,
                    'path': f"{path}/{name}" if path else name
                })
                result.extend(self._process_hierarchy(item, f"{path}/{name}" if path else name))
            else:
                # File node
                result.append({
                    'type': 'file',
                    'content': self._read_content(Path(item)),
                    'filename': name,
                    'path': path
                })
        return result
        
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