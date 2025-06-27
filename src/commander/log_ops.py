import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTextEdit, QTreeWidgetItem

class LogOperationsMixin:
    """Helpers for copying and clearing logs."""

    def copy_to_log(self):
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.status_bar.showMessage(
                "No item selected! Select a token or log file on the left."
            )
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.status_bar.showMessage("Selected item has no data")
            return
        tab_index = self.session_tabs.currentIndex()
        session_type = self.session_tabs.tabText(tab_index)
        if session_type == "Telnet":
            content = self.telnet_output.toPlainText()
        else:
            tab_widget = self.session_tabs.widget(tab_index)
            content_widget = tab_widget.layout().itemAt(0).widget()
            if isinstance(content_widget, QTextEdit):
                content = content_widget.toPlainText()
            else:
                return
        if not content:
            self.status_bar.showMessage("No content in current session")
            return
        if "log_path" in data:
            log_path = data["log_path"]
            with open(log_path, "a") as f:
                f.write(content + "\n")
            filename = os.path.basename(log_path)
            self.status_bar.showMessage(f"Content copied to {filename}")
        elif "token" in data:
            token_id = data["token"]
            node_name = data.get("node")
            token_type = data.get("token_type")
            if not node_name or not token_type:
                self.status_bar.showMessage(
                    "Token item missing node or token_type"
                )
                return
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_bar.showMessage(f"Node {node_name} not found")
                return
            ip = node.ip_address.replace(".", "-")
            filename = f"{node_name}_{ip}_{token_id}.{token_type.lower()}"
            self.log_writer.append_to_log(token_id, content, source=session_type)
            self.status_bar.showMessage(f"Content copied to {filename}")
        else:
            self.status_bar.showMessage("Unsupported item type")

    def clear_terminal(self):
        self.telnet_output.clear()
        self.status_bar.showMessage("Terminal cleared", 3000)

    def clear_node_log(self):
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.status_bar.showMessage(
                "No item selected! Select a log file on the left."
            )
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "log_path" not in data:
            self.status_bar.showMessage("Selected item is not a log file")
            return
        log_path = data["log_path"]
        try:
            with open(log_path, "w") as f:
                f.truncate(0)
            self.status_bar.showMessage(
                f"Cleared log: {os.path.basename(log_path)}", 3000
            )
        except Exception as e:
            self.status_bar.showMessage(f"Error clearing log: {e}")

    def open_log_file(self, item: QTreeWidgetItem, column: int):
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            if "log_path" in data:
                log_path = data["log_path"]
                try:
                    os.startfile(log_path)
                    self.status_bar.showMessage(
                        f"Opened log file: {os.path.basename(log_path)}"
                    )
                except Exception as e:
                    self.status_bar.showMessage(f"Error opening file: {e}")
                return True
        return False
