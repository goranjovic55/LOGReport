from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class ContextMenuMixin:
    """Provides context menu helpers for CommanderWindow."""

    def generate_fieldbus_command(self, item_data):
        """Generates and sets the fieldbus structure command for FBC tokens."""
        token_id = item_data["token"]
        command_text = f"print from fieldbus io structure {token_id}0000"
        self.cmd_input.setPlainText(command_text)
        self.session_tabs.setCurrentWidget(self.telnet_tab)
        self.cmd_input.setFocus()
        self.status_bar.showMessage(
            f"Command set: {command_text} - Press Execute to run"
        )

    def determine_token_type(self, token_id):
        """Helper to determine token type based on token ID."""
        # For now, all log files are FBC - this can be extended later
        return "FBC"

    def show_context_menu(self, position):
        """Display context menu depending on item type."""
        item = self.node_tree.itemAt(position)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return
        token_type = data.get("token_type", "")
        token_id = data.get("token")
        if not token_id:
            return

        menu = QMenu(self.node_tree)
        if token_type == "FBC":
            action = QAction(
                f"Print FieldBus Structure (Token {token_id})", self
            )
            action.triggered.connect(
                lambda: self.process_fieldbus_command(token_id)
            )
            menu.addAction(action)
        elif token_type == "RPC":
            print_action = QAction(
                f"Print Rupi Counters (Token {token_id})", self
            )
            print_action.triggered.connect(
                lambda: self.process_rpc_command(token_id, "print")
            )
            clear_action = QAction(
                f"Clear Rupi Counters (Token {token_id})", self
            )
            clear_action.triggered.connect(
                lambda: self.process_rpc_command(token_id, "clear")
            )
            menu.addAction(print_action)
            menu.addAction(clear_action)
        menu.exec(self.node_tree.viewport().mapToGlobal(position))

    def process_fieldbus_command(self, token_id):
        """Prepare fieldbus command for execution."""
        command_text = f"print from fieldbus io structure {token_id}0000"
        self.cmd_input.setPlainText(command_text)
        self.session_tabs.setCurrentWidget(self.telnet_tab)
        self.cmd_input.setFocus()
        self.status_bar.showMessage(
            f"Command set: {command_text} - Press Execute to run", 3000
        )

    def process_rpc_command(self, token_id, action_type):
        """Prepare RPC command for execution."""
        if action_type == "print":
            command_text = f"print from rpc counters {token_id}0000"
        elif action_type == "clear":
            command_text = f"clear rpc counters {token_id}0000"
        else:
            return
        self.cmd_input.setPlainText(command_text)
        self.session_tabs.setCurrentWidget(self.telnet_tab)
        self.cmd_input.setFocus()
        action_name = "Print" if action_type == "print" else "Clear"
        self.status_bar.showMessage(
            f"{action_name} Rupi counters command set for token {token_id}", 3000
        )
