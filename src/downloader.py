import requests
import os
import json
from PyQt5.QtCore import pyqtSignal, QObject
import re 
from bs4 import BeautifulSoup

class DownloaderSignals(QObject):
    """
    定义用于与主UI线程通信的信号。
    """
    log_message = pyqtSignal(str)          # 发送日志消息
    progress_update = pyqtSignal(int)      # 更新下载进度 (0-100)
    download_finished = pyqtSignal(str, bool) # 下载完成信号 (文件路径, 是否成功)
    data_loaded = pyqtSignal(list)         # 数据加载完成信号 (例如，版本列表)
    server_types_loaded = pyqtSignal(list) # 服务端类型加载完成信号
    core_versions_loaded = pyqtSignal(list) # 核心版本加载完成信号

class BMCLAPIDownloader:
    BASE_URL = "https://bmclapi2.bangbang93.com"

    def __init__(self):
        self.signals = DownloaderSignals()

    def _get_json(self, url):
        """通用方法，用于发送GET请求并返回JSON数据"""
        try:
            response = requests.get(url, timeout=10) 
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.RequestException as e:
            self.signals.log_message.emit(f"网络请求失败: {url} - {e}")
            return None

    # Helper function for version parsing (new)
    def _parse_version_string(self, version_str):
        """
        解析版本字符串，返回一个可用于排序的元组。
        处理数字和非数字部分，并将非数字部分（如'beta', 'alpha', 'pre'）
        排在数字部分之后，或根据其字母顺序排序。
        例如: "1.20.1-47.1.12", "1.20.1-47.1.12-beta", "1.20.1-47.1.13"
        应排序为: 1.20.1-47.1.13, 1.20.1-47.1.12, 1.20.1-47.1.12-beta
        """
        parts = []
        # 分割主版本号和构建号，例如 "1.20.1-47.1.12-beta" -> "1.20.1", "47.1.12-beta"
        main_version_parts = version_str.split('-', 1) 
        
        mc_version_nums = [int(x) if x.isdigit() else x for x in main_version_parts[0].split('.')]
        parts.extend(mc_version_nums)

        if len(main_version_parts) > 1:
            build_info = main_version_parts[1]
            sub_parts = re.split(r'(\d+)', build_info)
            for sub_part in sub_parts:
                if sub_part: 
                    if sub_part.isdigit():
                        parts.append(int(sub_part))
                    else:
                        parts.append(sub_part.lower())
        return tuple(parts) 


    def get_minecraft_versions(self):
        """
        从BMCLAPI获取Minecraft版本列表。
        对应文档：http://launchermeta.mojang.com/mc/game/version_manifest_v2.json -> https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json
        """
        self.signals.log_message.emit("正在从 BMCLAPI 获取 Minecraft 版本列表...")
        url = f"{self.BASE_URL}/mc/game/version_manifest_v2.json"
        data = self._get_json(url)
        if data and "versions" in data:
            # 过滤掉一些非release版本，或者根据需要进行排序
            versions = [v['id'] for v in data['versions'] if v['type'] == 'release']
            versions.sort(key=lambda s: list(map(int, s.split('.'))), reverse=True) 
            self.signals.log_message.emit(f"成功获取 {len(versions)} 个 Minecraft 版本。")
            return versions
        self.signals.log_message.emit("获取 Minecraft 版本失败。")
        return []

    def get_server_types(self, mc_version):
        """
        根据Minecraft版本获取支持的服务端核心类型 (例如：vanilla, forge, fabric, neoforge, liteloader, bukkit, paper, spigot, catserver, mohist)。
        """
        self.signals.log_message.emit(f"正在获取 Minecraft {mc_version} 的服务端核心类型...")
        supported_types = ["vanilla"] 

        # 检查 Forge 是否支持该MC版本
        # BMCLAPI文档：Forge | 获取forge支持的minecraft版本列表
        forge_mc_versions_url = f"{self.BASE_URL}/forge/minecraft"
        forge_mc_versions = self._get_json(forge_mc_versions_url)
        if forge_mc_versions and mc_version in forge_mc_versions:
            supported_types.append("forge")

        # 检查 Fabric 是否支持该MC版本
        # Fabric API (通过 BMCLAPI 镜像): https://bmclapi2.bangbang93.com/fabric-meta/v2/versions/loader/
        fabric_loader_url = f"{self.BASE_URL}/fabric-meta/v2/versions/loader/{mc_version}"
        fabric_loaders = self._get_json(fabric_loader_url)
        if fabric_loaders and isinstance(fabric_loaders, list) and len(fabric_loaders) > 0:
            supported_types.append("fabric")


        # 检查 Neoforge 是否支持该MC版本
        # BMCLAPI文档：Neoforge | 根据minecraft版本获取neoforge列表
        neoforge_list_url = f"{self.BASE_URL}/neoforge/list/{mc_version}"
        neoforge_versions = self._get_json(neoforge_list_url)
        if neoforge_versions:
            supported_types.append("neoforge")

        # 检查 Liteloader 是否支持该MC版本
        # BMCLAPI文档：Liteloader | 获取liteloader列表
        liteloader_list_url = f"{self.BASE_URL}/liteloader/list?mcversion={mc_version}"
        liteloader_versions = self._get_json(liteloader_list_url)
        if liteloader_versions:
            supported_types.append("liteloader")


        # 检查 Optifine 是否支持该MC版本
        # BMCLAPI文档：Optifine | 获取optifine列表
        optifine_url = f"{self.BASE_URL}/optifine/{mc_version}"
        optifine_versions = self._get_json(optifine_url)
        if optifine_versions:
            supported_types.append("optifine")

        return sorted(list(set(supported_types))) # 去重并排序

    def get_core_versions(self, mc_version, server_type):
        """
        根据Minecraft版本和服务端类型获取核心版本列表。
        """
        self.signals.log_message.emit(f"正在获取 {mc_version} {server_type} 的核心版本列表...")
        versions = []

        if server_type == "vanilla":
            url = f"{self.BASE_URL}/mc/game/version_manifest_v2.json"
            data = self._get_json(url)
            if data and "versions" in data:
                for v in data['versions']:
                    if v['id'] == mc_version and v['type'] == 'release':
                        # 原版服务端通常只有一个版本，用MC版本号代表
                        versions.append(mc_version)
                        break
            if not versions:
                self.signals.log_message.emit(f"未找到 {mc_version} 的原版核心版本。")
            versions = [str(v) for v in versions]
        
        elif server_type == "forge":
            # BMCLAPI文档：Forge | 根据版本获取forge列表
            url = f"{self.BASE_URL}/forge/minecraft/{mc_version}"
            forge_builds = self._get_json(url)
            if forge_builds:
                versions = [str(b['version']) for b in forge_builds]
                versions.sort(key=self._parse_version_string, reverse=True)
            if not versions:
                self.signals.log_message.emit(f"未找到 {mc_version} 的 Forge 核心版本。")
        
        elif server_type == "fabric":
            loader_url = f"{self.BASE_URL}/fabric-meta/v2/versions/loader/{mc_version}"
            installer_url = f"{self.BASE_URL}/fabric-meta/v2/versions/installer"
            loaders = self._get_json(loader_url)
            installers = self._get_json(installer_url)
            if isinstance(loaders, list) and isinstance(installers, list) and loaders and installers:
                for loader in loaders:
                    loader_version = loader.get('loader') or loader.get('version')
                    if isinstance(loader_version, dict):
                        loader_version = loader_version.get('version')
                    if not isinstance(loader_version, str):
                        continue
                    for installer in installers:
                        installer_version = installer.get('version')
                        if installer_version:
                            versions.append(f"loader-{loader_version}-installer-{installer_version}")
                versions = [str(v) for v in versions]
                versions.sort(key=self._parse_version_string, reverse=True)
            else:
                self.signals.log_message.emit(f"未找到 {mc_version} 的 Fabric loader 或 installer 版本。")
        
        elif server_type == "neoforge":
            # BMCLAPI文档：Neoforge | 根据minecraft版本获取neoforge列表
            url = f"{self.BASE_URL}/neoforge/list/{mc_version}"
            neoforge_list = self._get_json(url)
            if neoforge_list:
                versions = [str(v['rawVersion']) for v in neoforge_list]
                versions.sort(key=self._parse_version_string, reverse=True)
            if not versions:
                self.signals.log_message.emit(f"未找到 {mc_version} 的 Neoforge 核心版本。")
        
        elif server_type == "liteloader":
            # BMCLAPI文档：Liteloader | 获取liteloader列表
            url = f"{self.BASE_URL}/liteloader/list?mcversion={mc_version}"
            liteloader_list = self._get_json(url)
            if liteloader_list:
                versions = [str(l['version']) for l in liteloader_list]
                versions.sort(key=self._parse_version_string, reverse=True)
            if not versions:
                self.signals.log_message.emit(f"未找到 {mc_version} 的 Liteloader 核心版本。")
        
        elif server_type == "optifine":
            # BMCLAPI文档：Optifine | 获取optifine列表
            url = f"{self.BASE_URL}/optifine/{mc_version}"
            optifine_list = self._get_json(url)
            if optifine_list:
                versions = [str(f"{o['type']}_{o['patch']}") for o in optifine_list]
                versions.sort(key=self._parse_version_string, reverse=True)
            if not versions:
                self.signals.log_message.emit(f"未找到 {mc_version} 的 Optifine 核心版本。")

        return versions

    def get_download_url_and_filename(self, mc_version, server_type, core_version_info):
        """
        根据Minecraft版本、服务端类型和核心版本信息获取BMCLAPI镜像源下载链接和文件名。
        """
        self.signals.log_message.emit(f"正在获取 {mc_version} {server_type} {core_version_info} 的下载链接...")
        download_url = None
        file_name = None

        if server_type == "vanilla":
            download_url = f"https://bmclapi2.bangbang93.com/version/{mc_version}/server/"
            file_name = f"minecraft_server-{mc_version}.jar"
            self.signals.log_message.emit(f"获取到 Vanilla BMCLAPI 镜像源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "forge":
            download_url = f"https://bmclapi2.bangbang93.com/forge/download?mcversion={mc_version}&version={core_version_info}&category=installer&format=jar"
            file_name = f"forge-{mc_version}-{core_version_info}-installer.jar"
            self.signals.log_message.emit(f"获取到 Forge BMCLAPI 镜像源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "fabric":
            loader_version = None
            installer_version = None
            if core_version_info.startswith("loader-") and "-installer-" in core_version_info:
                try:
                    loader_version = core_version_info.split("loader-")[1].split("-installer-")[0]
                    installer_version = core_version_info.split("-installer-")[1]
                except Exception:
                    loader_version = None
                    installer_version = None
            if loader_version and installer_version:
                # 始终使用官方源下载
                download_url = f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}/{loader_version}/{installer_version}/server/jar"
                file_name = f"fabric-server-mc.{mc_version}-loader.{loader_version}-installer.{installer_version}.jar"
                self.signals.log_message.emit(f"获取到 Fabric 官方源下载链接: {download_url}")
                return download_url, file_name
            else:
                self.signals.log_message.emit("Fabric core_version_info 格式错误，无法生成下载链接。")
                return None, None

        elif server_type == "neoforge":
            neoforge_version = core_version_info.replace("neoforge-", "")
            file_type = "installer.jar"  
            download_url = f"https://bmclapi2.bangbang93.com/neoforge/version/{neoforge_version}/download/{file_type}"
            file_name = f"neoforge-{mc_version}-{neoforge_version}-{file_type}"
            self.signals.log_message.emit(f"获取到 Neoforge BMCLAPI 镜像源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "liteloader":
            download_url = f"https://bmclapi2.bangbang93.com/maven/com/mumfrey/liteloader/{core_version_info}/liteloader-{core_version_info}.jar"
            file_name = f"liteloader-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Liteloader BMCLAPI 镜像源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "optifine":
            if '_' in core_version_info:
                type_part, patch_part = core_version_info.split('_', 1)
            else:
                type_part, patch_part = core_version_info, ''
            download_url = f"https://bmclapi2.bangbang93.com/optifine/{mc_version}/{type_part}/{patch_part}"
            file_name = f"optifine-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Optifine BMCLAPI 镜像源下载链接: {download_url}")
            return download_url, file_name

        self.signals.log_message.emit("未能获取到有效的下载链接。")
        return None, None

    def download_file(self, url, dest_folder, file_name):
        """
        下载文件到指定文件夹。
        下载前先检查链接是否存在，避免404。
        """
        # 检查链接是否存在
        try:
            head_resp = requests.head(url, timeout=10, allow_redirects=True)
            if head_resp.status_code != 200:
                self.signals.log_message.emit(f"文件未找到或未同步: {url}")
                self.signals.download_finished.emit("", False)
                return
        except Exception as e:
            self.signals.log_message.emit(f"检测文件链接失败: {e}")
            self.signals.download_finished.emit("", False)
            return

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        file_size = None
        try:
            #  HEAD 请求获取文件大小
            head_resp = requests.head(url, timeout=10, allow_redirects=True)
            if head_resp.ok:
                cl = head_resp.headers.get('content-length')
                try:
                    file_size = int(cl) if cl and int(cl) > 0 else None
                except Exception:
                    file_size = None
        except Exception:
            file_size = None  
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            block_size = 1024
            downloaded_size = 0
            with open(os.path.join(dest_folder, "temp_file"), 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded_size += len(data)
                    if file_size:
                        percent = int(downloaded_size / file_size * 100)
                        percent = min(percent, 100)
                        self.signals.progress_update.emit(percent)
                    else:
                        # 没有文件大小时，无法准确显示进度，只能发100
                        self.signals.progress_update.emit(100)
            os.rename(os.path.join(dest_folder, "temp_file"), os.path.join(dest_folder, file_name))
            self.signals.log_message.emit(f"文件下载完成: {file_name}")
            self.signals.download_finished.emit(os.path.join(dest_folder, file_name), True)
        except Exception as e:
            self.signals.log_message.emit(f"文件下载失败: {e}")
            self.signals.download_finished.emit("", False)

class DataLoaderWorker(QObject):
    data_loaded = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader

    def run(self):
        mc_versions = self.downloader.get_minecraft_versions()
        self.data_loaded.emit(mc_versions)
        self.finished.emit()

class ServerTypeLoaderWorker(QObject):
    server_types_loaded = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, downloader, mc_version):
        super().__init__()
        self.downloader = downloader
        self.mc_version = mc_version

    def run(self):
        server_types = self.downloader.get_server_types(self.mc_version)
        self.server_types_loaded.emit(server_types)
        self.finished.emit()

class CoreVersionLoaderWorker(QObject):
    core_versions_loaded = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, downloader, mc_version, server_type):
        super().__init__()
        self.downloader = downloader
        self.mc_version = mc_version
        self.server_type = server_type

    def run(self):
        core_versions = self.downloader.get_core_versions(self.mc_version, self.server_type)
        self.core_versions_loaded.emit(core_versions or [])
        self.finished.emit()

class DownloadWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, downloader, url, file_path):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.file_path = file_path

    def run(self):
        dest_folder = os.path.dirname(self.file_path)
        file_name = os.path.basename(self.file_path)
        self.downloader.download_file(self.url, dest_folder, file_name)
        self.finished.emit()
