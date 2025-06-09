"""
Icon Generator
Creates placeholder icons for Commander UI
"""
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize

def create_node_icon(color: QColor) -> QIcon:
    """Creates a circular icon for nodes"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(0, 0, 15, 15)
    painter.end()
    
    return QIcon(pixmap)

def create_token_icon(color: QColor) -> QIcon:
    """Creates a square icon for tokens"""
    pixmap = QPixmap(12, 12)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRect(0, 0, 11, 11)
    painter.end()
    
    return QIcon(pixmap)

# Create icon instances
NODE_ONLINE_ICON = create_node_icon(QColor(50, 168, 82))      # Green
NODE_OFFLINE_ICON = create_node_icon(QColor(200, 200, 200))   # Gray
TOKEN_ICON = create_token_icon(QColor(88, 139, 139))          # CadetBlue
