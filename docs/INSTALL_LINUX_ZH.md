# Linux 直接安装

1. 获取经批准的 `.tar.gz` 安装资产，按 `SHA256SUMS.txt` 校验压缩包的 SHA256。
2. 在主机安装兼容的 NVIDIA 驱动。不允许 PathPocket 替换驱动或已有 Conda/GROMACS 环境。
3. 解压到可写目录。Linux 下尚未确认所有安装路径和项目路径的兼容性；已观察到的 fpocket 空格路径及过长输入路径限制见 `KNOWN_ISSUES.md`。保留可执行位和符号链接；如传输工具丢失权限，运行 `chmod +x Setup_First_Run.sh PathPocket.sh Verify_Installation.sh Verify_Package.sh Create_Shortcuts.sh`。
4. 先自行准备具有适当使用许可的 ED2Mol 权重压缩包和 smina 文件，分别将 `PATHPOCKET_ED2MOL_WEIGHTS_ARCHIVE` 和 `PATHPOCKET_SMINA_BINARY` 环境变量设为本机文件路径。两项资产的具体许可范围仍待确认，哈希匹配并不证明获授权；程序不会自动下载这两项。在解压包根目录先运行 `./Verify_Package.sh`，再运行 `./Setup_First_Run.sh`。其他锁定 runtime 依赖和 fpocket 需要联网获取。
5. 运行 `./Verify_Installation.sh`。所有必需 doctor 检查通过后再做新生成。
6. 用 `./PathPocket.sh` 启动；可选运行 `./Create_Shortcuts.sh`。项目目录与安装目录分开。

GUI 必须显示 v1.0.7。如失败，保留安装/doctor 日志和退出码。源码仓库不是 portable 安装包。当前候选包仍需新的 Linux 直接安装和 GUI 流程验收，不能用旧 Linux 证据代替。见 `KNOWN_ISSUES.md`。
