# Linux 直接安装

1. 获取经批准的 `.tar.gz` 安装资产，按 `SHA256SUMS.txt` 校验压缩包的 SHA256。
2. 在主机安装兼容的 NVIDIA 驱动。不允许 PathPocket 替换驱动或已有 Conda/GROMACS 环境。
3. 解压到可写目录，支持含空格的路径。保留可执行位和符号链接；如传输工具丢失权限，运行 `chmod +x Setup_First_Run.sh PathPocket.sh Verify_Installation.sh Verify_Package.sh Create_Shortcuts.sh`。
4. 在解压包根目录先运行 `./Verify_Package.sh`，再运行 `./Setup_First_Run.sh`。锁定 runtime 依赖、fpocket 和官方 ED2Mol 权重需要联网获取。
5. 运行 `./Verify_Installation.sh`。所有必需 doctor 检查通过后再做新生成。
6. 用 `./PathPocket.sh` 启动；可选运行 `./Create_Shortcuts.sh`。项目目录与安装目录分开。

GUI 必须显示 v1.0.6。如失败，保留安装/doctor 日志和退出码。源码仓库不是 portable 安装包。当前候选包仍需新的 Linux 直接安装和 GUI 流程验收，不能用旧 Linux 证据代替。见 `KNOWN_ISSUES.md`。
