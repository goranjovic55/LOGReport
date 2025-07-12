import os
import re
import shutil
import json
import argparse
from typing import Dict, List, Tuple
from pathlib import Path

def load_node_config(config_path: str) -> Dict[str, dict]:
    """Load node configuration from JSON file"""
    with open(config_path, 'r') as f:
        return {node['name']: node for node in json.load(f)}

def parse_filename(filename: str) -> Tuple[str, str, str]:
    """Parse filename into node_name, token_id, token_type"""
    # Handle both old and new filename patterns
    match = re.match(r'^(\w+)_(\d+)_(\w+)\.log$', filename)
    if match:
        return match.groups()
    return None, None, None

def restructure_logs(log_root: str, node_config: Dict[str, dict]):
    """Restructure log directories and rename files to new format"""
    # First pass: collect all log files
    log_files = []
    for root, _, files in os.walk(log_root):
        for file in files:
            if file.lower().endswith(('.log', '.fbc', '.rpc', '.lis')):
                log_files.append(os.path.join(root, file))
    
    # Process each log file
    for file_path in log_files:
        filename = os.path.basename(file_path)
        node_name, token_id, token_type = parse_filename(filename)
        
        if not node_name or not token_id or not token_type:
            print(f"Skipping invalid filename: {filename}")
            continue
        
        # Find matching node
        node = node_config.get(node_name)
        if not node:
            print(f"Node not found for {filename}")
            continue
        
        # Get IP address for this token
        token = next((t for t in node['tokens'] if t['token_id'] == token_id), None)
        if not token:
            print(f"Token {token_id} not found for node {node_name}")
            continue
        
        # Format IP address: 192.168.0.11 -> 192-168-0-11
        formatted_ip = token['ip_address'].replace('.', '-')
        
        # Create new filename: <node_name>_<ip>_<token_id>.<ext>
        ext = os.path.splitext(filename)[1]
        new_filename = f"{node_name}_{formatted_ip}_{token_id}{ext}"
        
        # Create new directory: <log_root>/<token_type>/<node_name>
        new_dir = os.path.join(log_root, token_type, node_name)
        os.makedirs(new_dir, exist_ok=True)
        
        # Move and rename file
        new_path = os.path.join(new_dir, new_filename)
        shutil.move(file_path, new_path)
        print(f"Moved {filename} -> {new_path}")

def main():
    parser = argparse.ArgumentParser(description='Restructure log files')
    parser.add_argument('--log-dir', default='test_logs', help='Root directory of log files')
    parser.add_argument('--config', default='nodes.json', help='Path to nodes.json config file')
    args = parser.parse_args()

    # Load node configuration
    node_config = load_node_config(args.config)
    
    # Restructure logs
    restructure_logs(args.log_dir, node_config)

if __name__ == '__main__':
    main()