# 原生 Linux 安装

1. 获取经批准的 Linux portable 包并核对 SHA256。
2. 在 Ubuntu 安装兼容 NVIDIA 驱动；解压包到可写目录。
3. 在该目录运行 bash Setup_First_Run.sh；完成后运行 bash PathPocket.sh。
4. Backend doctor 必须通过后才启动新生成。下载失败保留日志并重试；需要重启时先重启。不要修改科学默认值。

当前 staging 不附未批准二进制和权重；官方来源、版本和 hash 在 third_party 的 lock 文件中。ED2Mol weights 必须从官方来源获取，不能从本仓库假定获得再分发授权。公开安装包下载地址待确认。首次安装不会被本轮本地代码/replay QA 替代。
