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
        main_version_parts = version_str.split('-', 1) # Split only on the first '-'
        
        # Handle the MC version part (e.g., "1.20.1")
        mc_version_nums = [int(x) if x.isdigit() else x for x in main_version_parts[0].split('.')]
        parts.extend(mc_version_nums)

        if len(main_version_parts) > 1:
            build_info = main_version_parts[1]
            # Split build info further by '.' and potentially by non-digits for suffixes
            # Using re.split to handle numbers and non-numbers
            sub_parts = re.split(r'(\d+)', build_info)
            for sub_part in sub_parts:
                if sub_part: # Filter out empty strings from re.split
                    if sub_part.isdigit():
                        parts.append(int(sub_part))
                    else:
                        # For non-numeric parts (e.g., 'beta', 'alpha', 'pre'),
                        # prepend a character to ensure they sort lexicographically after numbers,
                        # or specifically handle common pre-release terms.
                        # For reverse sorting, we want 'beta' to come *after* stable numbers.
                        # A common strategy is to assign large numbers to stable versions and
                        # smaller/negative numbers to pre-releases, or use a tuple for comparison.
                        
                        # Let's use a tuple for (is_numeric, value)
                        # Higher value for stable, lower for pre-release
                        # Example: ('beta', -1), ('alpha', -2) for reverse sorting
                        # Or just regular string comparison, ensuring 'beta' comes after numbers
                        
                        # For reverse sorting, 'beta' should effectively be "smaller" than numbers.
                        # We can add a high sorting value for stable versions and a low one for pre-releases.
                        # Or, simplest for now: treat all numeric parts as numbers, others as strings.
                        # For reverse sorting, 'beta' needs to be handled carefully.
                        # A robust way is to convert things into (numeric_value, string_suffix_value)
                        
                        # Simpler: convert to lowercase and treat as string.
                        # In reverse sort, 'z' is "smaller" than 'a'
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
            versions.sort(key=lambda s: list(map(int, s.split('.'))), reverse=True) # 按照版本号降序排序
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
  
  
        # 以下内容未实现
        # # 检查 Paper 是否支持该MC版本（官方Fill v3 API）
        # try:
        #     paper_versions_url = "https://fill.papermc.io/v3/projects/paper/versions"
        #     paper_data = requests.get(paper_versions_url, timeout=5).json()
        #     if 'versions' in paper_data and mc_version in paper_data['versions']:
        #         supported_types.append("paper")
        # except Exception:
        #     pass

        # # 检查 Bukkit 是否支持该MC版本（官方API）
        # try:
        #     bukkit_versions_url = "https://api.getbukkit.org/craftbukkit/versions"
        #     bukkit_data = requests.get(bukkit_versions_url, timeout=5).json()
        #     if isinstance(bukkit_data, list) and mc_version in bukkit_data:
        #         supported_types.append("bukkit")
        # except Exception:
        #     pass

        # # 检查 Spigot 是否支持该MC版本（官方API）
        # try:
        #     spigot_versions_url = "https://api.getbukkit.org/spigot/versions"
        #     spigot_data = requests.get(spigot_versions_url, timeout=5).json()
        #     if isinstance(spigot_data, list) and mc_version in spigot_data:
        #         supported_types.append("spigot")
        # except Exception:
        #     pass

        # # 检查 CatServer 是否支持该MC版本（通过目录检测）
        # try:
        #     catserver_url = f"https://download.catserver.cn/{mc_version}/"
        #     resp = requests.head(catserver_url, timeout=5)
        #     if resp.status_code == 200:
        #         supported_types.append("catserver")
        # except Exception:
        #     pass

        # # 检查 Mohist 是否支持该MC版本（官方API）
        # try:
        #     mohist_versions_url = "https://mohistmc.com/api/v2/versions"
        #     mohist_data = requests.get(mohist_versions_url, timeout=5).json()
        #     if isinstance(mohist_data, dict) and mc_version in mohist_data:
        #         supported_types.append("mohist")
        # except Exception:
        #     pass
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
        
        # 以下内容未实现
        # elif server_type == "bukkit":
        #     url = f"{self.BASE_URL}/bukkit/list/{mc_version}"
        #     bukkit_list = self._get_json(url)
        #     if bukkit_list:
        #         versions = [str(v['version']) for v in bukkit_list if 'version' in v]
        #         versions.sort(key=self._parse_version_string, reverse=True)
        #     # 官方API补充
        #     if not versions:
        #         bukkit_builds_url = f"https://api.getbukkit.org/craftbukkit/versions/{mc_version}"
        #         try:
        #             builds = requests.get(bukkit_builds_url, timeout=8).json()
        #             if isinstance(builds, list):
        #                 versions = [str(b) for b in builds]
        #                 versions.sort(key=lambda x: int(x) if x.isdigit() else x, reverse=True)
        #         except Exception:
        #             pass
        #     if not versions:
        #         self.signals.log_message.emit(f"未找到 {mc_version} 的 Bukkit 核心版本。")
        
        # elif server_type == "paper":
        #     # fill.papermc.io v3 API 获取所有构建号
        #     builds_url = f"https://fill.papermc.io/v3/projects/paper/versions/{mc_version}/builds"
        #     try:
        #         builds_data = requests.get(builds_url, timeout=8).json()
        #         if 'builds' in builds_data and isinstance(builds_data['builds'], list):
        #             versions = [str(b['build']) for b in builds_data['builds'] if 'build' in b]
        #             versions = [str(v) for v in versions]
        #             versions.sort(key=lambda x: int(x), reverse=True)
        #     except Exception:
        #         pass
        #     if not versions:
        #         self.signals.log_message.emit(f"未找到 {mc_version} 的 Paper 核心版本。")
        
        # elif server_type == "spigot":
        #     # 官方API获取所有spigot版本
        #     spigot_builds_url = f"https://api.getbukkit.org/spigot/versions/{mc_version}"
        #     try:
        #         builds = requests.get(spigot_builds_url, timeout=8).json()
        #         if isinstance(builds, list):
        #             versions = [str(b) for b in builds]
        #             versions = [str(v) for v in versions]
        #             versions.sort(key=lambda x: int(x) if x.isdigit() else x, reverse=True)
        #     except Exception:
        #         pass
        #     if not versions:
        #         self.signals.log_message.emit(f"未找到 {mc_version} 的 Spigot 核心版本。")
        
        # elif server_type == "catserver":
        #     # 目录检测，假定文件名格式 CatServer-{mc_version}-{version}.jar
        #     import re
        #     from bs4 import BeautifulSoup
        #     try:
        #         page = requests.get(f"https://download.catserver.cn/{mc_version}/", timeout=8).text
        #         soup = BeautifulSoup(page, "html.parser")
        #         links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
        #         versions = []
        #         for link in links:
        #             # 兼容所有 CatServer jar 文件名
        #             m = re.match(r'CatServer-[^/]+-(.+)\\.jar', link)
        #             if m:
        #                 versions.append(str(m.group(1)))
        #         versions = list(set(versions))
        #         versions = [str(v) for v in versions]
        #         versions.sort(reverse=True)
        #     except Exception:
        #         pass
        #     if not versions:
        #         self.signals.log_message.emit(f"未找到 {mc_version} 的 CatServer 核心版本。")
        
        # elif server_type == "mohist":
        #     # 官方API获取所有mohist版本
        #     mohist_versions_url = f"https://mohistmc.com/api/v2/versions/{mc_version}"
        #     try:
        #         builds = requests.get(mohist_versions_url, timeout=8).json()
        #         if isinstance(builds, list):
        #             versions = [str(b) for b in builds]
        #             versions = [str(v) for v in versions]
        #             versions.sort(reverse=True)
        #     except Exception:
        #         pass
        #     if not versions:
        #         self.signals.log_message.emit(f"未找到 {mc_version} 的 Mohist 核心版本。")

        return versions

    def get_download_url_and_filename(self, mc_version, server_type, core_version_info):
        """
        根据Minecraft版本、服务端类型和核心版本信息获取下载链接和文件名。
        """
        self.signals.log_message.emit(f"正在获取 {mc_version} {server_type} {core_version_info} 的下载链接...")
        download_url = None
        file_name = None

        if server_type == "vanilla":
            # 原版下载链接通常直接用MC版本号
            download_url = f"https://launcher.mojang.com/v1/objects/{core_version_info}/server.jar"
            file_name = f"minecraft_server-{mc_version}.jar"
            self.signals.log_message.emit(f"获取到 Vanilla 官方源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "forge":
            # Forge 通常在其官方网站提供下载
            download_url = f"https://files.minecraftforge.net/maven/net/minecraftforge/forge/{mc_version}/{core_version_info}/forge-{core_version_info}-installer.jar"
            file_name = f"forge-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Forge 官方源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "fabric":
            # Fabric 的下载链接较为复杂，需通过其官方API获取
            download_url = f"https://meta.fabricmc.net/v2/versions/installer/{mc_version}"
            file_name = f"fabric-installer-{mc_version}.jar"
            self.signals.log_message.emit(f"获取到 Fabric 官方源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "neoforge":
            # Neoforge 通常在其官方网站提供下载
            download_url = f"https://github.com/Neoforged/Neoforge-MC/releases/download/{core_version_info}/Neoforge-{core_version_info}.jar"
            file_name = f"neoforge-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Neoforge 官方源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "liteloader":
            # Liteloader 通常在其官方网站提供下载
            download_url = f"https://github.com/LCClass/LiteLoader/releases/download/{core_version_info}/LiteLoader-{core_version_info}.jar"
            file_name = f"liteloader-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Liteloader 官方源下载链接: {download_url}")
            return download_url, file_name

        elif server_type == "optifine":
            # Optifine 的下载链接较为特殊，需通过其官方网站获取
            download_url = f"https://optifine.net/download/OptiFine{mc_version}{core_version_info}.jar"
            file_name = f"optifine-{mc_version}-{core_version_info}.jar"
            self.signals.log_message.emit(f"获取到 Optifine 官方源下载链接: {download_url}")
            return download_url, file_name

        # 以下内容未实现
        # elif server_type == "paper":
        #     # fill.papermc.io v3 API 获取下载链接
        #     build = str(core_version_info)
        #     build_url = f"https://fill.papermc.io/v3/projects/paper/versions/{mc_version}/builds/{build}"
        #     try:
        #         build_data = requests.get(build_url, timeout=8).json()
        #         downloads = build_data.get('downloads', {})
        #         application = downloads.get('application', {})
        #         download_url = application.get('url')
        #         file_name = application.get('name')
        #         if download_url and file_name:
        #             self.signals.log_message.emit(f"获取到 Paper 官方源下载链接: {download_url}")
        #             return download_url, file_name
        #     except Exception as e:
        #         self.signals.log_message.emit(f"Paper 下载信息获取失败: {e}")
        #     return None, None

        # elif server_type == "bukkit":
        #     # 官方API获取下载链接
        #     download_url = f"https://download.getbukkit.org/craftbukkit/craftbukkit-{core_version_info}.jar"
        #     file_name = f"bukkit-{mc_version}-{core_version_info}.jar"
        #     self.signals.log_message.emit(f"获取到 Bukkit 官方源下载链接: {download_url}")
        #     return download_url, file_name

        # elif server_type == "spigot":
        #     # 官方API获取下载链接
        #     download_url = f"https://download.getbukkit.org/spigot/spigot-{core_version_info}.jar"
        #     file_name = f"spigot-{mc_version}-{core_version_info}.jar"
        #     self.signals.log_message.emit(f"获取到 Spigot 官方源下载链接: {download_url}")
        #     return download_url, file_name

        # elif server_type == "catserver":
        #     # 直接拼接CatServer官方目录
        #     download_url = f"https://download.catserver.cn/{mc_version}/CatServer-{mc_version}-{core_version_info}.jar"
        #     file_name = f"catserver-{mc_version}-{core_version_info}.jar"
        #     self.signals.log_message.emit(f"获取到 CatServer 官方源下载链接: {download_url}")
        #     return download_url, file_name

        # elif server_type == "mohist":
        #     # 官方API获取下载链接
        #     download_url = f"https://mohistmc.com/api/v2/download/{mc_version}/{core_version_info}"
        #     file_name = f"mohist-{mc_version}-{core_version_info}.jar"
        #     self.signals.log_message.emit(f"获取到 Mohist 官方源下载链接: {download_url}")
        #     return download_url, file_name

        self.signals.log_message.emit("未能获取到有效的下载链接。")
        return None, None

    def download_file(self, url, dest_folder, file_name):
        """
        下载文件到指定文件夹。
        """
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder) 
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))
            block_size = 1024 
            with open(os.path.join(dest_folder, "temp_file"), 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded_size = file.tell()
                    self.signals.progress_update.emit(int(downloaded_size / file_size * 100))
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
