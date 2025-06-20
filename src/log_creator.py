import os
import json
import time
from pathlib import Path
from typing import Dict, List, Union

class LogCreator:
    @staticmethod
    def create_file_structure(output_dir: str, nodes: list, content_template: str) -> Dict[str, str]:
        """Simple implementation to create log files and folders"""
        results = {}
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for node in nodes:
            node_name = str(node['name']).replace(" ", "_")
            node_types = node.get('types', [])
            tokens = [str(t) for t in node.get('tokens', [])]
            
            if not node_types:
                continue
                
            # Format IP address for filename (replace dots with hyphens)
            ip_formatted = node.get('ip', '192.168.0.1').replace('.', '-')
            
            if "FBC" in node_types and tokens:
                # Create node directory for FBC files
                node_dir = Path(output_dir) / "FBC" / node_name
                node_dir.mkdir(parents=True, exist_ok=True)
                
                # Create FBC files with IP in filename
                for token in tokens[:3]:
                    filename = f"{node_name}_{ip_formatted}_{token}.fbc"
                    file_path = node_dir / filename
                    
                    if not file_path.exists():
                        content = content_template \
                            .replace('$FILENAME', filename) \
                            .replace('$DATETIME', time.strftime("%Y-%m-%d %H:%M:%S"))
                        with open(file_path, 'w') as f:
                            f.write(content)
                        results[str(file_path)] = "Created FBC"
                    
            if "RPC" in node_types and tokens:
                # Create node directory for RPC files
                node_dir = Path(output_dir) / "RPC" / node_name
                node_dir.mkdir(parents=True, exist_ok=True)
                
                # Create RPC files with IP in filename
                for token in tokens[:3]:
                    filename = f"{node_name}_{ip_formatted}_{token}.rpc"
                    file_path = node_dir / filename
                    
                    if not file_path.exists():
                        content = content_template \
                            .replace('$FILENAME', filename) \
                            .replace('$DATETIME', time.strftime("%Y-%m-%d %H:%M:%S"))
                        with open(file_path, 'w') as f:
                            f.write(content)
                        results[str(file_path)] = "Created RPC"
                        
            if "LOG" in node_types:
                # Create LOG directory
                log_dir = Path(output_dir) / "LOG"
                log_dir.mkdir(exist_ok=True)
                
                # Create log file with IP in filename (use log extension as per example)
                filename = f"{node_name}_{ip_formatted}.log"
                file_path = log_dir / filename
                
                if not file_path.exists():
                    content = content_template \
                        .replace('$FILENAME', filename) \
                        .replace('$DATETIME', time.strftime("%Y-%m-%d %H:%M:%S"))
                    with open(file_path, 'w') as f:
                        f.write(content)
                    results[str(file_path)] = "Created LOG"
                    
            if "LIS" in node_types:
                # Create LIS directory structure with node_name
                lis_dir = Path(output_dir) / "LIS" / node_name
                lis_dir.mkdir(parents=True, exist_ok=True)
                
                # Create 6 files with the updated pattern including IP address
                for i in range(1, 7):
                    filename = f"{node_name}_{ip_formatted}_exe{i}_5irb_5orb.lis"
                    file_path = lis_dir / filename
                    
                    if not file_path.exists():
                        content = content_template \
                            .replace('$FILENAME', filename) \
                            .replace('$DATETIME', time.strftime("%Y-%m-%d %H:%M:%S"))
                        with open(file_path, 'w') as f:
                            f.write(content)
                        results[str(file_path)] = "Created LIS"
        
        return results

    @staticmethod
    def create_all_nodes(source_file: str, base_output_dir: str, content_template: str, **kwargs) -> Dict[str, Dict[str, str]]:
        """Wrapper method for compatibility with existing calls"""
        with open(source_file, 'r') as f:
            nodes = json.load(f)
            
        # Create all files using our new implementation
        created_files = LogCreator.create_file_structure(base_output_dir, nodes, content_template)
        
        # Format results to match old structure
        results = {
            "fbc": {k: v for k, v in created_files.items() if "FBC" in v},
            "rpc": {k: v for k, v in created_files.items() if "RPC" in v},
            "log": {k: v for k, v in created_files.items() if "LOG" in v},
            "lis": {k: v for k, v in created_files.items() if "LIS" in v},
        }
        return results
