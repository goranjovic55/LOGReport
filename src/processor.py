from typing import List, Dict, Optional, Union
import os
from pathlib import Path

class LogProcessor:
    def __init__(self):
        self.supported_ext = ('.log', '.txt', '.text')
        self.line_limit = None  # Can be set via GUI
        self.lines_mode = "first"  # or "last", "range"
        self.line_range = (0, 0)   # (start, end) for range mode
        
    def set_line_options(self, *, limit: Optional[int] = None, 
                        mode: str = "first", 
                        line_range: tuple = (0, 0)):
        """Update line filtering options"""
        self.line_limit = limit
        self.lines_mode = mode.lower()
        self.line_range = line_range

    def _filter_lines(self, lines: List[str]) -> List[str]:
        """Apply line filtering based on current settings"""
        if not self.line_limit and self.lines_mode != "range":
            return lines
            
        if self.lines_mode == "first":
            return lines[:self.line_limit]
        elif self.lines_mode == "last":
            return lines[-self.line_limit:]
        elif self.lines_mode == "range":
            start, end = self.line_range
            return lines[start-1:end]  # Convert to 0-based index
        return lines

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

    def process_directory(self, directory):
        results = []
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.log', '.txt')):  # Note: .text not included as per CHANGE
                        full_path = os.path.normpath(os.path.join(root, file))
                        results.append({
                            'type': 'file',
                            'content': self._read_content(Path(full_path)),
                            'filename': file,
                            'path': root
                        })
            return results
        except Exception as e:
            raise Exception(f"Directory scan failed: {str(e)}")

    def process_file(self, file_path):
        """Process single file and return dict with metadata and lines"""
        try:
            content = self._read_content(file_path)
            return {
                'filename': os.path.basename(file_path),
                'modified': os.path.getmtime(file_path),
                'content': content,
                'path': file_path
            }
        except Exception as e:
            return {
                'filename': os.path.basename(file_path),
                'error': str(e)
            }
    
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
        """Read file with encoding fallback and line filtering"""
        encodings = ['utf-8', 'ascii', 'latin-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    return self._filter_lines(lines)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not read {filepath} with any supported encoding")