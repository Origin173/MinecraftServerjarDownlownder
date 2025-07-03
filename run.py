import sys
from src.main_app import MinecraftServerDownloaderApp
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinecraftServerDownloaderApp()
    window.show()
    sys.exit(app.exec_())
