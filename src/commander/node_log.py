import os
from typing import Optional

class NodeLogMixin:
    """Provides log scanning helpers for NodeManager."""

    def set_log_root(self, path):
        """Set the root folder for log files and rescan."""
        self.log_root = path
        self.scan_log_files()

    def scan_log_files(self, log_root=None):
        """Scan filesystem for existing log files."""
        root = log_root or self.log_root
        if not os.path.exists(root):
            return
        for token_type in os.listdir(root):
            token_type_path = os.path.join(root, token_type)
            if not os.path.isdir(token_type_path) or token_type.upper() not in ["FBC", "LIS", "LOG", "RPC"]:
                continue
            for node_folder in os.listdir(token_type_path):
                node_path = os.path.join(token_type_path, node_folder)
                if not os.path.isdir(node_path):
                    continue
                matched_node = next((n for n in self.nodes.values() if n.name.lower() == node_folder.lower()), None)
                if not matched_node:
                    continue
                for filename in os.listdir(node_path):
                    if not filename.lower().endswith((".log", ".txt")):
                        continue
                    try:
                        base_name = os.path.splitext(filename)[0]
                        parts = base_name.split('_')
                        if len(parts) < 4:
                            continue
                        file_node_name = parts[0]
                        token_id = parts[-2]
                        file_token_type = parts[-1]
                        if file_node_name.lower() != node_folder.lower():
                            continue
                        if file_token_type.lower() != token_type.lower():
                            continue
                        token = next((t for t in matched_node.tokens.values() if t.token_id.lower() == token_id.lower()), None)
                        if token:
                            token.log_path = os.path.join(node_path, filename)
                    except Exception as e:
                        print(f"Error processing {filename}: {str(e)}")

    def _generate_log_path(self, node_name: str, token_id: str, log_type: str) -> str:
        """Generate standardized log path for a token."""
        return os.path.join(self.log_root, node_name, f"{token_id}_{log_type}.log")

