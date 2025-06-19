# Runtime hook for PyInstaller to handle Qt environment during build and runtime
import sys
import os

def configure_qt_environment():
    """Configure Qt environment variables"""
    # Disable unnecessary logging
    os.environ["QT_LOGGING_RULES"] = "qt.*=false;*.warning=false"
    
    # Avoid plugin warnings
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    
    # Handle high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

def initialize_qapplication():
    """Initialize minimal QApplication if needed"""
    if not hasattr(sys, 'frozen'):
        return
    
    try:
        from PyQt6 import QtWidgets
        
        # Check if QApplication already exists
        if QtWidgets.QApplication.instance() is None:
            # Create minimal QApplication without arguments
            app = QtWidgets.QApplication([])
            print("Created minimal QApplication instance for frozen environment")
    except ImportError:
        pass  # Qt not available, but not required in all contexts

# Always configure the environment
configure_qt_environment()

# For frozen builds, also initialize QApplication
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Configure environment for frozen build
    os.environ["QT_PLUGIN_PATH"] = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "plugins")
    os.environ["QML2_IMPORT_PATH"] = os.path.join(sys._MEIPASS, "PyQt6", "Qt6", "qml")
    
    # Initialize QApplication if needed
    try:
        initialize_qapplication()
    except Exception as e:
        print(f"Error initializing QApplication in frozen environment: {e}")
    else:
        print("Runtime hook successfully initialized Qt environment")
