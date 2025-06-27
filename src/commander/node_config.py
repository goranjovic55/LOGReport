import json
import os
from typing import Optional, Dict, List
from .models import Node, NodeToken

class NodeConfigMixin:
    """Provides configuration loading and saving helpers for NodeManager."""

    def set_config_path(self, path):
        """Set the configuration file path."""
        self.config_path = path

    def load_configuration(self, file_path: str = None) -> bool:
        """Load node configuration from JSON file."""
        path = file_path or self.config_path
        if not path:
            print("Configuration path is empty")
            return False
        try:
            abs_path = os.path.abspath(path)
            print(f"Loading configuration from: {abs_path}")
            if not os.path.exists(abs_path):
                print(f"Configuration file does not exist: {abs_path}")
                return False
            with open(abs_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self._parse_config(config_data)
            print("Configuration loaded successfully")
            return True
        except FileNotFoundError:
            print(f"File not found: {path}")
            return False
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in {path}: {str(e)}")
            return False
        except KeyError as e:
            print(f"Missing required key in configuration: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error loading configuration: {str(e)}")
            return False

    def _parse_config(self, config_data: dict):
        """Parse configuration JSON into Node objects."""
        self.nodes.clear()
        if isinstance(config_data, list) and config_data:
            first_node = config_data[0]
            is_old_format = (
                'ip' in first_node and
                'tokens' in first_node and
                isinstance(first_node['tokens'], list) and
                all(isinstance(t, str) for t in first_node['tokens'])
            )
            if is_old_format:
                print("Detected old format - converting to new format")
                config_data = self._convert_old_format(config_data)

        for node_data in config_data:
            try:
                if "name" not in node_data or "ip_address" not in node_data:
                    print(f"Skipping invalid node entry: {node_data}")
                    continue
                node = Node(name=node_data["name"], ip_address=node_data["ip_address"])
                tokens = node_data.get("tokens", [])
                for token_data in tokens:
                    try:
                        if "token_id" not in token_data or "token_type" not in token_data or "port" not in token_data:
                            print(f"Skipping invalid token entry: {token_data}")
                            continue
                        token = NodeToken(
                            name=f"{node.name} {token_data['token_id']}",
                            token_id=token_data["token_id"],
                            token_type=token_data["token_type"],
                            ip_address=token_data.get("ip_address", node.ip_address),
                            port=token_data["port"],
                            protocol=token_data.get("protocol", "telnet")
                        )
                        token.log_path = self._generate_log_path(node.name, token.token_id, token.token_type)
                        node.add_token(token)
                    except Exception as e:
                        print(f"Error processing token: {str(e)}")
                self.nodes[node.name] = node
            except Exception as e:
                print(f"Error processing node: {str(e)}")

    def _convert_old_format(self, old_config: list) -> list:
        """Convert legacy configuration format."""
        new_config = []
        for node in old_config:
            if 'ip' not in node:
                continue
            tokens = []
            token_ids = node.get('tokens', [])
            token_types = node.get('types', ['UNKNOWN'] * len(token_ids))
            for i, token_id in enumerate(token_ids):
                token_type = token_types[i] if i < len(token_types) else 'UNKNOWN'
                tokens.append({"token_id": str(token_id), "token_type": token_type, "port": 23})
            new_config.append({"name": node["name"], "ip_address": node["ip"], "tokens": tokens})
        return new_config

    def save_configuration(self, file_path: str = None) -> bool:
        """Save current configuration to JSON file."""
        if file_path is None:
            file_path = self.config_path
        config_data: List[Dict] = []
        for node in self.nodes.values():
            node_data = {
                "name": node.name,
                "ip_address": node.ip_address,
                "tokens": []
            }
            for token in node.tokens.values():
                token_data = {
                    "token_id": token.token_id,
                    "token_type": token.token_type,
                    "ip_address": token.ip_address,
                    "port": token.port,
                    "protocol": token.protocol
                }
                node_data["tokens"].append(token_data)
            config_data.append(node_data)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            return True
        except (OSError, TypeError):
            return False

    def create_empty_config(self, file_path: str):
        """Create an empty configuration file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

