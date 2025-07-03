# Minecraft 服务端核心下载器

这是一个使用 Python 和 PyQt5 开发的桌面应用程序，用于从下载各种 Minecraft 服务端核心（如 Vanilla, Forge, Fabric, Paper, Spigot 等）。


## 功能

* 选择 Minecraft 游戏版本。
* 选择支持的服务端核心类型。
* 选择具体的核心版本进行下载。
* 显示下载进度和日志信息。

## 目前支持列表
- [x] **Vanilla**: 原版 Minecraft 服务端核心。
- [x] **Forge**: Minecraft Forge 服务端核心。
- [x] **Fabric**: Fabric 服务端核心。
- [x] **NeoForge**: NeoForge 服务端核心。
- [x] **Liteloader**: LiteLoader 服务端核心。
- [x] **Optifine**: OptiFine 下载器（仅限客户端）。
- [ ] **Paper**: Paper 服务端核心。
- [ ] **Spigot**: Spigot 服务端核心。
- [ ] **Bukkit**: Bukkit 服务端核心。
- [ ] **CatServer**: CatServer 服务端核心。
- [ ] **Mohist**: Mohist 服务端核心。

## 目录结构

```
minecraft_server_downloader/
├── src/
│   ├── __init__.py
│   ├── main_app.py        # 主应用程序窗口
│   └── downloader.py      # 下载逻辑和BMCLAPI接口
├── resources/
│   └── icon.ico           # 应用程序图标
├── README.md              # 项目说明
├── requirements.txt       # 项目依赖
└── run.py                 # 启动脚本
```

## 安装与运行

1.  **克隆或下载项目：**
    ```bash
    git clone https://github.com/Origin173/MinecraftServerjarDownloader.git
    cd MinecraftServerjarDownloader
    ```
    （如果你没有使用 Git，请手动创建上述文件和目录结构，并复制内容）

2.  **安装依赖：**
    推荐使用虚拟环境：
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
    然后安装所需的 Python 包：
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行应用程序：**
    ```bash
    python run.py
    ```

## 贡献

欢迎提出问题和贡献代码！

## 感谢
特别感谢 BMCLAPI 提供的 API 支持，使得这个下载器能够顺利运行。

## 许可证
本项目使用 MIT 许可证。请查看 [LICENSE](LICENSE) 文件了解详细信息。
