import sys
import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QGroupBox, QRadioButton, QPushButton, QLineEdit,
    QLabel, QFormLayout, QMessageBox, QButtonGroup
)
from PyQt6.QtCore import Qt

LOG_TYPES = {
    "FBC": "Fieldbus Logs",
    "RPC": "RPC Counter Logs",
    "LOG": "Node Logs",
    "LIS": "Serial Listener Logs"
}

class NodeManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node Configuration")
        self.setMinimumSize(600, 400)
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "nodes.json")
        self.nodes_data = self.load_config()
        self.init_ui()
        self.populate_node_list()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Node list section
        node_group = QGroupBox("Nodes")
        node_layout = QVBoxLayout()
        self.node_list = QListWidget()
        self.node_list.itemSelectionChanged.connect(self.on_node_selected)
        node_layout.addWidget(self.node_list)
        
        self.add_btn = QPushButton("+ Add Node")
        self.add_btn.clicked.connect(self.add_node)
        self.remove_btn = QPushButton("- Remove Selected")
        self.remove_btn.clicked.connect(self.remove_node)
        node_layout.addWidget(self.add_btn)
        node_layout.addWidget(self.remove_btn)
        node_group.setLayout(node_layout)
        
        # Configuration section
        config_group = QGroupBox("Node Configuration")
        config_layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Comma separated tokens (162,163)")
        
        form = QFormLayout()
        form.addRow("Node Name:", self.name_input)
        form.addRow("Tokens:", self.token_input)
        
        # Log types section
        type_group = QGroupBox("Log Types")
        type_layout = QVBoxLayout()
        self.type_buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(False)
        
        for type_id, label in LOG_TYPES.items():
            btn = QRadioButton(f"{type_id}: {label}")
            btn.setProperty("type_id", type_id)
            self.button_group.addButton(btn)
            self.type_buttons[type_id] = btn
            type_layout.addWidget(btn)
        
        type_group.setLayout(type_layout)
        
        # Action buttons
        self.save_btn = QPushButton("Save to JSON")
        self.save_btn.clicked.connect(self.save_config)
        self.create_files_btn = QPushButton("Create Files and Folders")
        self.create_files_btn.clicked.connect(self.create_files)
        
        config_layout.addLayout(form)
        config_layout.addWidget(type_group)
        config_layout.addWidget(QLabel("Example Files:"))
        self.example_label = QLabel("No examples generated yet")
        config_layout.addWidget(self.example_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.create_files_btn)
        config_layout.addLayout(btn_layout)
        config_group.setLayout(config_layout)
        
        # Assemble main layout
        main_layout.addWidget(node_group, 45)
        main_layout.addWidget(config_group, 55)
        self.setLayout(main_layout)
    
    def create_files(self):
        """Create files and folders based on the current node configuration"""
        from log_creator import LogCreator
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
        base_output_dir = os.path.join(parent_dir, "_DIA")
        
        # Ensure nodes.json saved to disk before creating files
        self.save_config(silent=True)
        
        # Create all files and folders
        results = LogCreator.create_all_nodes(
            source_file=self.config_file,
            base_output_dir=base_output_dir,
            interactive=False,
            content_template="# $FILENAME\n# Log created: $DATETIME\n\nAdd log entries below this line\n"
        )
        
        # Process results to count success/failure
        total_created = 0
        for category in results.values():
            for status in category.values():
                if "Created" in status:
                    total_created += 1
        
        QMessageBox.information(
            self, 
            "Log Structure Created", 
            f"Successfully created {total_created} files and folders!"
        )
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []
    
    def save_config(self, silent=False):
        selected = self.node_list.currentRow()
        if selected >= 0:
            self.validate_current()
            
        # Save as JSON for Node Manager
        with open(self.config_file, 'w') as f:
            # Use compact JSON formatting
            f.write('[\n')
            for i, node in enumerate(self.nodes_data):
                tokens = ', '.join([f'"{t}"' for t in node['tokens']])
                types = ', '.join([f'"{t}"' for t in node['types']])
                
                f.write('    {\n')
                f.write(f'        "name": "{node["name"]}",\n')
                f.write(f'        "tokens": [{tokens}],\n')
                f.write(f'        "types": [{types}]\n')
                
                if i < len(self.nodes_data) - 1:
                    f.write('    },\n')
                else:
                    f.write('    }\n')
            f.write(']')
            
        if not silent:
            QMessageBox.information(self, "Saved", "Configuration saved successfully!")
        
        # Also save as text format for Log Creator
        txt_config = self.config_file.replace(".json", ".txt")
        with open(txt_config, 'w') as f:
            for node in self.nodes_data:
                if node['tokens']:
                    tokens_str = ','.join(node['tokens'])
                    f.write(f"{node['name']}:{tokens_str}\n")
                else:
                    f.write(f"{node['name']}\n")
    
    def populate_node_list(self):
        self.node_list.clear()
        for node in self.nodes_data:
            node_label = node['name'] 
            if node.get('tokens'):
                node_label += f" ({', '.join(node['tokens'])})"
            types = [t for t in LOG_TYPES.keys() if t in node.get('types', [])]
            if types:
                node_label += f" [{', '.join(types)}]"
            self.node_list.addItem(node_label)
    
    def on_node_selected(self):
        selected = self.node_list.currentRow()
        if selected >= 0:
            node_data = self.nodes_data[selected]
            self.name_input.setText(node_data['name'])
            self.token_input.setText(", ".join(node_data.get('tokens', [])))
            
            # Clear all selections first
            for btn in self.type_buttons.values():
                btn.setChecked(False)
                
            # Set selected types
            for t in node_data.get('types', []):
                if t in self.type_buttons:
                    self.type_buttons[t].setChecked(True)
                    
            self.generate_example()
    
    def generate_example(self):
        if not self.name_input.text():
            return
            
        node_name = self.name_input.text().strip()
        tokens = [t.strip() for t in self.token_input.text().split(',') if t.strip()]
        selected_types = [t for t, btn in self.type_buttons.items() if btn.isChecked()]
        
        examples = []
        for t in selected_types:
            if t in ["FBC", "RPC"] and tokens:
                for idx, token in enumerate(tokens[:3]):
                    if t == "FBC":
                        # Extract last digit for FBC number
                        fbc_num = int(token) % 10 if token.isdigit() else 1
                        examples.append(f"• {node_name}_{token}_fbc{fbc_num}.txt")
                    else:
                        examples.append(f"• {node_name}_{token}_rpc.txt")
            elif t == "LOG":
                examples.append(f"• {node_name}_log.txt")
            elif t == "LIS":
                examples.append(f"• {node_name}/exe1_5irb_5orb.txt")
                
        self.example_label.setText("\n".join(examples) if examples else "No examples generated")
    
    def add_node(self):
        new_data = {"name": "", "types": [], "tokens": []}
        self.nodes_data.append(new_data)
        self.populate_node_list()
        self.node_list.setCurrentRow(len(self.nodes_data)-1)
    
    def remove_node(self):
        selected = self.node_list.currentRow()
        if selected >= 0:
            self.nodes_data.pop(selected)
            self.populate_node_list()
    
    def validate_current(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Node name cannot be empty!")
            return False
            
        tokens = [t.strip() for t in self.token_input.text().split(',') if t.strip()]
        selected_types = [t for t, btn in self.type_buttons.items() if btn.isChecked()]
        
        # Validate token requirements
        if not tokens and any(t in ["FBC", "RPC"] for t in selected_types):
            QMessageBox.warning(self, "Validation", 
                               "FBC and RPC log types require tokens!")
            return False
            
        # Update node data
        selected = self.node_list.currentRow()
        if selected >= 0:
            self.nodes_data[selected] = {
                "name": name,
                "tokens": tokens,
                "types": selected_types
            }
        
        self.populate_node_list()
        return True
    

