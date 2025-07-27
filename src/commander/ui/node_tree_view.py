"""
Node Tree View Component
Stateless UI component for displaying nodes in a tree structure
"""
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class NodeTreeView(QWidget):
    """View component for the node tree UI"""
    
    # Signals for user interactions
    node_selected = pyqtSignal(object)  # QTreeWidgetItem
    node_double_clicked = pyqtSignal(object)  # QTreeWidgetItem
    context_menu_requested = pyqtSignal(object)  # QPoint
    load_nodes_clicked = pyqtSignal()
    set_log_root_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the node tree UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar with buttons
        toolbar_layout = QHBoxLayout()
        self.load_nodes_btn = QPushButton("Load Nodes")
        self.set_log_root_btn = QPushButton("Set Log Root")
        
        toolbar_layout.addWidget(self.load_nodes_btn)
        toolbar_layout.addWidget(self.set_log_root_btn)
        layout.addLayout(toolbar_layout)
        
        # Node Tree Widget
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Nodes"])
        self.node_tree.setColumnWidth(0, 300)
        self.node_tree.setFont(QFont("Consolas", 10))
        
        layout.addWidget(self.node_tree, 1)  # Add stretch factor
        
        # Connect signals
        self.load_nodes_btn.clicked.connect(self.load_nodes_clicked.emit)
        self.set_log_root_btn.clicked.connect(self.set_log_root_clicked.emit)
        self.node_tree.itemClicked.connect(self._on_item_clicked)
        self.node_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.node_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.node_tree.customContextMenuRequested.connect(self.context_menu_requested.emit)
        
    def _on_item_clicked(self, item, column):
        """Handle item click and emit signal"""
        self.node_selected.emit(item)
        
    def _on_item_double_clicked(self, item, column):
        """Handle item double click and emit signal"""
        self.node_double_clicked.emit(item)
        
    def clear(self):
        """Clear the node tree"""
        self.node_tree.clear()
        
    def add_top_level_item(self, item):
        """Add a top level item to the tree"""
        self.node_tree.addTopLevelItem(item)
        
    def set_status_message(self, message):
        """Set status message (for compatibility with existing code)"""
        # This is a placeholder to maintain compatibility
        pass
        
    # Proxy methods for QTreeWidget functionality
    def selectedItems(self):
        """Get selected items"""
        return self.node_tree.selectedItems()
        
    def currentItem(self):
        """Get current item"""
        return self.node_tree.currentItem()
        
    def setCurrentItem(self, item):
        """Set current item"""
        self.node_tree.setCurrentItem(item)
        
    def itemAt(self, position):
        """Get item at position"""
        return self.node_tree.itemAt(position)
        
    def viewport(self):
        """Get viewport"""
        return self.node_tree.viewport()