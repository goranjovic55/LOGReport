import sys
import os
import time
import logging
from src.commander.ui.commander_window import CommanderWindow
from PyQt6.QtWidgets import QApplication

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='commander_test.log',
    filemode='w'
)

def test_commander():
    app = QApplication(sys.argv)
    window = CommanderWindow()
    window.show()
    
    # Allow time for UI to initialize
    time.sleep(1)
    
    # Programmatically test node tree
    test_node_tree(window)
    
    # Programmatically test context menus
    test_context_menus(window)
    
    # Run the event loop for a while to process events
    QApplication.processEvents()
    time.sleep(3)
    
    # Exit the application
    sys.exit(app.exec())

def test_node_tree(window):
    """Test node tree population"""
    logging.debug("=== TESTING NODE TREE ===")
    
    # Simulate loading test configuration
    test_config = os.path.join(os.path.dirname(__file__), 'src', 'nodes_test.json')
    if os.path.exists(test_config):
        window.node_manager.set_config_path(test_config)
        window.node_manager.load_configuration()
        window.node_manager.scan_log_files()
        window.populate_node_tree()
        logging.debug("Loaded test configuration")
    else:
        logging.error(f"Test config not found: {test_config}")
    
    # Verify node tree has items
    top_level_count = window.node_tree.topLevelItemCount()
    logging.debug(f"Top-level items in node tree: {top_level_count}")
    if top_level_count > 0:
        logging.debug("Node tree population: SUCCESS")
    else:
        logging.error("Node tree population: FAILED")

def test_context_menus(window):
    """Test context menu actions"""
    logging.debug("=== TESTING CONTEXT MENUS ===")
    
    # Find the first FBC/RPC subsection
    for i in range(window.node_tree.topLevelItemCount()):
        node_item = window.node_tree.topLevelItem(i)
        for j in range(node_item.childCount()):
            section_item = node_item.child(j)
            if section_item.text(0) in ["FBC", "RPC"]:
                logging.debug(f"Found {section_item.text(0)} subsection in node {node_item.text(0)}")
                
                # Simulate right-click on subsection
                logging.debug(f"Triggering context menu for {section_item.text(0)}")
                window.show_context_menu(section_item.treeWidget().visualItemRect(section_item).center())
                
                # Simulate selecting "Print All Tokens" action
                if hasattr(window, 'process_all_fbc_subgroup_commands') and section_item.text(0) == "FBC":
                    window.process_all_fbc_subgroup_commands(section_item)
                    logging.debug("Triggered FBC subgroup commands")
                elif hasattr(window, 'process_all_rpc_subgroup_commands') and section_item.text(0) == "RPC":
                    window.process_all_rpc_subgroup_commands(section_item)
                    logging.debug("Triggered RPC subgroup commands")
                return
    
    logging.warning("No FBC/RPC subsections found for context menu test")

if __name__ == "__main__":
    test_commander()