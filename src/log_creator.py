import os
import time
from pathlib import Path  # Corrected import
import json
from typing import Dict, Union, List, Tuple

class LogCreator:
    @staticmethod
    def parse_nodes_file(source_file: str, required_type: str = None) -> Dict[str, List[str]]:
        """
        Parse nodes JSON file with token mappings
        Format: [ { "name": "node1", "tokens": ["t1", "t2"], "types": ["FBC", "RPC"] }, ...]
        
        Args:
            required_type (str): Filter nodes by log type (FBC, RPC, LOG, LIS)
            
        Returns:
            Dictionary with node names as keys and token lists as values
        """
        if not os.path.exists(source_file):
            return {}
            
        try:
            with open(source_file, 'r') as f:
                nodes_data = json.load(f)
                
            filtered_nodes = {}
            for node in nodes_data:
                # Skip nodes that don't have required type
                if required_type and required_type not in node.get('types', []):
                    continue
                    
                filtered_nodes[node['name']] = node.get('tokens', [])
            
            return filtered_nodes
        except Exception as e:
            print(f"Error parsing nodes file: {str(e)}")
            return {}
    
    @staticmethod
    def create_log_structure(root_path: str, structure: Dict[str, Union[str, dict]], template: str = None) -> Dict[str, str]:
        """Hierarchical log structure creation method""" 
        # Implementation remains the same
        return {}

    @staticmethod
    def create_fbc_nodes(
        source_file: str,
        output_dir: str = "_FBC",
        interactive: bool = False,
        content_template: str = "# FBC file: $FILENAME\n# Created: $DATETIME\n\n"
    ) -> Dict[str, str]:
        """Create FBC node files"""
        return LogCreator._create_generic_nodes(
            source_file=source_file,
            output_dir=output_dir,
            interactive=interactive,
            content_template=content_template,
            node_type="AP",
            use_tokens=True,
            suffix_style="fbc",
            required_type="FBC"  # New argument for type filtering
        )

    @staticmethod
    def create_rpc_nodes(
        source_file: str,
        output_dir: str = "_RPC",
        interactive: bool = False,
        content_template: str = "# RPC file: $FILENAME\n# Created: $DATETIME\n\n"
    ) -> Dict[str, str]:
        """Create RPC node files"""
        return LogCreator._create_generic_nodes(
            source_file=source_file,
            output_dir=output_dir,
            interactive=interactive,
            content_template=content_template,
            node_type="AP",
            use_tokens=True,
            suffix_style="rpc",
            required_type="RPC"  # New argument for type filtering
        )

    @staticmethod
    def create_log_nodes(
        source_file: str,
        output_dir: str = "_LOG",
        interactive: bool = False,
        content_template: str = "# Log file: $FILENAME\n# Created: $DATETIME\n\n"
    ) -> Dict[str, str]:
        """Create standard log files"""
        return LogCreator._create_generic_nodes(
            source_file=source_file,
            output_dir=output_dir,
            interactive=interactive,
            content_template=content_template,
            node_type=("AL", "AP"),
            use_tokens=False,
            suffix_style="log",
            required_type="LOG"  # New argument for type filtering
        )
    
    @staticmethod
    def create_irb_orb_nodes(
        source_file: str,
        output_dir: str = "_LIS",
        interactive: bool = False,
        content_template: str = "# IRB/ORB file: $FILENAME\n# Created: $DATETIME\n\n"
    ) -> Dict[str, str]:
        """Create IRB/ORB node files with directory structure"""
        nodes_dict = LogCreator.parse_nodes_file(source_file, "LIS")  # Require LIS type
        results = {}
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        created_count = 0
        skipped_count = 0
        
        for node in nodes_dict.keys():
            # No need for additional prefix filter - already filtered by type
                
            # Create node directory
            node_folder = os.path.join(output_dir, node)
            if not os.path.exists(node_folder):
                os.makedirs(node_folder)
                results[node_folder] = "Folder created"
            
            # Create 6 files for each node
            for i in range(1, 7):
                filename = f"{node}_exe{i}_5irb_5orb.txt"
                filepath = os.path.join(node_folder, filename)
                
                content = content_template.replace("$FILENAME", filename).replace("$DATETIME", timestamp)
                file_exists = os.path.exists(filepath)
                status = ""
                
                if file_exists and interactive:
                    overwrite = input(f"Overwrite {filepath}? (y/N) ").strip().lower()
                    if overwrite in ["y", "yes"]:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        status = "Overwritten"
                        created_count += 1
                    else:
                        status = "Skipped (exists)"
                        skipped_count += 1
                elif file_exists:
                    status = "Skipped (exists)"
                    skipped_count += 1
                else:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    status = "Created"
                    created_count += 1
                    
                results[filepath] = status  # Fixed variable name
        
        print(f"IRB/ORB: Created {created_count} files, skipped {skipped_count}")
        return results

    @staticmethod
    def _create_generic_nodes(
        source_file: str,
        output_dir: str,
        interactive: bool,
        content_template: str,
        node_type: Union[str, Tuple[str]],
        use_tokens: bool,
        suffix_style: str,
        required_type: str = None
    ) -> Dict[str, str]:
        """Core implementation for node creation methods"""
        nodes_dict = LogCreator.parse_nodes_file(source_file, required_type)
        results = {}
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        created_count = 0
        skipped_count = 0
        
        for node, tokens in nodes_dict.items():
            # Filter by node prefix (additional to type filter)
            if isinstance(node_type, tuple):
                if not any(node.startswith(t) for t in node_type):
                    continue
            elif not node.startswith(node_type):
                continue
            
            items = tokens if use_tokens else [""]
            
            for item in items:
                # Generate filename according to style
                if suffix_style == "fbc":
                    filename = f"{node}_{item}.txt"
                elif suffix_style == "rpc":
                    filename = f"{node}_{item}_rpc.txt"
                elif suffix_style == "log":
                    filename = f"{node}_log.txt" if node.startswith("AL") else f"{node}_log_{item}.txt"
                
                filepath = os.path.join(output_dir, filename)
                content = content_template.replace("$FILENAME", filename).replace("$DATETIME", timestamp)
                file_exists = os.path.exists(filepath)
                
                if file_exists and interactive:
                    overwrite = input(f"Overwrite {filepath}? (y/N) ").strip().lower()
                    if overwrite in ["y", "yes"]:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        status = "Overwritten"
                        created_count += 1
                    else:
                        status = "Skipped (exists)"
                        skipped_count += 1
                elif file_exists:
                    status = "Skipped (exists)"
                    skipped_count += 1
                else:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    status = "Created"
                    created_count += 1
                    
                results[filepath] = status
        
        print(f"{suffix_style.upper()}: Created {created_count} files, skipped {skipped_count}")
        return results

    @staticmethod
    def create_all_nodes(
        source_file: str,
        base_output_dir: str = "_DIA",
        interactive: bool = False,
        content_template: str = "# Log file: $FILENAME\n# Created: $DATETIME\n\n"
    ) -> Dict[str, Dict[str, str]]:
        """Create all node types under _DIA directory"""
        Path(base_output_dir).mkdir(parents=True, exist_ok=True)
        results = {}
        
        # Create FBC nodes in _DIA/FBC
        results["fbc"] = LogCreator.create_fbc_nodes(
            source_file=source_file,
            output_dir=os.path.join(base_output_dir, "FBC"),
            interactive=interactive,
            content_template=content_template
        )
        
        # Create RPC nodes in _DIA/RPC
        results["rpc"] = LogCreator.create_rpc_nodes(
            source_file=source_file,
            output_dir=os.path.join(base_output_dir, "RPC"),
            interactive=interactive,
            content_template=content_template
        )
        
        # Create log nodes in _DIA/LOG
        results["log"] = LogCreator.create_log_nodes(
            source_file=source_file,
            output_dir=os.path.join(base_output_dir, "LOG"),
            interactive=interactive,
            content_template=content_template
        )
        
        # Create IRB/ORB nodes in _DIA/LIS
        results["irb_orb"] = LogCreator.create_irb_orb_nodes(
            source_file=source_file,
            output_dir=os.path.join(base_output_dir, "LIS"),
            interactive=interactive,
            content_template=content_template
        )
        
        return results

if __name__ == "__main__":
    # Production log creation
    print("Creating production logs in _DIA structure...")
    results = LogCreator.create_all_nodes(
        source_file="nodes.json",  # Changed to use JSON format
        base_output_dir="_DIA",
        interactive=False,
        content_template="# $FILENAME\n# Log created: $DATETIME\n\nAdd log entries below this line\n"
    )
    
    print("\nLog Creation Summary:")
    print("=====================")
    for category, files in results.items():
        created = sum(1 for status in files.values() if status.startswith("Created") or status.startswith("Overwritten"))
        skipped = sum(1 for status in files.values() if "Skipped" in status)
        print(f"  {category.upper()}: {created} files created, {skipped} files skipped")
    
    print("\nProduction log creation completed successfully!")
