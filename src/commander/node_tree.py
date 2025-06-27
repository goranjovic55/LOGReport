from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QIcon
import os
import glob

from .icons import get_node_online_icon, get_node_offline_icon, get_token_icon
from .widgets import ConnectionState

class NodeTreeMixin:
    """Mix-in providing node tree population and selection logic."""

    def populate_node_tree(self):
        """Populate tree view with nodes and log files."""
        self.node_tree.clear()
        for node in self.node_manager.get_all_nodes():
            node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
            node_item.setIcon(0, get_node_online_icon() if node.status == "online" else get_node_offline_icon())

            log_root = self.node_manager.log_root
            if not log_root or not os.path.isdir(log_root):
                no_folder = QTreeWidgetItem(["Please set log root folder"])
                no_folder.setIcon(0, QIcon(":/icons/warning.png"))
                node_item.addChild(no_folder)
                self.node_tree.addTopLevelItem(node_item)
                continue

            sections = {
                "FBC": QTreeWidgetItem(["FBC"]),
                "RPC": QTreeWidgetItem(["RPC"]),
                "LOG": QTreeWidgetItem(["LOG"]),
                "LIS": QTreeWidgetItem(["LIS"]),
            }
            sections["FBC"].setIcon(0, get_token_icon())
            sections["RPC"].setIcon(0, get_token_icon())
            sections["LOG"].setIcon(0, QIcon(":/icons/page.png"))
            sections["LIS"].setIcon(0, QIcon(":/icons/page.png"))

            added_log = False
            log_dir = os.path.join(log_root, "LOG")
            pattern = f"{node.name}_{node.ip_address.replace('.', '-')}.log"
            for log_path in glob.glob(os.path.join(log_dir, pattern)):
                if os.path.isfile(log_path):
                    log_item = QTreeWidgetItem([f"📝 {os.path.basename(log_path)}"])
                    log_item.setData(0, Qt.ItemDataRole.UserRole, {"log_path": log_path})
                    log_item.setIcon(0, QIcon(":/icons/page.png"))
                    sections["LOG"].addChild(log_item)
                    added_log = True

            added_fbc = False
            fbc_dir = os.path.join(log_root, "FBC", node.name)
            if os.path.isdir(fbc_dir):
                for filename in os.listdir(fbc_dir):
                    if filename.lower().endswith((".fbc", ".log", ".txt")) and filename.startswith(node.name + "_"):
                        file_path = os.path.join(fbc_dir, filename)
                        if os.path.isfile(file_path):
                            token_id = filename.split("_")[-1].split(".")[0]
                            item = QTreeWidgetItem([f"📝 {filename}"])
                            item.setData(0, Qt.ItemDataRole.UserRole, {
                                "log_path": file_path,
                                "token": token_id,
                                "token_type": "FBC",
                                "node": node.name,
                            })
                            item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["FBC"].addChild(item)
                            added_fbc = True

            added_rpc = False
            rpc_dir = os.path.join(log_root, "RPC", node.name)
            if os.path.isdir(rpc_dir):
                for filename in os.listdir(rpc_dir):
                    if filename.lower().endswith((".rpc", ".log", ".txt")) and filename.startswith(node.name + "_"):
                        file_path = os.path.join(rpc_dir, filename)
                        if os.path.isfile(file_path):
                            token_id = filename.rsplit('_', 1)[-1].split('.')[0]
                            item = QTreeWidgetItem([f"📝 {filename}"])
                            item.setData(0, Qt.ItemDataRole.UserRole, {
                                "log_path": file_path,
                                "node": node.name,
                                "token": token_id,
                                "token_type": "RPC",
                            })
                            item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["RPC"].addChild(item)
                            added_rpc = True

            added_lis = False
            lis_dir = os.path.join(log_root, "LIS", node.name)
            if os.path.isdir(lis_dir):
                for filename in os.listdir(lis_dir):
                    if filename.endswith(".lis") and filename.startswith(node.name + "_"):
                        file_path = os.path.join(lis_dir, filename)
                        if os.path.isfile(file_path):
                            item = QTreeWidgetItem([f"📝 {filename}"])
                            item.setData(0, Qt.ItemDataRole.UserRole, {"log_path": file_path})
                            item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["LIS"].addChild(item)
                            added_lis = True

            if added_fbc:
                node_item.addChild(sections["FBC"])
            if added_rpc:
                node_item.addChild(sections["RPC"])
                node_item.addChild(sections["LOG"])
            if added_lis:
                node_item.addChild(sections["LIS"])

            if not (added_fbc or added_rpc or added_log or added_lis):
                no_files = QTreeWidgetItem(["No files found for this node"])
                no_files.setIcon(0, QIcon(":/icons/warning.png"))
                node_item.addChild(no_files)

            self.node_tree.addTopLevelItem(node_item)

        self.node_tree.expandAll()

    def on_node_selected(self, item: QTreeWidgetItem, column: int):
        """Handle node/token selection."""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            token_id = data.get("token")
            node_name = data.get("node")
            if node_name and token_id:
                token = self.node_manager.get_token(node_name, token_id)
                if not token:
                    return
                self.current_token = token
                if token.token_type == "FBC":
                    self.session_tabs.setCurrentWidget(self.telnet_tab)
                    self.telnet_connection_bar.ip_edit.setText(token.ip_address)
                    self.telnet_connection_bar.port_edit.setText(str(token.port))
                    self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token.token_type == "VNC":
                    self.session_tabs.setCurrentWidget(self.vnc_tab)
                    if hasattr(self, 'vnc_connection_bar'):
                        self.vnc_connection_bar.ip_edit.setText(token.ip_address)
                        self.vnc_connection_bar.port_edit.setText(str(token.port))
                        self.vnc_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token.token_type == "FTP":
                    self.session_tabs.setCurrentWidget(self.ftp_tab)
                    if hasattr(self, 'ftp_connection_bar'):
                        self.ftp_connection_bar.ip_edit.setText(token.ip_address)
                        self.ftp_connection_bar.port_edit.setText(str(token.port))
                        self.ftp_connection_bar.update_status(ConnectionState.DISCONNECTED)

                try:
                    log_path = self.log_writer.open_log(node_name, token_id, token.token_type)
                    self.status_bar.showMessage(f"Log ready: {os.path.basename(log_path)}")
                except OSError as e:
                    self.status_bar.showMessage(f"Error opening log: {e}")

