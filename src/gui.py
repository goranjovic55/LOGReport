import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox, QProgressBar,
    QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
from processor import LogProcessor
from generator import ReportGenerator

# Default styles for the application
DEFAULT_STYLES = {
    'content_font': 'Courier',
    'content_size': 10,
    'header_font': 'Helvetica',
    'space_between': 24  # points
}

class Worker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, input_dir, output_file, use_subdirs, format_type):
        super().__init__()
        self.input_dir = input_dir
        self.output_file = output_file
        self.use_subdirs = use_subdirs
        self.format_type = format_type
        self.processor = LogProcessor()
        self.generator = ReportGenerator()

    def process_logs(self, logs):
        """Simulate processing with progress updates"""
        for i, log in enumerate(logs):
            # Process each log (in a real app this would be actual processing)
            self.progress_updated.emit(int((i + 1) / len(logs) * 100))
            QThread.msleep(50)  # Simulate work

    def run(self):
        try:
            # Step 1: Get all log files
            logs = []
            for root, _, files in Path(self.input_dir).rglob('*') if self.use_subdirs \
                  else [(self.input_dir, [], files) for _ in [Path(self.input_dir).iterdir()]]:
                for file in files:
                    if file.suffix.lower() in ('.log', '.txt'):
                        logs.append(Path(root) / file)
            
            self.progress_updated.emit(10)  # Files found

            # Step 2: Process files with progress updates
            processed_data = []
            for i, filepath in enumerate(logs):
                processed_data.append(self.processor.process_file(filepath))
                self.progress_updated.emit(10 + int(i / len(logs) * 70))
            
            self.progress_updated.emit(80)  # Processing complete

            # Step 3: Generate output
            if self.format_type.lower() == 'pdf':
                self.generator.generate_pdf(processed_data, self.output_file)
            else:
                self.generator.generate_docx(processed_data, self.output_file)
            
            self.progress_updated.emit(100)
            self.finished.emit(self.output_file)

        except Exception as e:
            self.error_occurred.emit(str(e))

class LogReportGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("LOG Report Generator")
        self.setMinimumSize(600, 400)
        
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Folder selection
        folder_layout = QVBoxLayout()
        folder_layout.addWidget(QLabel("Select Log Folder:"))
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("color: #555; font-style: italic;")
        
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)
        
        # Format selection
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF (.pdf)", "Word (.docx)"])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        # Process button
        btn_process = QPushButton("Generate Report")
        btn_process.clicked.connect(self.process)
        btn_process.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px;"
        )
        layout.addWidget(btn_process)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
    def select_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select Log Folder")
        if folder:
            self.selected_path = Path(folder)
            self.folder_label.setText(f"Selected: {folder}")
            self.folder_label.setStyleSheet("color: #333; font-style: normal;")
            
    def process(self):
        """Process selected folder"""
        if not self.selected_path:
            QMessageBox.warning(self, "Error", "Please select a folder first")
            return
            
        try:
            output_path = f"report.{'pdf' if self.format_combo.currentIndex() == 0 else 'docx'}"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Report",
                str(self.selected_path.parent / output_path),
                "PDF Files (*.pdf);;Word Documents (*.docx)"
            )
            
            if not save_path:
                return
                
            self.progress.setValue(10)
            
            processor = LogProcessor()
            generator = ReportGenerator()
            
            logs = processor.process_directory(self.selected_path)
            self.progress.setValue(70)
            
            if save_path.endswith('.pdf'):
                generator.generate_pdf(logs, save_path)
            else:
                generator.generate_docx(logs, save_path)
                
            self.progress.setValue(100)
            QMessageBox.information(self, "Success", "Report generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")
        finally:
            self.progress.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = LogReportGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()