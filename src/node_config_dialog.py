import sys
import os
import json
import tempfile
import re
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QGroupBox, QRadioButton, QPushButton, QLineEdit,
    QLabel, QFormLayout, QMessageBox, QButtonGroup,
    QFileDialog, QInputDialog, QCheckBox
)
from PyQt6.QtCore import Qt

class NodeConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node Configuration")
        self.setMinimumSize(1000, 450)
        # Initialize config_file with absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(script_dir, "..", "nodes.json")
        self.nodes_data = []
        
        # Try to load the configuration from default location
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.nodes_data = json.load(f)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Loading Configuration",
                    f"Could not load configuration: {str(e)}\n\nStarting with empty configuration."
                )
        else:
            # If no file exists, create a default one
            self.nodes_data = [
                {"name": "AP00", "tokens": ["001", "002"], "types": ["FBC"], "ip": "192.168.0.1"}
            ]
            # Save the default configuration to nodes.json
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(self.nodes_data, f, indent=4)
            except:
                pass
        
        # Initialize UI and populate node list
        self.init_ui()
        self.populate_node_list()
            
    def save_config(self):
        """Save configuration to a user-selected JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            self.config_file or os.path.expanduser("~"),
            "JSON Files (*.json)"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                json.dump(self.nodes_data, f, indent=4)
            QMessageBox.information(
                self,
                "Success",
                f"Configuration saved to:\n{file_path}"
            )
            self.config_file = file_path  # Update to use the new path
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save configuration: {str(e)}"
            )
            
    def load_configuration(self):
        """Load a configuration from a user-selected JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration File",
            os.path.expanduser("~"),  # Start in home directory
            "JSON Files (*.json)"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                self.nodes_data = json.load(f)
            
            self.populate_node_list()
            
            # Auto-select first node to populate fields
            if self.nodes_data:
                self.node_list.setCurrentRow(0)
                
            QMessageBox.information(
                self,
                "Success",
                f"Configuration loaded from:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load configuration: {str(e)}"
            )
            
    def populate_node_list(self):
        """Populate node list widget with node names"""
        self.node_list.clear()
        for node in self.nodes_data:
            name = node.get('name', 'Unnamed node')
            self.node_list.addItem(name)
            
    def on_node_selected(self):
        """Called when user selects a node from the list"""
        selected = self.node_list.currentRow()
        if 0 <= selected < len(self.nodes_data):
            node_data = self.nodes_data[selected]
            self.name_input.setText(node_data.get('name', ''))
            self.token_input.setText(', '.join(node_data.get('tokens', [])))
            self.ip_input.setText(node_data.get('ip', ''))
            
            # Set types
            for btn in self.type_buttons.values():
                btn.setChecked(False)
            for log_type in node_data.get('types', []):
                if log_type in self.type_buttons:
                    self.type_buttons[log_type].setChecked(True)
            
            self.generate_examples()
        else:
            self.name_input.setText("")
            self.token_input.setText("")
            self.ip_input.setText("")
            for btn in self.type_buttons.values():
                btn.setChecked(False)
            self.generate_examples()
            
    def add_node(self):
        """Add new node to the configuration"""
        self.nodes_data.append({
            "name": "",
            "tokens": [],
            "types": [],
            "ip": ""
        })
        self.populate_node_list()
        self.node_list.setCurrentRow(len(self.nodes_data) - 1)
        
    def remove_node(self):
        """Remove selected node from configuration"""
        selected = self.node_list.currentRow()
        if 0 <= selected < len(self.nodes_data):
            del self.nodes_data[selected]
            self.populate_node_list()
            # Select the next item or clear fields
            if selected < len(self.nodes_data):
                self.node_list.setCurrentRow(selected)
            else:
                self.on_node_selected()  # This will clear fields
        
        self.init_ui()
        self.populate_node_list()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Left: Node list
        left_group = QGroupBox("Nodes")
        left_layout = QVBoxLayout()
        self.node_list = QListWidget()
        self.node_list.itemSelectionChanged.connect(self.on_node_selected)
        
        # Node buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Node")
        self.add_btn.clicked.connect(self.add_node)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_node)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        
        left_layout.addWidget(self.node_list)
        left_layout.addLayout(btn_layout)
        left_group.setLayout(left_layout)
        
        # Right: Configuration pane
        right_group = QGroupBox("Node Configuration")
        right_layout = QVBoxLayout()
        
        # Node details form
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("AP## format")
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Comma separated 3-digit numbers")
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.0.1")
        
        form_layout.addRow(QLabel("Node Name:"), self.name_input)
        form_layout.addRow(QLabel("Tokens (comma-sep):"), self.token_input)
        form_layout.addRow(QLabel("IP Address:"), self.ip_input)
        
        # Log type selection (multiple checkboxes) including new LIS type
        log_types = ["FBC", "RPC", "LOG", "LIS"]
        self.type_buttons = {}
        controls_layout = QHBoxLayout()
        
        for log_type in log_types:
            checkbox = QCheckBox(log_type)
            self.type_buttons[log_type] = checkbox
            controls_layout.addWidget(checkbox)
        
        form_layout.addRow(QLabel("Log Types:"), controls_layout)
        right_layout.addLayout(form_layout)
        
        # Example files display
        example_group = QGroupBox("Example Files")
        example_layout = QVBoxLayout()
        self.example_label = QLabel("No examples generated yet")
        example_layout.addWidget(self.example_label)
        example_group.setLayout(example_layout)
        right_layout.addWidget(example_group)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Configuration")
        self.load_btn.setMinimumWidth(180)
        self.load_btn.clicked.connect(self.load_configuration)
        btn_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Save to JSON")
        self.save_btn.setMinimumWidth(180)
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)
        
        self.create_files_btn = QPushButton("Create Files/Folders")
        self.create_files_btn.setMinimumWidth(220)
        self.create_files_btn.clicked.connect(self.create_files)
        btn_layout.addWidget(self.create_files_btn)
        
        right_layout.addLayout(btn_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        right_layout.addWidget(close_btn)
        
        right_group.setLayout(right_layout)
        
        # Add left and right sections to main layout
        main_layout.addWidget(left_group, 35)
        main_layout.addWidget(right_group, 65)
        self.setLayout(main_layout)
        
        # Set up change handlers
        self.name_input.textChanged.connect(self.generate_examples)
        self.token_input.textChanged.connect(self.generate_examples)
        self.ip_input.textChanged.connect(self.generate_examples)
        for checkbox in self.type_buttons.values():
            checkbox.stateChanged.connect(self.generate_examples)
            
    def apply_current_changes(self):
        """Apply UI changes to the current node in nodes_data"""
        selected = self.node_list.currentRow()
        if 0 <= selected < len(self.nodes_data):
            name = self.name_input.text().strip()
            ip = self.ip_input.text().strip()
            tokens = [t.strip() for t in self.token_input.text().split(',') if t.strip()]
            selected_types = [t for t, btn in self.type_buttons.items() if btn.isChecked()]
            
            # Update current node in node_data
            self.nodes_data[selected] = {
                "name": name,
                "ip": ip,
                "tokens": tokens,
                "types": selected_types
            }
            
    def generate_examples(self):
        """Generate examples and optionally save current changes if node selected"""
        selected = self.node_list.currentRow()
        if selected >= 0 and selected < len(self.nodes_data):
            try:
                # Update current node first
                self.apply_current_changes()
                
                # Get from node_data instead of UI to ensure consistency
                node = self.nodes_data[selected]
                name = node.get('name') or "APXX"
                ip = node.get('ip', '').replace('.', '-') or "192-168-0-1"
                tokens = node.get('tokens', [])
                selected_types = node.get('types', [])
                
                # Generate examples including the new LIS type
                examples = []
                for log_type in selected_types:
                    if log_type == "FBC":
                        examples.extend([f"{name}_{ip}_{token}.fbc" for token in tokens])
                    elif log_type == "RPC":
                        examples.extend([f"{name}_{ip}_{token}.rpc" for token in tokens])
                    elif log_type == "LOG":
                        examples.append(f"{name}_{ip}.log")
                    elif log_type == "LIS":
                        # Generate LIS filenames including IP address as specified
                        examples.extend([f"{name}_{ip}_exe{i}_5irb_5orb.lis" for i in range(1, 7)])
                
                self.example_label.setText("Example files:\n" + "\n".join(examples) if examples else "No examples")
            except Exception as e:
                self.example_label.setText(f"Couldn't generate examples: {str(e)}")
        else:
            self.example_label.setText("No examples generated yet")
            
    def create_files(self):
        """Create files and folders based on current configuration"""
        from log_creator import LogCreator
        from PyQt6.QtWidgets import QFileDialog
        
        # Validate configuration first
        errors = []
        for i, node in enumerate(self.nodes_data):
            if not node.get('name'):
                errors.append(f"Node {i+1} has no name")
            if not node.get('types'):
                errors.append(f"Node {node.get('name', str(i+1))} has no log types selected")
            elif any(lt in ['FBC', 'RPC'] for lt in node['types']):
                if not node.get('tokens'):
                    errors.append(f"Node {node.get('name', str(i+1))} requires tokens for FBC/RPC logs")
        
        if errors:
            QMessageBox.critical(
                self,
                "Configuration Error",
                "Cannot create files:\n" + "\n".join(errors[:3])
            )
            return
        
        # Ask user for output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.abspath(os.path.expanduser("~")),  # Start at user's home directory
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        )
        if not output_dir:
            return  # User cancelled
            
        try:
            # Define a simple content template for the files
            content_template = """This is a log file for $FILENAME.
Generated on $DATETIME."""
            
            LogCreator.create_file_structure(output_dir, self.nodes_data, content_template)
                
            QMessageBox.information(
                self,
                "Success",
                f"Sample files created in:\n{output_dir}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "File Creation Failed",
                f"Error creating files: {str(e)}"
            )