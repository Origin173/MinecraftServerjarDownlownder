# Minecraft 服务端核心下载器

这是一个使用 Python 和 PyQt5 开发的桌面应用程序，用于从多个镜像源下载各种 Minecraft 服务端核心（如 Vanilla, Forge, Fabric, Paper, Spigot 等）。

## ✨ 功能特性

* **🔄 双镜像源支持**: 支持 BMCL API 和 MSL API 两个镜像源，可实时切换
* **📦 广泛的服务端支持**: 支持30+种服务端核心类型的下载
* **🎯 智能版本选择**: 根据选择的 Minecraft 版本自动筛选可用的服务端类型
* **📊 实时下载进度**: 显示详细的下载进度和日志信息
* **🛡️ 完善的错误处理**: 网络异常处理和用户反馈机制
* **🔧 统一接口设计**: UnifiedDownloader 提供一致的API体验

### 🆕 最新功能亮点

* **🎛️ 统一下载器架构**: 一个接口，两种镜像源，无缝切换
* **📋 智能分类系统**: MSL API 提供8大服务端分类，便于选择
* **☕ Java 环境支持**: 显示兼容的 Java 版本信息
* **📢 实时公告系统**: 获取最新的服务维护和更新信息
* **🔒 设备ID管理**: 自动生成和持久化设备标识
* **🎨 现代化UI设计**: 清晰直观的用户界面

## 🚀 支持的镜像源

### BMCL API
- **支持的服务端类型**: Vanilla, Forge, Fabric, NeoForge, OptiFine
- **特点**: 稳定可靠，国内访问速度快，版本齐全（94个Minecraft版本）
- **适用场景**: 常用服务端类型的下载，适合个人开发者

### MSL API V3
- **支持的服务端类型**: 30+种服务端类型，包括所有主流服务端
- **特点**: 功能全面，支持服务端分类、公告查询、Java版本管理
- **独有功能**: 
  - 📢 实时公告查询
  - 📋 服务端分类管理（插件核心、模组核心、原版核心等8大分类）
  - ☕ Java版本查询（Java8, Java11, Java17, Java21）
  - 🎛️ 设备ID管理和持久化

## 📦 支持的服务端类型

### 通过 BMCL API 支持
- [x] **Vanilla**: 原版 Minecraft 服务端核心
- [x] **Forge**: Minecraft Forge 服务端核心
- [x] **Fabric**: Fabric 服务端核心
- [x] **NeoForge**: NeoForge 服务端核心
- [x] **OptiFine**: OptiFine 下载

### 通过 MSL API V3 支持（30+种服务端类型）

#### 🔌 插件核心 (Plugin Cores)
- [x] **Paper**: 高性能的 Spigot 分支
- [x] **Purpur**: Paper 的高性能分支
- [x] **Spigot**: Bukkit 的高性能分支
- [x] **Bukkit**: 经典的插件服务端
- [x] **Folia**: Paper 的多线程分支
- [x] **Leaves**: 基于 Paper 的中文优化服务端
- [x] **Pufferfish**: 高性能的 Paper 分支
- [x] **SpongeVanilla**: Sponge 原版服务端

#### 🔧 插件+模组混合核心 (Plugin & Mod Cores)
- [x] **Mohist**: 高性能的 Mod+插件混合服务端
- [x] **CatServer**: 同时支持 Mod 和插件的混合服务端
- [x] **Arclight**: 支持 Forge/Fabric/NeoForge + 插件
- [x] **Youer**: 中文优化的混合服务端
- [x] **Banner**: Fabric + 插件支持

#### 🎮 模组核心 (Mod Cores)
- [x] **Forge**: 经典的模组服务端
- [x] **NeoForge**: Forge 的新分支
- [x] **Fabric**: 轻量级的模组服务端
- [x] **Quilt**: Fabric 的分支项目

#### 🎯 原版核心 (Vanilla Cores)
- [x] **Vanilla**: 官方原版服务端
- [x] **Vanilla-Snapshot**: 原版快照服务端

#### 📱 基岩版核心 (Bedrock Cores)
- [x] **NukkitX**: 基岩版服务端

#### 🌐 代理核心 (Proxy Cores)
- [x] **Velocity**: 现代化的代理服务端
- [x] **BungeeCord**: 经典的代理服务端
- [x] **Travertine**: BungeeCord 的分支

## 📁 目录结构

```
MinecraftServerjarDownloader/
├── src/
│   ├── __init__.py
│   ├── main_app.py        # 主应用程序窗口
│   └── downloader.py      # 统一下载器 (UnifiedDownloader)
├── resources/
│   └── icon.svg           # 应用程序图标
├── server_cores/          # 下载的服务端核心文件
├── device_id.json         # MSL API 设备ID配置
├── README.md              # 项目说明
├── requirements.txt       # 项目依赖
└── run.py                 # 启动脚本
```

## 🎮 使用说明

### 启动应用程序
运行 `run.py` 启动应用程序：
```bash
python run.py
```

### 操作步骤

1. **🔄 选择下载源**: 
   - 在界面顶部选择 "BMCL API" 或 "MSL API"
   - BMCL API: 适用于常用服务端类型，94个Minecraft版本
   - MSL API: 支持30+种服务端类型，88个Minecraft版本

2. **📋 查看公告（MSL API独有）**:
   - 切换到 MSL API 后可查看官方公告
   - 包含服务器维护、新功能等重要信息

3. **🎯 选择 Minecraft 版本**:
   - 从下拉菜单中选择目标 Minecraft 版本
   - 版本列表会根据选择的下载源自动更新
   - 版本按降序排列（最新版本在前）

4. **🛠️ 选择服务端类型**:
   - 根据选择的 Minecraft 版本，系统会显示支持的服务端类型
   - MSL API 支持服务端分类查看
   - 不同下载源支持的服务端类型可能不同

5. **🔧 选择服务端版本**:
   - 选择具体的服务端版本或构建号
   - 系统会自动筛选出可用的版本

6. **⬇️ 开始下载**:
   - 点击"下载服务端核心"按钮
   - 查看实时下载进度和日志信息
   - 下载完成的文件将保存在 `server_cores` 目录中

### MSL API 独有功能

- **📢 公告查询**: 实时获取MSL官方公告
- **📊 服务端分类**: 按功能分类查看服务端（插件核心、模组核心等）
- **☕ Java版本查询**: 查看支持的Java版本（Java8, Java11, Java17, Java21）
- **🎛️ 设备管理**: 自动生成和管理设备ID
### 📝 特殊说明

- **Fabric 服务端**: 下载的是 Fabric 安装器，需要按照 Fabric 官方文档进行安装
- **网络连接**: 确保网络连接正常，某些下载源可能需要稳定的网络环境
- **版本兼容性**: 不同服务端类型对 Minecraft 版本的支持程度不同
- **设备ID**: MSL API 会自动生成设备ID并保存在 `device_id.json` 中

### 💡 使用技巧

1. **选择合适的镜像源**:
   - **BMCL API**: 适合下载常用服务端类型，稳定性好
   - **MSL API**: 适合需要更多服务端选择和高级功能的用户

2. **版本选择建议**:
   - 生产环境建议使用稳定的发布版本
   - 测试环境可以尝试较新的版本
   - 注意服务端类型与 Minecraft 版本的兼容性

3. **性能优化**:
   - 定期清理 `server_cores` 目录中的旧文件
   - 使用稳定的网络连接以提高下载速度
   - 根据服务器配置选择合适的服务端类型

### 🔧 高级配置

#### 自定义下载目录
默认下载目录为 `server_cores`，如需修改可以在代码中调整：
```python
# 在 main_app.py 中修改
download_dir = "your_custom_directory"
```

#### 设备ID 管理
MSL API 使用设备ID进行身份识别，相关文件：
- `device_id.json`: 存储设备ID的配置文件
- 首次运行会自动生成UUID格式的设备ID
- 如遇到认证问题，删除此文件重新生成即可

## 🚀 安装与运行

### 环境要求
- Python 3.6+
- PyQt5
- requests
- beautifulsoup4
- uuid

### 安装步骤

1. **📥 克隆或下载项目**:
    ```bash
    git clone https://github.com/Origin173/MinecraftServerjarDownloader.git
    cd MinecraftServerjarDownloader
    ```

2. **🔧 安装依赖**:
    推荐使用虚拟环境：
    ```bash
    # 创建虚拟环境
    python -m venv venv
    
    # 激活虚拟环境
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
    
    安装所需的 Python 包：
    ```bash
    pip install -r requirements.txt
    ```

3. **🎮 运行应用程序**:
    ```bash
    python run.py
    ```

## 🛠️ 故障排除

### 常见问题解决方案

#### 1. 程序启动失败 (退出代码 -1073740791)
这通常是由于以下原因导致的：
- **PyQt5 版本问题**: 确保使用兼容的 PyQt5 版本
- **依赖包缺失**: 运行 `pip install -r requirements.txt` 重新安装依赖
- **Python 版本不兼容**: 确保使用 Python 3.6+

**解决方法**:
```bash
# 使用安全启动脚本
python run_safe.py

# 或者重新安装依赖
pip uninstall PyQt5 PyQt5-tools
pip install PyQt5==5.15.9
```

#### 2. 下载功能异常
- **网络连接问题**: 确保网络连接正常
- **API 服务异常**: 尝试切换到另一个镜像源
- **文件权限问题**: 确保程序有写入 `server_cores` 目录的权限

#### 3. MSL API 功能限制
- 某些 MSL API 端点可能暂时不可用
- 设备ID 会自动生成并保存在 `device_id.json` 中
- 如遇到问题，请删除 `device_id.json` 文件重新生成

### 调试模式
如果遇到问题，可以使用调试模式运行：
```bash
python -c "
import sys
sys.path.insert(0, '.')
from src.main_app import MinecraftServerDownloaderApp
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = MinecraftServerDownloaderApp()
window.show()
app.exec_()
"
```


## 🎯 API 状态

| 功能 | BMCL API | MSL API | 状态 |
|------|----------|---------|------|
| Minecraft版本列表 | ✅ (94个) | ✅ (88个) | 完全正常 |
| 服务端类型 | ✅ (动态) | ✅ (30种) | 完全正常 |
| 下载链接 | ✅ 官方链接 | ✅ 镜像链接 | 完全正常 |
| 公告功能 | ❌ 不支持 | ✅ 完全正常 | MSL独有 |
| 服务端分类 | ❌ 不支持 | ✅ 完全正常 | MSL独有 |
| Java版本 | ❌ 不支持 | ✅ 常用版本 | MSL独有 |

## 🤝 贡献

欢迎提出问题和贡献代码！

### 贡献指南
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 问题反馈
- 🐛 Bug 报告: 请提供详细的错误信息和复现步骤
- 💡 功能建议: 欢迎提出新的功能需求
- 📝 文档改进: 帮助完善项目文档

## 🙏 致谢

特别感谢以下项目和服务：
- **BMCL API**: 提供稳定可靠的镜像服务
- **MSL API V3**: 提供丰富的服务端类型和功能
- **PyQt5**: 提供优秀的GUI框架
- **Python 社区**: 提供优秀的开发环境和生态

## 📄 许可证

本项目使用 MIT 许可证。请查看 [LICENSE](LICENSE) 文件了解详细信息。

## 🔮 未来计划

- [ ] 🎨 UI/UX 改进
- [ ] 🔧 更多服务端类型支持
- [ ] 📱 移动端支持
- [ ] 🌐 多语言支持
- [ ] 🔄 自动更新功能
- [ ] 📊 下载统计功能

---

**如果这个项目对你有帮助，请给它一个 ⭐ Star！**
