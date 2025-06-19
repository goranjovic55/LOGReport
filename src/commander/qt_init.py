"""Centralized Qt initialization and configuration"""
import os
import sys

def initialize_qt():
    """Initialize Qt application instance and set up environment"""
    # Set up Qt environment variables
    os.environ["QT_LOGGING_RULES"] = "qt.core.filesystemwatcher=false"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"  # Default to windows platform
    
    # Only create application if required
    if "--cli" in sys.argv or not have_gui():
        # Command-line mode or headless environment
        os.environ["QT_QPA_PLATFORM"] = "minimal"
        return None
    
    # Create QApplication if it doesn't exist
    try:
        from PyQt6.QtWidgets import QApplication
        if QApplication.instance() is None:
            return QApplication(sys.argv)
    except ImportError:
        pass
    return None

def have_gui():
    """Check if we're in a GUI-capable environment"""
    # For build environments like PyInstaller that set _MEIPASS
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
        return False
    # Running without DISPLAY on Linux/macOS
    if sys.platform != "win32" and not os.environ.get('DISPLAY'):
        return False
    return True  # Default to GUI available