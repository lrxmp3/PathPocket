# Windows 安装

1. 从维护者获取经批准的 portable 包并核对 SHA256。源码 ZIP 不是安装包。
2. 完整解压到可写目录；结果 workspace 单独保存。
3. Windows 11 安装 NVIDIA 驱动后双击 Setup_First_Run.bat，按提示启用 WSL2、管理员权限和重启。之后双击 PathPocket_GUI.exe。
4. Backend doctor 必须通过后才启动新生成。下载失败保留日志并重试；需要重启时先重启。不要修改科学默认值。

当前 staging 不附未批准二进制和权重；官方来源、版本和 hash 在 third_party 的 lock 文件中。ED2Mol weights 必须从官方来源获取，不能从本仓库假定获得再分发授权。公开安装包下载地址待确认。首次安装不会被本轮本地代码/replay QA 替代。
