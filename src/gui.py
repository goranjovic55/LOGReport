import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox, QSpinBox,
    QGroupBox, QStatusBar, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QStyleFactory
from processor import LogProcessor
from generator import ReportGenerator
from datetime import datetime

class Worker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, processor, folder, filters):
        super().__init__()
        self.processor = processor
        self.folder = folder
        self.filters = filters

    def run(self):
        try:
            result = self.processor.process_directory(self.folder)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class LogReportGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Apply system theme and fix styling
        self.setStyle(QStyleFactory.create('Fusion'))
        self._set_dark_theme()  # Or light theme if preferred
        self.processor = LogProcessor()
        self.generator = ReportGenerator()
        self.init_menu_bar()  # Initialize menu bar first
        self.init_ui()
        
    def init_menu_bar(self):
        menu_bar = self.menuBar()
        
        # Operations Menu
        operations_menu = menu_bar.addMenu("Operations")
        
        # Node Manager action
        manage_nodes_action = operations_menu.addAction("Node Manager")
        manage_nodes_action.triggered.connect(self.open_node_manager)
        
        # Command Center action
        commander_action = operations_menu.addAction("Command Center")
        commander_action.triggered.connect(self.open_commander)
        
    def _set_dark_theme(self):
        """Configure a nice dark theme"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197).lighter())
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        QApplication.instance().setPalette(dark_palette)

    def init_ui(self):
        # Main Window Setup
        self.setWindowTitle('LOGReport v1.0')
        self.setGeometry(300, 300, 800, 600)
        
        # Central Widget and Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create all UI components
        self._create_controls()
        self._create_statusbar()
        self._style_controls()
        self._setup_connections()
        
    def _create_controls(self):
        """Create all control widgets"""
        # Output Format Selection
        format_group = QGroupBox("Output Settings")
        format_layout = QHBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "DOCX"])
        format_layout.addWidget(QLabel("Output Format:"))
        format_layout.addWidget(self.format_combo)
        
        format_group.setLayout(format_layout)
        self.main_layout.addWidget(format_group)
        
        # Log Line Filtering
        self.filter_group = QGroupBox("Log Line Filtering")
        filter_layout = QHBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Show All", "First N Lines", "Last N Lines", "Range"])
        filter_layout.addWidget(self.filter_combo)
        
        # Line count control
        self.line_count = QSpinBox()
        self.line_count.setRange(1, 10000)
        self.line_count.setValue(50)
        self.line_count.setEnabled(False)
        
        # Range controls
        self.range_start = QSpinBox()
        self.range_end = QSpinBox()
        
        filter_layout.addWidget(QLabel("Lines:"))
        filter_layout.addWidget(self.line_count)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.range_start)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.range_end)
        
        self.filter_combo.currentTextChanged.connect(self._update_filter_controls)
        
        self.filter_group.setLayout(filter_layout)
        self.main_layout.addWidget(self.filter_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Select Log Folder")
        self.select_btn.clicked.connect(self._select_folder)
        
        self.process_btn = QPushButton("Generate Report")
        self.process_btn.clicked.connect(self._process_logs)

        self.generate_btn = QPushButton("Generate")
        btn_layout.addWidget(self.select_btn)
        btn_layout.addWidget(self.process_btn)
        btn_layout.addWidget(self.generate_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.main_layout.addWidget(self.progress)

    def _update_filter_controls(self, mode):
        """Update filter control visibility"""
        is_range = mode == "Range"
        is_limited = mode in ["First N Lines", "Last N Lines"]
        
        self.line_count.setEnabled(is_limited)
        self.range_start.setVisible(is_range)
        self.range_end.setVisible(is_range)
        
        for i in range(self.filter_group.layout().count()):
            widget = self.filter_group.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setVisible(
                    ("From" in widget.text() or "To" in widget.text()) 
                    if is_range 
                    else "Lines" in widget.text()
                )

    def _create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def open_node_manager(self):
        from gui_node_manager import NodeManager
        dialog = NodeManager(self)
        dialog.exec()
        
    def open_commander(self):
        from commander.commander_window import CommanderWindow
        self.commander = CommanderWindow()
        self.commander.show()
        
    def _style_controls(self):
        self.setStyleSheet("""
            QWidget {
                font family: Segoe UI;
                font-size: 10pt;
            }
            QMainWindow {
                background-color: #2D2D2D;
            }
            QGroupBox {
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
                color: white;
            }
            QPushButton {
                background-color: #3A3A3A;
                border: 1px solid #3E3E3E;
                padding: 5px 15px;
                min-width: 100px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QSpinBox, QComboBox {
                padding: 3px;
                background-color: #252525;
                color: white;
                border: 1px solid #3E3E3E;
            }
            QProgressBar {
                border: 1px solid #3E3E3E;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #5D3E8E;
            }
        """)

    def _select_folder(self):
        # Ensure dialog runs in main thread
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Log Folder",
            "",  # Start at default location
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
        )
        if folder:
            self.selected_folder = folder
            self.status_bar.showMessage(f"Selected: {folder}")

    def _get_filter_settings(self):
        mode = self.filter_combo.currentText()
        if mode == "Range":
            return {
                "mode": "range",
                "line_range": (self.range_start.value(), self.range_end.value())
            }
        elif mode != "Show All":
            return {
                "mode": mode.lower().split()[0],  # "first" or "last"
                "limit": self.line_count.value()
            }
        return {}

    def _process_logs(self):
        if not hasattr(self, 'selected_folder'):
            self.status_bar.showMessage("Error: No folder selected")
            return
            
        # Disable UI during processing
        self.setEnabled(False)
        self.status_bar.showMessage("Processing...")

        # Start processing thread
        self.worker = Worker(
            self.processor,
            self.selected_folder,
            self._get_filter_settings()
        )
        self.worker.finished.connect(self._on_processing_done)
        self.worker.error.connect(self._on_processing_error)
        self.worker.start()

    def _on_processing_done(self, logs):
        self.setEnabled(True)
        self.processed_logs = logs
        if logs:
            self.status_bar.showMessage("Processing complete")
        else:
            self.status_bar.showMessage("No valid log files found")

    def _on_processing_error(self, message):
        self.setEnabled(True)
        self.status_bar.showMessage(f"Error: {message}")

    def _setup_connections(self):
        """Ensure all signals are connected"""
        self.generate_btn.clicked.connect(self._on_generate)
        
    def _on_generate(self):
        """Handle generate button click"""
        if hasattr(self, 'processed_logs'):
            self._generate_report(self.processed_logs)
        else:
            self.status_bar.showMessage("No logs processed yet")

    def _generate_report(self, logs):
        """Handle full report generation flow"""
        if not logs:
            self.status_bar.showMessage("No logs to generate report")
            return False
            
        # 1. Get output format
        output_ext = self.format_combo.currentText().lower()
        
        # 2. Show save file dialog
        default_name = f"log_report_{datetime.now().strftime('%Y%m%d')}.{output_ext}"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report As",
            default_name,
            f"PDF (*.pdf);;Word (*.docx)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        
        if not save_path:
            return False  # User cancelled
            
        # 3. Get filtering parameters
        filter_mode = self.filter_combo.currentText().lower().split()[0]
        line_limit = self.line_count.value()
        range_start = self.range_start.value()
        range_end = self.range_end.value()

        # 4. Generate report (with progress feedback)
        self._show_progress(True, "Generating report...")
        
        try:
            if output_ext == "pdf":
                self.generator.generate_pdf(
                    logs,
                    save_path,
                    lines_mode=filter_mode,  # 'first', 'last', or 'range'
                    line_limit=line_limit,   # For first/last modes
                    range_start=range_start, # For range mode
                    range_end=range_end      # For range mode
                )
            else:
                self.generator.generate_docx(
                    logs,
                    save_path,
                    lines_mode=filter_mode,
                    line_limit=line_limit,
                    range_start=range_start,
                    range_end=range_end
                )
                
            self.status_bar.showMessage(f"Report saved to: {save_path}")
            return True
            
        except Exception as e:
            self.status_bar.showMessage(f"Generation failed: {str(e)}")
            return False
        finally:
            self._show_progress(False)

    def _show_progress(self, visible, message=""):
        """Toggle progress indicators"""
        self.progress.setVisible(visible)
        if visible:
            self.progress.setRange(0, 0)  # Indeterminate mode
            self.status_bar.showMessage(message)
        self.setEnabled(not visible)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogReportGUI()
    window.show()
    sys.exit(app.exec())