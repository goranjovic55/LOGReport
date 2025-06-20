from PyQt6.QtCore import QThread, pyqtSignal


class Worker(QThread):
    """Background worker for processing directories."""
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
