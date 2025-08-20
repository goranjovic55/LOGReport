import sys
import os
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to capture context menu service output
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("context_menu_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ContextMenuTest")

def _trigger_context_menu(main_window, ap01m_node, app):
    """Helper function to trigger context menu within event loop"""
    try:
        logger.info("=== Entering _trigger_context_menu function ===")
        # Simulate right-click on FBC subgroup (token 164)
        logger.debug(f"AP01m node has {len(ap01m_node.tokens)} tokens: {list(ap01m_node.tokens.keys())}")
        target_token = ap01m_node.tokens.get("164")
        
        if not target_token:
            logger.warning("Token 164 not found - using closest match")
            target_token = next((t for t in ap01m_node.tokens.values()
                                if t.token_type == "FBC"), None)
        
        if target_token:
            logger.info(f"Simulating right-click on FBC token: {target_token.token_id}")
            # Directly trigger context menu service
            logger.debug(f"Token details: ID={target_token.token_id}, Type={target_token.token_type}, Path={target_token.log_path}")
            logger.debug(f"Node details: Name={ap01m_node.name}, Tokens={len(ap01m_node.tokens)}")
            
            from src.commander.services.context_menu_service import ContextMenuService
            service = ContextMenuService(main_window)
            service.show_context_menu(
                node=ap01m_node,
                token=target_token,
                position=None,
                test_mode=True  # Enable test mode for additional logging
            )
            
            # Add verification of context menu actions
            logger.debug("Verifying context menu actions...")
            actions = service._create_context_menu(ap01m_node, target_token).actions()
            for i, action in enumerate(actions):
                logger.debug(f"Action {i}: {action.text()} | Enabled: {action.isEnabled()}")
            
            logger.info("Context menu service triggered successfully")
        else:
            logger.error("No FBC tokens available for AP01m")
            # Add more detailed error logging
            if ap01m_node and hasattr(ap01m_node, 'tokens'):
                logger.error(f"Available tokens: {list(ap01m_node.tokens.keys())}")
                for token_id, token in ap01m_node.tokens.items():
                    logger.error(f"Token {token_id}: type={token.token_type}")
            else:
                logger.error("AP01m node has no tokens attribute")
    except Exception as e:
        logger.exception(f"Error in _trigger_context_menu: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Clean exit after operation completes
        logger.debug("Quitting application")
        app.quit()

def run_test(app):
    """Set up and run the context menu simulation test within event loop"""
    try:
        # Add extremely early logging to verify function is called
        print("=== run_test function called ===")
        logger.debug("=== run_test function called ===")
        logger.info("=== Starting context menu simulation for AP01m FBC tokens ===")
        
        # Create main window within event loop where QApplication is fully initialized
        from src.commander.main_window import CommanderMainWindow
        main_window = CommanderMainWindow()
        main_window._load_settings()
        logger.debug("Main window created and settings loaded")
        
        # Set correct test-specific log directory path (relative to workspace root)
        main_window.log_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_logs'))
        logger.debug(f"Log directory set to: {main_window.log_directory}")
        
        # Verify log directory exists and contains files
        logger.debug(f"Log directory exists: {os.path.exists(main_window.log_directory)}")
        if os.path.exists(main_window.log_directory):
            logger.debug(f"Log directory contents: {os.listdir(main_window.log_directory)}")
        
        # Initialize node manager and scan logs
        from src.commander.node_manager import NodeManager
        node_manager = NodeManager()
        node_manager.log_directory = main_window.log_directory
        logger.debug("Scanning log files...")
        node_manager.scan_log_files()
        logger.debug(f"NodeManager initialized with {len(node_manager.nodes)} nodes")
        
        # Log all detected nodes and their tokens for verification
        logger.debug("=== Detected Nodes and Tokens ===")
        for node_name, node in node_manager.nodes.items():
            logger.debug(f"Node: {node_name} | Tokens: {len(node.tokens)}")
            for token_id, token in node.tokens.items():
                logger.debug(f"  Token: {token_id} | Type: {token.token_type} | Path: {token.log_path}")
        logger.debug("=== End of Node and Token Listing ===")
        
        # Find AP01m node and its FBC tokens
        ap01m_node = next((n for n in node_manager.nodes.values() if n.name == "AP01m"), None)
        if not ap01m_node:
            logger.error("AP01m node not found in node manager")
            # Log all available nodes for debugging
            logger.error(f"Available nodes: {list(node_manager.nodes.keys())}")
            for node_name, node in node_manager.nodes.items():
                logger.error(f"Node {node_name} has {len(node.tokens)} tokens")
            app.quit()
            return
        
        logger.info(f"Found AP01m node with {len(ap01m_node.tokens)} tokens")
        for token_id, token in ap01m_node.tokens.items():
            logger.debug(f"  Token: {token_id} | Type: {token.token_type} | Path: {token.log_path}")
        
        # Schedule context menu simulation to run within event loop
        from PyQt5.QtCore import QTimer
        logger.debug("Scheduling context menu simulation...")
        QTimer.singleShot(0, lambda: _trigger_context_menu(main_window, ap01m_node, app))
        logger.debug("Context menu simulation scheduled")
    except Exception as e:
        logger.exception(f"Error in run_test: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        app.quit()
    finally:
        # Add final cleanup logging
        logger.debug("run_test function completed")


if __name__ == "__main__":
    # CRITICAL: Create QApplication FIRST (before ANY Qt operations)
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    logger.debug("QApplication created")
    
    # Critical initialization sequence to ensure Qt is fully initialized
    app.processEvents()
    logger.debug("First processEvents() called")
    
    from PyQt5.QtCore import QThread
    QThread.msleep(500)  # Standard delay for QApplication initialization
    logger.debug("500ms sleep completed")
    
    app.processEvents()
    logger.debug("Second processEvents() called")
    
    # Verify QApplication is properly initialized
    if not QApplication.instance():
        logger.error("CRITICAL: QApplication instance not available after initialization!")
        sys.exit(1)
    
    # Schedule test execution within the event loop
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(0, lambda: run_test(app))
    logger.debug("Test scheduled with 0ms delay")
    
    # Start the event loop (required for proper Qt operation)
    logger.debug("Starting event loop")
    sys.exit(app.exec_())