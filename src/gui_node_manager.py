import sys
import os
import json
import re  # Added for regex validation
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QGroupBox, QRadioButton, QPushButton, QLineEdit,
    QLabel, QFormLayout, QMessageBox, QButtonGroup,
    QFileDialog, QInputDialog, QWidget  # Added QWidget
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
        
        # Use cleanup layout if one exists
        if self.layout():
            # Properly remove existing layout
            QWidget().setLayout(self.layout())
        
        # Set configuration file path
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "nodes.json")
        self.nodes_data = self.load_config()  # Proper initialization
        
        # Set initial window size (before creating UI)
        self.resize(1100, 500)
        
        # Initialize UI with proper layout
        self.init_ui()
        self.populate_node_list()
        
    def init_ui(self):
        # Create UI components
        main_layout = QHBoxLayout()
        
        # ... [rest of UI creation code remains the same] ...
        
        # Set button minimum widths at the end of UI initialization
        if hasattr(self, 'load_btn'):
            self.load_btn.setMinimumWidth(200)
        if hasattr(self, 'save_btn'):
            self.save_btn.setMinimumWidth(200)
        if hasattr(self, 'create_files_btn'):
            self.create_files_btn.setMinimumWidth(220)
        
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
        # Add Load button first
        self.load_btn = QPushButton("Load Configuration")
        self.load_btn.setMinimumWidth(180)  # Ensure consistent width
        self.load_btn.clicked.connect(self.load_configuration)
        btn_layout.addWidget(self.load_btn)
        
        self.save_btn.setMinimumWidth(180)  # Ensure consistent width
        btn_layout.addWidget(self.save_btn)
        
        self.create_files_btn.setMinimumWidth(180)  # Ensure consistent width
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
        import json
        
        # Validate current node configuration
        if self.node_list.currentRow() >= 0:
            if not self.validate_current():
                return
        
        # Choose output directory via dialog
        current_dir = os.path.dirname(__file__)
        base_output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Root Directory",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        )
        
        if not base_output_dir:
            return  # User cancelled

        try:
            # Save current node data to a temporary file
            with open("nodes_temp.json", "w") as f:
                json.dump(self.nodes_data, f, indent=2)
            
            # Create all files and folders in chosen location using temporary file
            results = LogCreator.create_all_nodes(
                "nodes_temp.json",
                base_output_dir,
                "# $FILENAME\n# Log created: $DATETIME\n\nAdd log entries below this line\n"
            )
            
            # Process results to count success/failure
            total_created = 0
            for category in results.values():
                for status in category.values():
                    if "Created" in status:
                        total_created += 1
            
            success_msg = (
                f"Successfully created {total_created} files and folders!\n\n"
                f"Created at: {base_output_dir}"
            )
            
            QMessageBox.information(
                self, 
                "Log Structure Created", 
                success_msg
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Creation Failed",
                f"Failed to create files/folders:\n{str(e)}"
            )
        finally:
            # Clean up temporary file if it exists
            if os.path.exists("nodes_temp.json"):
                os.remove("nodes_temp.json")
    
    def load_configuration(self):
        """Load configuration from selected JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Node Configuration",
            self.config_file,  # Start at current config location
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            
            # Validate basic structure
            if not isinstance(new_config, list):
                raise ValueError("Invalid configuration: Root should be an array")
            
            # Validate node entries
            errors = []
            for i, node in enumerate(new_config):
                if not isinstance(node, dict):
                    errors.append(f"Node {i}: Expected object but got {type(node).__name__}")
                    continue
                    
                if 'name' not in node:
                    errors.append(f"Node {i}: Missing 'name' field")
                    continue
                    
                # Validate name format: must start with AL/AP and digits
                if not node['name'].startswith(('AL', 'AP')):
                    errors.append(f"Node {node['name']}: Must start with 'AL' or 'AP'")
                elif not all(c.isdigit() for c in node['name'][2:4]):
                    errors.append(f"Node {node['name']}: Must have 2 digits after prefix")
                
                # Warn about missing properties
                if 'tokens' not in node:
                    node['tokens'] = []
                if 'types' not in node:
                    node['types'] = []
            
            if errors:
                error_msg = "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors)-5} more issues"
                QMessageBox.warning(
                    self,
                    "Configuration Issues",
                    f"Loading with warnings:\n\n{error_msg}"
                )
                
            # Update configuration
            self.nodes_data = new_config
            self.config_file = file_path  # Update default save location
            self.populate_node_list()
            QMessageBox.information(self, "Success", "Configuration loaded successfully")
            return True
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Parse Error",
                f"Invalid JSON format:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load configuration:\n{str(e)}"
            )
        return False
        
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
            
        # For silent saves, use the default location
        save_path = self.config_file
        
        # For non-silent saves, ask for new location
        if not silent:
            # Show file dialog with options
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Node Configuration As",
                self.config_file,
                "JSON Files (*.json);;All Files (*)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            if not save_path:
                return False  # User cancelled
                
        try:
            # Save as JSON for Node Manager
            with open(save_path, 'w') as f:
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
                
            # Also save as text format in the same location for Log Creator
            txt_config = os.path.splitext(save_path)[0] + ".txt"
            with open(txt_config, 'w') as f:
                for node in self.nodes_data:
                    if node['tokens']:
                        tokens_str = ','.join(node['tokens'])
                        f.write(f"{node['name']}:{tokens_str}\n")
                    else:
                        f.write(f"{node['name']}\n")
            
            # Update the default location for future saves
            self.config_file = save_path
            
            if not silent:
                QMessageBox.information(
                    self, 
                    "Saved", 
                    f"Configuration saved to:\n\n{save_path}\n"
                    f"Text version: {txt_config}"
                )
            return True
            
        except Exception as e:
            if not silent:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save configuration:\n{str(e)}"
                )
            return False
    
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
        if 0 <= selected < len(self.nodes_data):
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
                        examples.append(f"• .../{node_name}/{node_name}_{token}_fbc{fbc_num}.txt")
                    else:
                        examples.append(f"• .../{node_name}/{node_name}_{token}_rpc.txt")
            elif t == "LOG":
                examples.append(f"• .../{node_name}/{node_name}_log.txt")
            elif t == "LIS":
                examples.append(f"• .../{node_name}/exe1_5irb_5orb.txt")
                
        self.example_label.setText("\n".join(examples) if examples else "No examples generated\n(Choose configuration first)")
    
    def add_node(self):
        """Add a new node entry with validation"""
        # Start with empty entry
        new_data = {
            "name": "",   # Start with empty name
            "types": [],
            "tokens": []
        }
        self.nodes_data.append(new_data)
        self.populate_node_list()
        new_index = len(self.nodes_data) - 1
        self.node_list.setCurrentRow(new_index)
        self.name_input.setFocus()  # Focus name field for immediate editing
    
    def remove_node(self):
        selected = self.node_list.currentRow()
        if selected == -1:
            QMessageBox.information(self, "No Selection", "Please select a node to remove")
            return
            
        if selected >= 0 and selected < len(self.nodes_data):
            # Confirm node deletion
            node_name = self.nodes_data[selected]['name']
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Delete node '{node_name}'? This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.nodes_data.pop(selected)
                self.populate_node_list()
                
                # Clear inputs, selections, and examples
                self.name_input.clear()
                self.token_input.clear()
                for btn in self.type_buttons.values():
                    btn.setChecked(False)
                self.example_label.setText("No examples generated yet")
                
                # Clear selection highlight
                self.node_list.setCurrentRow(-1)
    
    def validate_current(self):
        """Validate and save current node configuration"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, 
                "Validation", 
                "Node name cannot be empty!"
            )
            return False
            
        # Validate name format
        if not re.match(r'^[A-Z]{2}\d{2}[a-z]?$', name):
            QMessageBox.warning(
                self,
                "Invalid Format",
                "Node name must be in AP## or AL## format\n(Examples: AP01, AL23, AP05m)"
            )
            return False
            
        tokens = [t.strip() for t in self.token_input.text().split(',') if t.strip()]
        selected_types = [t for t, btn in self.type_buttons.items() if btn.isChecked()]
        
        # Validate token requirements
        token_required_types = [t for t in selected_types if t in ("FBC", "RPC")]
        if token_required_types and not tokens:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                f"{', '.join(token_required_types)} log types require at least one token."
            )
            return False
            
        # Validate token format (3 digits)
        tokens_modified = False
        new_tokens = []
        
        for token in tokens:
            if token.isdigit() and len(token) > 3:
                # Auto-correct to last three digits
                corrected = token[-3:]
                new_tokens.append(corrected)
                tokens_modified = True
            elif token.isdigit() and len(token) == 3:
                new_tokens.append(token)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Token",
                    f"Token '{token}' must be a 3-digit number"
                )
                return False
                
        # Apply corrections if needed
        if tokens_modified:
            tokens = new_tokens  # Use the corrected tokens
            self.token_input.setText(', '.join(tokens))
            QMessageBox.information(
                self,
                "Token Formatted",
                "Token values auto-corrected to 3 digits"
            )
        
        # Update node data
        selected = self.node_list.currentRow()
        if selected >= 0 and selected < len(self.nodes_data):
            self.nodes_data[selected] = {
                "name": name,
                "tokens": tokens,
                "types": selected_types
            }
        
        self.populate_node_list()
        return True
            
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
    

