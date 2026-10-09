# Windows 11 + WSL2 安装

PathPocket 不是 Windows 原生计算程序。本包通过 Ubuntu 24.04 + WSL2/WSLg 安装并启动共用 Linux 核心。

1. 解压前，对**原始 ZIP**按 `SHA256SUMS.txt` 校验 SHA256。
2. 完整解压到可写目录。支持空格和 Unicode/中文路径；不要在 ZIP 预览窗口内运行脚本。
3. 双击 `Test_Package_Preflight.bat`，只有看到 `Package preflight: PASS` 才继续。
4. 双击 `Setup_First_Run.bat`。安装器可能请求管理员权限执行 `wsl.exe --install -d Ubuntu-24.04`。如提示 `RESTART_REQUIRED`，重启 Windows，打开一次 Ubuntu 完成 Linux 用户名/密码初始化，然后重新运行同一脚本。
5. 安装过程会按嵌套 Linux 包中的锁定记录下载依赖、fpocket 和 ED2Mol 权重，需要联网。它不安装 Windows/Linux NVIDIA 驱动，不修改 Conda/base 或 GROMACS 环境。
6. 运行 `Verify_Installation.bat`，再运行 `Create_Desktop_Shortcut.bat`。以后点击该脚本创建的快捷方式，或运行 `Launch_PathPocket.bat`。
7. 项目目录与安装目录分开。GUI 必须显示 v1.0.6。

如失败，保留 `diagnostics` 目录、截图、准确退出码和复现步骤。“打开文件”失败不等于报告或 SDF 未生成；请同时核对 run 目录实际文件，并记录 Windows 是否关联 SDF 查看器。候选版边界见 `KNOWN_ISSUES.md`。

GPU 检查使用 `wsl -d Ubuntu-24.04 -- nvidia-smi`（或官方 WSL shim）。只安装兼容的 Windows NVIDIA 驱动，不要在 WSL 内安装 Linux 显示驱动。
