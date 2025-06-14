import sys
from PyQt5.QtWidgets import QApplication, QLabel

def main():
    app = QApplication(sys.argv)
    label = QLabel("🎉 PyQt5 is working!")
    label.setWindowTitle("Test Window")
    label.resize(300, 100)
    label.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
