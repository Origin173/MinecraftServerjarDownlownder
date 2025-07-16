import requests
import os
import json
from PyQt5.QtCore import pyqtSignal, QObject
import re 
from bs4 import BeautifulSoup
import uuid

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
        parts.append(mc_version_nums)
        
        if len(main_version_parts) > 1:
            # 有构建号，例如 "47.1.12-beta"
            build_info = main_version_parts[1]
            # 分割数字和非数字部分，例如 "47.1.12-beta" -> "47.1.12", "beta"
            build_parts = build_info.split('-', 1)
            build_nums = [int(x) if x.isdigit() else x for x in build_parts[0].split('.')]
            parts.append(build_nums)
            if len(build_parts) > 1:
                # 有非数字部分，例如 "beta"
                parts.append(build_parts[1])
        
        return parts

    def _parse_mcc_version(self, version_str):
        """
        解析 MCC 版本字符串，返回一个可用于排序的元组。
        例如: "1.20.1-47.1.12", "1.20.1-47.1.12-beta", "1.20.1-47.1.13"
        """
        try:
            parts = version_str.split('-', 2)
            if len(parts) >= 2:
                mc_version = parts[0]
                build_version = parts[1]
                extra = parts[2] if len(parts) > 2 else ""
                
                # 解析 MC 版本
                mc_parts = [int(x) if x.isdigit() else x for x in mc_version.split('.')]
                
                # 解析构建版本
                build_parts = [int(x) if x.isdigit() else x for x in build_version.split('.')]
                
                # 排序键: MC版本 (降序), 构建版本 (降序), 额外信息 (升序)
                return (mc_parts, build_parts, extra)
            else:
                return ([int(x) if x.isdigit() else x for x in version_str.split('.')], [], "")
        except Exception:
            return ([version_str], [], "")

    def get_minecraft_versions(self):
        """获取 Minecraft 版本列表"""
        self.signals.log_message.emit("正在获取 Minecraft 版本列表...")
        
        try:
            data = self._get_json(f"{self.BASE_URL}/mc/game/version_manifest.json")
            if data:
                versions = [version['id'] for version in data['versions'] if version['type'] == 'release']
                self.signals.log_message.emit(f"获取到 {len(versions)} 个版本")
                return versions
            else:
                self.signals.log_message.emit("获取 Minecraft 版本列表失败")
                return []
        except Exception as e:
            self.signals.log_message.emit(f"获取 Minecraft 版本列表失败: {e}")
            return []

    def get_server_types(self, mc_version):
        """获取指定 Minecraft 版本的服务端类型"""
        self.signals.log_message.emit(f"正在获取 {mc_version} 版本的服务端类型...")
        
        # 根据版本确定可用的服务端类型
        available_types = []
        
        # 所有版本都支持原版
        available_types.append("vanilla")
        
        # 根据版本添加其他服务端类型
        if mc_version >= "1.14":
            available_types.extend(["fabric", "forge", "neoforge"])
        elif mc_version >= "1.12":
            available_types.extend(["fabric", "forge"])
        elif mc_version >= "1.7":
            available_types.append("forge")
        
        # 插件服务端
        if mc_version >= "1.8":
            available_types.append("optifine")
        
        self.signals.log_message.emit(f"获取到 {len(available_types)} 个服务端类型")
        return available_types

    def get_core_versions(self, mc_version, server_type):
        """获取指定 Minecraft 版本和服务端类型的核心版本"""
        self.signals.log_message.emit(f"正在获取 {server_type} {mc_version} 的核心版本...")
        
        try:
            if server_type == "vanilla":
                # 原版服务端只有一个版本
                return [mc_version]
            elif server_type == "forge":
                # 获取 Forge 版本
                data = self._get_json(f"{self.BASE_URL}/forge/minecraft/{mc_version}")
                if data:
                    # 排序版本
                    versions = sorted(data, key=lambda x: self._parse_mcc_version(x['version']), reverse=True)
                    return [version['version'] for version in versions]
                else:
                    return []
            elif server_type == "fabric":
                # 获取 Fabric 版本
                loader_data = self._get_json(f"{self.BASE_URL}/fabric-meta/v2/versions/loader/{mc_version}")
                if loader_data:
                    # 排序版本
                    versions = sorted(loader_data, key=lambda x: self._parse_version_string(x['loader']['version']), reverse=True)
                    return [version['loader']['version'] for version in versions]
                else:
                    return []
            elif server_type == "neoforge":
                # 获取 NeoForge 版本
                data = self._get_json(f"{self.BASE_URL}/neoforge/list/{mc_version}")
                if data:
                    # 排序版本
                    versions = sorted(data, key=lambda x: self._parse_version_string(x['version']), reverse=True)
                    return [version['version'] for version in versions]
                else:
                    return []
            elif server_type == "optifine":
                # 获取 OptiFine 版本
                data = self._get_json(f"{self.BASE_URL}/optifine/{mc_version}")
                if data:
                    # 排序版本
                    versions = sorted(data, key=lambda x: self._parse_version_string(x['patch']), reverse=True)
                    return [version['patch'] for version in versions]
                else:
                    return []
            else:
                return []
        except Exception as e:
            self.signals.log_message.emit(f"获取核心版本失败: {e}")
            return []

    def get_download_url_and_filename(self, mc_version, server_type, core_version_info):
        """获取下载链接和文件名"""
        self.signals.log_message.emit(f"正在获取 {server_type} {mc_version} 的下载链接...")
        
        try:
            if server_type == "vanilla":
                # 原版服务端
                version_data = self._get_json(f"{self.BASE_URL}/mc/game/version_manifest.json")
                if version_data:
                    for version in version_data['versions']:
                        if version['id'] == mc_version:
                            version_detail = self._get_json(version['url'])
                            if version_detail and 'downloads' in version_detail and 'server' in version_detail['downloads']:
                                server_info = version_detail['downloads']['server']
                                return server_info['url'], f"minecraft_server-{mc_version}.jar"
                return None, None
            elif server_type == "forge":
                # Forge 服务端
                data = self._get_json(f"{self.BASE_URL}/forge/minecraft/{mc_version}")
                if data:
                    for version in data:
                        if version['version'] == core_version_info:
                            files = version.get('files', [])
                            for file in files:
                                if file[1] == 'installer':
                                    return file[0], f"forge-{mc_version}-{core_version_info}-installer.jar"
                return None, None
            elif server_type == "fabric":
                # Fabric 服务端
                installer_data = self._get_json(f"{self.BASE_URL}/fabric-meta/v2/versions/installer")
                if installer_data:
                    latest_installer = installer_data[0]['version']
                    url = f"{self.BASE_URL}/fabric/{mc_version}/{core_version_info}/{latest_installer}/server/jar"
                    filename = f"fabric-server-mc.{mc_version}-loader.{core_version_info}-installer.{latest_installer}.jar"
                    return url, filename
                return None, None
            elif server_type == "neoforge":
                # NeoForge 服务端
                data = self._get_json(f"{self.BASE_URL}/neoforge/list/{mc_version}")
                if data:
                    for version in data:
                        if version['version'] == core_version_info:
                            return version['url'], f"neoforge-{mc_version}-{core_version_info}.jar"
                return None, None
            elif server_type == "optifine":
                # OptiFine
                data = self._get_json(f"{self.BASE_URL}/optifine/{mc_version}")
                if data:
                    for version in data:
                        if version['patch'] == core_version_info:
                            return version['url'], f"optifine-{mc_version}-{core_version_info}.jar"
                return None, None
            else:
                return None, None
        except Exception as e:
            self.signals.log_message.emit(f"获取下载链接失败: {e}")
            return None, None

    def download_file(self, url, dest_folder, file_name):
        """下载文件"""
        self.signals.log_message.emit(f"开始下载: {file_name}")
        
        os.makedirs(dest_folder, exist_ok=True)
        file_path = os.path.join(dest_folder, file_name)
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.signals.progress_update.emit(progress)
            
            self.signals.log_message.emit(f"下载完成: {file_name}")
            self.signals.download_finished.emit(file_path, True)
            return True
        except Exception as e:
            self.signals.log_message.emit(f"下载失败: {e}")
            self.signals.download_finished.emit(file_path, False)
            return False

# Worker classes for threading
class DataLoaderWorker(QObject):
    data_loaded = pyqtSignal(list)
    finished = pyqtSignal()
    
    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader
    
    def run(self):
        data = self.downloader.get_minecraft_versions()
        self.data_loaded.emit(data)
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
        self.core_versions_loaded.emit(core_versions)
        self.finished.emit()

class DownloadWorker(QObject):
    download_finished = pyqtSignal(str, bool)
    finished = pyqtSignal()
    
    def __init__(self, downloader, url, dest_folder, file_name):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.dest_folder = dest_folder
        self.file_name = file_name
    
    def run(self):
        success = self.downloader.download_file(self.url, self.dest_folder, self.file_name)
        self.download_finished.emit(os.path.join(self.dest_folder, self.file_name), success)
        self.finished.emit()

class MSLAPIDownloader:
    """
    MSL API 下载器，基于 MSL API V3 文档实现
    """
    BASE_URL = "https://api.mslmc.cn/v3"
    
    def __init__(self):
        self.signals = DownloaderSignals()
        self.device_id = self._get_or_create_device_id()
        self.headers = {
            'deviceID': self.device_id,
            'User-Agent': 'MinecraftServerjarDownloader/1.0'
        }
        self.signals.log_message.emit(f"MSL API 已初始化，设备ID: {self.device_id}")

    def _get_or_create_device_id(self):
        """获取或创建设备ID"""
        device_id_file = "device_id.json"
        
        if os.path.exists(device_id_file):
            try:
                with open(device_id_file, 'r') as f:
                    data = json.load(f)
                    return data.get('device_id')
            except:
                pass
        
        # 创建新的设备ID
        device_id = str(uuid.uuid4())
        try:
            with open(device_id_file, 'w') as f:
                json.dump({'device_id': device_id}, f)
        except:
            pass
        
        return device_id

    def _get_json(self, url):
        """通用方法，用于发送GET请求并返回JSON数据"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.signals.log_message.emit(f"MSL API 请求失败: {url} - {e}")
            return None

    def get_notice(self):
        """获取公告信息"""
        self.signals.log_message.emit("正在从 MSL API 获取公告...")
        
        url = f"{self.BASE_URL}/query/notice"
        data = self._get_json(url)
        
        if data and data.get("code") == 200:
            notice_data = data.get("data", {})
            notice_text = notice_data.get("notice", "")
            self.signals.log_message.emit("获取到公告信息")
            return notice_text
        else:
            self.signals.log_message.emit("获取公告失败")
            return ""

    def get_server_types(self):
        """获取 MSL 支持的所有服务端类型"""
        self.signals.log_message.emit("正在从 MSL API 获取支持的服务端类型...")
        
        url = f"{self.BASE_URL}/query/available_server_types"
        data = self._get_json(url)
        
        if data and data.get("code") == 200:
            server_types = data.get("data", {}).get("types", [])
            if server_types:
                self.signals.log_message.emit(f"获取到 {len(server_types)} 个服务端类型")
                return server_types
            else:
                self.signals.log_message.emit("未找到服务端类型")
                return []
        else:
            self.signals.log_message.emit("获取 MSL API 服务端类型失败，使用默认类型")
            # 返回默认的服务端类型
            return ["vanilla", "forge", "fabric", "neoforge", "bukkit", "paper", "spigot", "catserver", "mohist"]

    def get_server_classify(self):
        """获取服务端分类信息"""
        self.signals.log_message.emit("正在从 MSL API 获取服务端分类...")
        
        url = f"{self.BASE_URL}/query/server_classify"
        data = self._get_json(url)
        
        if data and data.get("code") == 200:
            classify_data = data.get("data", {})
            self.signals.log_message.emit("获取到服务端分类信息")
            return classify_data
        else:
            self.signals.log_message.emit("获取服务端分类失败")
            return {}

    def get_available_versions(self, server_type):
        """获取指定服务端类型的可用版本"""
        self.signals.log_message.emit(f"正在从 MSL API 获取 {server_type} 的可用版本...")
        
        # 由于MSL API的available_versions端点不存在，我们返回常见的Minecraft版本
        common_versions = [
            "1.21.7", "1.21.6", "1.21.5", "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
            "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
            "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
            "1.18.2", "1.18.1", "1.18",
            "1.17.1", "1.17",
            "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
            "1.15.2", "1.15.1", "1.15",
            "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
            "1.13.2", "1.13.1", "1.13",
            "1.12.2", "1.12.1", "1.12",
            "1.11.2", "1.11.1", "1.11",
            "1.10.2", "1.10.1", "1.10",
            "1.9.4", "1.9.3", "1.9.2", "1.9.1", "1.9",
            "1.8.9", "1.8.8", "1.8.7", "1.8.6", "1.8.5", "1.8.4", "1.8.3", "1.8.2", "1.8.1", "1.8",
            "1.7.10", "1.7.9", "1.7.8", "1.7.7", "1.7.6", "1.7.5", "1.7.4", "1.7.3", "1.7.2",
            "1.6.4", "1.6.2", "1.6.1", "1.5.2", "1.5.1", "1.4.7", "1.4.6", "1.4.5", "1.4.4", "1.4.2",
            "1.3.2", "1.3.1", "1.2.5"
        ]
        
        self.signals.log_message.emit(f"获取到 {server_type} 的 {len(common_versions)} 个版本")
        return common_versions

    def get_server_builds_info(self, server_type, mc_version):
        """获取指定服务端类型和版本的构建信息"""
        self.signals.log_message.emit(f"MSL API 暂不支持构建信息查询")
        return {}

    def get_server_builds(self, server_type, mc_version):
        """获取构建版本列表（兼容性方法）"""
        builds_info = self.get_server_builds_info(server_type, mc_version)
        
        if builds_info:
            # 尝试从构建信息中提取版本列表
            builds = builds_info.get("builds", [])
            if builds:
                return [build.get("version", "latest") for build in builds]
            else:
                return ["latest"]
        else:
            return ["latest"]

    def get_java_versions(self):
        """获取支持的Java版本列表"""
        self.signals.log_message.emit("MSL API 暂不支持Java版本查询，返回常用版本")
        # 返回常用的Java版本
        return ["Java8", "Java11", "Java17", "Java21"]

    def get_java_download_url(self, java_version):
        """获取特定Java版本的下载地址"""
        self.signals.log_message.emit(f"MSL API 暂不支持Java下载功能")
        return ""

    def get_download_url_and_filename(self, server_type, mc_version, core_version_info):
        """获取下载链接和文件名"""
        self.signals.log_message.emit(f"正在从 MSL API 获取 {server_type} {mc_version} 的下载链接...")
        
        # 使用新的 download/server API 端点
        url = f"{self.BASE_URL}/download/server/{server_type}/{mc_version}"
        
        # 构建查询参数
        params = {}
        if core_version_info and core_version_info.lower() != 'latest':
            params['build'] = core_version_info
        else:
            params['build'] = 'latest'
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get("code") == 200:
                download_data = data.get("data", {})
                download_url = download_data.get("url", "")
                sha256 = download_data.get("sha256", "")
                
                if download_url:
                    # 从 URL 中提取文件名
                    filename = download_url.split('/')[-1]
                    if not filename or not filename.endswith('.jar'):
                        filename = f"{server_type}-{mc_version}.jar"
                    
                    self.signals.log_message.emit(f"获取到 {server_type} {mc_version} 的下载链接")
                    if sha256:
                        self.signals.log_message.emit(f"SHA256 校验码: {sha256}")
                    
                    return download_url, filename
                else:
                    self.signals.log_message.emit(f"未找到 {server_type} {mc_version} 的下载链接")
                    return None, None
            else:
                error_msg = data.get("message", "未知错误") if data else "响应格式错误"
                self.signals.log_message.emit(f"获取 {server_type} {mc_version} 下载链接失败: {error_msg}")
                return None, None
                
        except requests.exceptions.RequestException as e:
            self.signals.log_message.emit(f"网络请求失败: {e}")
            return None, None
        except Exception as e:
            self.signals.log_message.emit(f"获取 {server_type} {mc_version} 下载链接失败: {e}")
            return None, None

    def get_server_description(self, server_type):
        """获取服务端简介信息（从分类信息中获取）"""
        classify_data = self.get_server_classify()
        
        # 在分类中查找服务端类型
        for category, servers in classify_data.items():
            if server_type in servers:
                return f"{server_type} 服务端（归类为 {category}）"
        
        return f"{server_type} 服务端"

    def download_file(self, url, dest_folder, file_name):
        """下载文件"""
        self.signals.log_message.emit(f"开始下载: {file_name}")
        
        os.makedirs(dest_folder, exist_ok=True)
        file_path = os.path.join(dest_folder, file_name)
        
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.signals.progress_update.emit(progress)
            
            self.signals.log_message.emit(f"下载完成: {file_name}")
            self.signals.download_finished.emit(file_path, True)
            return True
        except Exception as e:
            self.signals.log_message.emit(f"下载失败: {e}")
            self.signals.download_finished.emit(file_path, False)
            return False

class UnifiedDownloader:
    """
    统一下载器，整合 BMCLAPI 和 MSL API
    """
    def __init__(self):
        self.signals = DownloaderSignals()
        self.bmcl_downloader = BMCLAPIDownloader()
        self.msl_downloader = MSLAPIDownloader()
        self.current_source = "bmcl"  # 默认使用 BMCL
        
        # 同步信号
        self.bmcl_downloader.signals = self.signals
        self.msl_downloader.signals = self.signals
    
    def _parse_version_for_sorting(self, version):
        """解析版本号用于排序"""
        try:
            # 提取主版本号 (1.21.7 -> [1, 21, 7])
            parts = version.split('.')
            return [int(part) if part.isdigit() else 0 for part in parts]
        except:
            return [0]
    
    def switch_source(self, source):
        """切换下载源"""
        if source in ["bmcl", "msl"]:
            self.current_source = source
            self.signals.log_message.emit(f"已切换到 {'BMCL API' if source == 'bmcl' else 'MSL API'} 镜像源")
        else:
            self.signals.log_message.emit("不支持的下载源")
    
    def get_minecraft_versions(self):
        """获取 Minecraft 版本列表"""
        if self.current_source == "bmcl":
            return self.bmcl_downloader.get_minecraft_versions()
        else:
            # MSL API 通过服务端类型获取版本，需要聚合所有服务端类型的版本
            try:
                server_types = self.msl_downloader.get_server_types()
                if not server_types:
                    self.signals.log_message.emit("无法获取服务端类型列表")
                    return []
                
                all_versions = set()
                for server_type in server_types:
                    versions = self.msl_downloader.get_available_versions(server_type)
                    all_versions.update(versions)
                
                # 转换为列表并排序（版本号降序）
                version_list = sorted(list(all_versions), key=lambda x: self._parse_version_for_sorting(x), reverse=True)
                return version_list
            except Exception as e:
                self.signals.log_message.emit(f"获取MSL API版本列表失败: {str(e)}")
                return []
    
    def get_server_types(self, mc_version=None):
        """获取服务端类型"""
        if self.current_source == "bmcl":
            return self.bmcl_downloader.get_server_types(mc_version)
        else:
            return self.msl_downloader.get_server_types()
    
    def get_core_versions(self, mc_version, server_type):
        """获取核心版本"""
        if self.current_source == "bmcl":
            return self.bmcl_downloader.get_core_versions(mc_version, server_type)
        else:
            return self.msl_downloader.get_server_builds(server_type, mc_version)
    
    def get_download_url_and_filename(self, mc_version, server_type, core_version_info):
        """获取下载链接和文件名"""
        if self.current_source == "bmcl":
            return self.bmcl_downloader.get_download_url_and_filename(mc_version, server_type, core_version_info)
        else:
            return self.msl_downloader.get_download_url_and_filename(server_type, mc_version, core_version_info)
    
    def get_server_description(self, server_type):
        """获取服务端简介信息"""
        if self.current_source == "msl":
            return self.msl_downloader.get_server_description(server_type)
        else:
            # BMCL API 没有提供服务端简介接口，返回默认描述
            default_descriptions = {
                "vanilla": "官方原版服务端，最稳定的Minecraft服务端",
                "forge": "支持Mod的服务端，拥有丰富的模组生态系统",
                "fabric": "轻量级的Mod服务端，启动速度快，适合现代Mod开发",
                "neoforge": "Forge的新分支，提供更好的性能和现代化的开发体验",
                "bukkit": "经典的插件服务端，拥有丰富的插件生态",
                "paper": "基于Spigot的高性能服务端，优化了游戏性能",
                "spigot": "Bukkit的高性能分支，支持插件开发",
                "catserver": "同时支持Mod和插件的混合服务端",
                "mohist": "高性能的Mod+插件混合服务端"
            }
            return default_descriptions.get(server_type, f"{server_type} 服务端")
    
    def get_server_classify(self):
        """获取服务端分类信息（仅MSL API支持）"""
        if self.current_source == "msl":
            return self.msl_downloader.get_server_classify()
        else:
            self.signals.log_message.emit("BMCL API 不支持服务端分类功能")
            return {}
    
    def get_java_versions(self):
        """获取支持的Java版本列表（仅MSL API支持）"""
        if self.current_source == "msl":
            return self.msl_downloader.get_java_versions()
        else:
            self.signals.log_message.emit("BMCL API 不支持Java版本查询功能")
            return []
    
    def get_java_download_url(self, java_version):
        """获取特定Java版本的下载地址（仅MSL API支持）"""
        if self.current_source == "msl":
            return self.msl_downloader.get_java_download_url(java_version)
        else:
            self.signals.log_message.emit("BMCL API 不支持Java下载功能")
            return ""
    
    def get_notice(self):
        """获取公告（仅MSL API支持）"""
        if self.current_source == "msl":
            return self.msl_downloader.get_notice()
        else:
            self.signals.log_message.emit("BMCL API 不支持公告查询功能")
            return ""
    
    def download_file(self, url, dest_folder, file_name):
        """统一下载方法"""
        return self.bmcl_downloader.download_file(url, dest_folder, file_name)
