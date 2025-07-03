import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QProgressBar, QGroupBox, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QIcon
from src.downloader import (
    BMCLAPIDownloader,
    DownloaderSignals,
    DataLoaderWorker,
    ServerTypeLoaderWorker,
    CoreVersionLoaderWorker,
    DownloadWorker
)

class MinecraftServerDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft 服务端核心下载器")
        self.setFixedSize(650, 600)

        # 设置窗口图标 (确保 resources/icon.ico 或 icon.png 存在)
        icon_path_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'icon.ico')
        icon_path_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'icon.png')
        icon_path_svg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'icon.svg')

        if os.path.exists(icon_path_ico):
            self.setWindowIcon(QIcon(icon_path_ico))
        elif os.path.exists(icon_path_png):
            self.setWindowIcon(QIcon(icon_path_png))
        elif os.path.exists(icon_path_svg):
            self.setWindowIcon(QIcon(icon_path_svg))

        # 初始化下载器逻辑类和信号
        self.downloader = BMCLAPIDownloader()
        self.signals = DownloaderSignals()

        # 连接信号与槽
        self.signals.log_message.connect(self.log)
        self.signals.progress_update.connect(self.update_progress)
        self.signals.download_finished.connect(self.on_download_finished)
        self.downloader.signals = self.signals 

        # 初始化线程和工作者引用为 None
        self.download_thread = None
        self.download_worker = None

        self.data_loader_thread = None
        self.data_loader_worker = None

        self.server_type_loader_thread = None
        self.server_type_loader_worker = None

        self.core_version_loader_thread = None
        self.core_version_loader_worker = None

        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- 选择选项区域 ---
        options_group = QGroupBox("选择下载选项")
        options_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        # Minecraft 版本选择
        mc_version_layout = QHBoxLayout()
        mc_version_layout.addWidget(QLabel("Minecraft 版本:"))
        self.mc_version_combo = QComboBox()
        self.mc_version_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # 连接信号，避免在加载数据时触发
        self.mc_version_combo.currentIndexChanged.connect(self.on_mc_version_selected)
        mc_version_layout.addWidget(self.mc_version_combo)
        options_layout.addLayout(mc_version_layout)

        # 核心类型选择
        server_type_layout = QHBoxLayout()
        server_type_layout.addWidget(QLabel("核心类型:"))
        self.server_type_combo = QComboBox()
        self.server_type_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.server_type_combo.currentIndexChanged.connect(self.on_server_type_selected)
        server_type_layout.addWidget(self.server_type_combo)
        options_layout.addLayout(server_type_layout)

        # 核心版本选择
        core_version_layout = QHBoxLayout()
        core_version_layout.addWidget(QLabel("核心版本:"))
        self.core_version_combo = QComboBox()
        self.core_version_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        core_version_layout.addWidget(self.core_version_combo)
        options_layout.addLayout(core_version_layout)

        # 下载按钮
        self.download_button = QPushButton("下载服务端核心")
        self.download_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.download_button.setFixedHeight(40)
        self.download_button.clicked.connect(self.start_download_process)
        options_layout.addWidget(self.download_button, alignment=Qt.AlignCenter)

        main_layout.addWidget(options_group)

        # --- 状态与进度区域 ---
        status_group = QGroupBox("状态与进度")
        status_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)
        status_layout.addWidget(self.progress_bar)

        # 日志输出区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        status_layout.addWidget(self.log_text)

        main_layout.addWidget(status_group)
        main_layout.setStretchFactor(status_group, 1)

        self.setLayout(main_layout)

    def log(self, message):
        """将消息添加到日志文本区域"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def _stop_and_cleanup_thread(self, thread_attr_name, worker_attr_name):
        """
        通用函数，用于停止线程并清理 worker。
        此函数主要用于在应用程序关闭时强制停止线程，或在启动新任务前停止旧任务。
        对于正常完成的线程，应通过信号和deleteLater()进行清理。
        """
        thread_ref = getattr(self, thread_attr_name, None)
        worker_ref = getattr(self, worker_attr_name, None)

        if thread_ref is not None: 
            try:
                # 尝试检查线程是否在运行。如果C++对象已被删除，这里会引发RuntimeError
                if thread_ref.isRunning():
                    self.signals.log_message.emit(f"正在停止现有线程: {thread_attr_name}...")
                    thread_ref.quit()
                    thread_ref.wait(2000) 
                    if thread_ref.isRunning():
                        self.signals.log_message.emit(f"线程 {thread_attr_name} 未在规定时间内结束，可能需要强制终止。")
                        thread_ref.terminate() 
                        thread_ref.wait(1000) 
            except RuntimeError as e:
                # 捕获并记录RuntimeError，这意味着底层C++对象可能已被删除
                self.signals.log_message.emit(f"清理线程 {thread_attr_name} 时发生运行时错误 (可能对象已删除): {e}")
            finally:
                # 无论是否发生错误，最终都将Python引用清除，以防止悬空引用
                if hasattr(self, worker_attr_name):
                    setattr(self, worker_attr_name, None)
                if hasattr(self, thread_attr_name):
                    setattr(self, thread_attr_name, None)
        else:
            if hasattr(self, worker_attr_name):
                setattr(self, worker_attr_name, None)
                

    def load_initial_data(self):
        """在单独线程中加载初始数据（Minecraft 版本列表）"""
        self.signals.log_message.emit("正在加载初始数据...")
        self.set_ui_enabled(False) 

        # 停止并清理旧的加载线程（如果存在）
        self._stop_and_cleanup_thread('data_loader_thread', 'data_loader_worker')

        self.data_loader_thread = QThread()
        self.data_loader_worker = DataLoaderWorker(self.downloader)
        self.data_loader_worker.moveToThread(self.data_loader_thread)

        self.data_loader_worker.data_loaded.connect(self.on_initial_data_loaded)
        self.data_loader_thread.started.connect(self.data_loader_worker.run)

        self.data_loader_thread.start()

    def on_initial_data_loaded(self, mc_versions):
        """初始数据加载完成后更新UI"""
        # 断开连接，防止在 clear() 或 addItems() 时再次触发 on_mc_version_selected
        self.mc_version_combo.currentIndexChanged.disconnect(self.on_mc_version_selected)

        self.mc_version_combo.clear()
        self.mc_version_combo.addItems(mc_versions)
        if mc_versions:
            self.mc_version_combo.setCurrentIndex(0)
        else:
            self.signals.log_message.emit("未能加载 Minecraft 版本列表，请检查网络连接或稍后重试。")

        self.mc_version_combo.currentIndexChanged.connect(self.on_mc_version_selected)
        self.signals.log_message.emit("初始数据加载完成。")
        self.set_ui_enabled(True) 
        # 自动触发选择第一个版本，加载核心类型
        if mc_versions:
            self.on_mc_version_selected()

    def on_mc_version_selected(self):
        """当 Minecraft 版本选择改变时触发"""
        selected_mc_version = self.mc_version_combo.currentText()
        if not selected_mc_version:
            self.server_type_combo.clear()
            self.core_version_combo.clear()
            return

        self.signals.log_message.emit(f"你选择了 Minecraft 版本: {selected_mc_version}")
        self.set_ui_enabled(False, exclude_mc_version=True) 

        # 停止并清理旧的服务端类型加载线程
        self._stop_and_cleanup_thread('server_type_loader_thread', 'server_type_loader_worker')

        self.server_type_loader_thread = QThread()
        self.server_type_loader_worker = ServerTypeLoaderWorker(self.downloader, selected_mc_version)
        self.server_type_loader_worker.moveToThread(self.server_type_loader_thread)

        self.server_type_loader_worker.server_types_loaded.connect(self.on_server_types_loaded)
        self.server_type_loader_thread.started.connect(self.server_type_loader_worker.run)

        self.server_type_loader_thread.start()

    def on_server_types_loaded(self, server_types):
        """核心类型加载完成后更新UI"""
        # 断开连接
        self.server_type_combo.currentIndexChanged.disconnect(self.on_server_type_selected)

        self.server_type_combo.clear()
        self.server_type_combo.addItems([s.capitalize() for s in server_types])
        if server_types:
            self.server_type_combo.setCurrentIndex(0)
        else:
            self.signals.log_message.emit("未能找到支持的核心类型。")
            self.core_version_combo.clear() 

        # 重新连接
        self.server_type_combo.currentIndexChanged.connect(self.on_server_type_selected)
        self.set_ui_enabled(True) 
        self._stop_and_cleanup_thread('server_type_loader_thread', 'server_type_loader_worker')
        # 自动触发选择第一个核心类型，加载核心版本
        if server_types:
            self.on_server_type_selected()

    def on_server_type_selected(self):
        """当服务端核心类型选择改变时触发"""
        selected_mc_version = self.mc_version_combo.currentText()
        selected_server_type = self.server_type_combo.currentText().lower()

        if not selected_mc_version or not selected_server_type: 
            self.core_version_combo.clear()
            return

        self.signals.log_message.emit(f"你选择了服务端核心类型: {selected_server_type.capitalize()}")
        self.set_ui_enabled(False, exclude_mc_version=True, exclude_server_type=True) 
        # 停止并清理旧的核心版本加载线程
        self._stop_and_cleanup_thread('core_version_loader_thread', 'core_version_loader_worker')

        self.core_version_loader_thread = QThread()
        self.core_version_loader_worker = CoreVersionLoaderWorker(self.downloader, selected_mc_version, selected_server_type)
        self.core_version_loader_worker.moveToThread(self.core_version_loader_thread)

        self.core_version_loader_worker.core_versions_loaded.connect(self.on_core_versions_loaded)
        self.core_version_loader_thread.started.connect(self.core_version_loader_worker.run)

        self.core_version_loader_thread.start()

    def on_core_versions_loaded(self, core_versions):
        """核心版本加载完成后更新UI"""
        self.core_version_combo.clear()
        self.core_version_combo.addItems(core_versions)
        if core_versions:
            self.core_version_combo.setCurrentIndex(0)
        else:
            self.signals.log_message.emit("未能找到核心版本。")
        self.set_ui_enabled(True) 
        self._stop_and_cleanup_thread('core_version_loader_thread', 'core_version_loader_worker')
        # 自动选中第一个核心版本

    def start_download_process(self):
        """开始下载按钮的槽函数"""
        selected_mc_version = self.mc_version_combo.currentText()
        selected_server_type = self.server_type_combo.currentText().lower()
        selected_core_version_info = self.core_version_combo.currentText()

        if not selected_mc_version or not selected_server_type or not selected_core_version_info:
            QMessageBox.warning(self, "输入错误", "请完整选择 Minecraft 版本、核心类型和核心版本。")
            return

        # 禁用所有UI元素，避免下载过程中用户再次操作
        self.set_ui_enabled(False)
        self.progress_bar.setValue(0) 

        download_link, file_name = self.downloader.get_download_url_and_filename(
            selected_mc_version, selected_server_type, selected_core_version_info
        )

        if not download_link:
            self.signals.log_message.emit("未能获取到下载链接，请检查你的选择或稍后重试。")
            QMessageBox.critical(self, "获取链接失败", "未能获取到下载链接，请检查你的选择或稍后重试。")
            self.set_ui_enabled(True) 

        download_dir = "server_cores"
        os.makedirs(download_dir, exist_ok=True)
        file_path = os.path.join(download_dir, file_name)

        # 在新线程中启动下载
        self._stop_and_cleanup_thread('download_thread', 'download_worker')

        self.download_thread = QThread()
        self.download_worker = DownloadWorker(self.downloader, download_link, file_path)
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.download_thread.quit) 
        # 连接 deleteLater 到工作者的 finished 信号，使其在自己的线程中被删除
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater) 
        
        self.download_thread.start()

    def on_download_finished(self, file_path, success):
        """下载完成后的处理槽函数"""
        self.progress_bar.setValue(0) 
        self.set_ui_enabled(True) 

        if success:
            QMessageBox.information(self, "下载完成", f"服务端核心下载成功！\n文件位置: {file_path}")
        else:
            QMessageBox.critical(self, "下载失败", "服务端核心下载失败，请查看日志信息。")



    def set_ui_enabled(self, enabled, exclude_mc_version=False, exclude_server_type=False):
        """统一控制UI元素的启用/禁用状态"""
        if not exclude_mc_version:
            self.mc_version_combo.setEnabled(enabled)
        if not exclude_server_type:
            self.server_type_combo.setEnabled(enabled)
        self.core_version_combo.setEnabled(enabled)
        self.download_button.setEnabled(enabled)

    def closeEvent(self, event):
        """在窗口关闭时，确保所有线程都被安全停止"""
        self.signals.log_message.emit("应用程序即将关闭，正在清理后台任务...")

        # 通过字符串名称停止所有正在运行的线程
        self._stop_and_cleanup_thread('data_loader_thread', 'data_loader_worker')
        self._stop_and_cleanup_thread('server_type_loader_thread', 'server_type_loader_worker')
        self._stop_and_cleanup_thread('core_version_loader_thread', 'core_version_loader_worker')
        self._stop_and_cleanup_thread('download_thread', 'download_worker')

        super().closeEvent(event)