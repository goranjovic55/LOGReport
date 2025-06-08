import sys
import os

# Suppress QFileSystemWatcher warnings
os.environ["QT_LOGGING_RULES"] = "qt.core.filesystemwatcher=false"

from gui import LogReportGUI
from PyQt6.QtWidgets import QApplication

def cli_main(input_path, output_file):
    from processor import LogProcessor
    from generator import ReportGenerator
    
    print(f"Starting LOGReport processing")
    logs = LogProcessor().process_directory(input_path)
    ReportGenerator().generate_report(logs, output_file)
    print(f"Successfully created: {output_file}")

if __name__ == "__main__":
    # Default to GUI mode with no arguments or with --gui flag
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "--gui"):
        app = QApplication(sys.argv)
        window = LogReportGUI()
        window.show()
        sys.exit(app.exec())
    elif len(sys.argv) == 3:
        cli_main(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  GUI Mode: python main.py [--gui]  (--gui optional for GUI mode)")
        print("  CLI Mode: python main.py <input_dir> <output.pdf>")
        sys.exit(1)