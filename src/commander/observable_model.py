from PyQt6.QtCore import QObject, pyqtSignal

class ObservableModel(QObject):
    """
    Base class for observable models that emit change notifications.
    Provides standardized 'updated' signal for model changes.
    """
    updated = pyqtSignal()