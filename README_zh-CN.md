# PathPocket

比较蛋白不同构象或重复单元中的对应局部区域，用预训练 ED2Mol 生成候选分子，再查看化学空间、原始结构位置和可追溯导出。

## 能做什么
结合几何和规范残基身份建立区域对应，保留 state/repeat 信息，记录 target、分子与源文件。PathPocket 不重新训练 ED2Mol；生成分子不是已验证 binder，Qnorm 不是亲和力。

## 从哪里开始
- 没有 GPU：使用预计算 HSA replay，浏览分子、化学空间、结构并导出 complex。
- 有兼容 NVIDIA GPU：安装 scientific runtime 后运行单 target、10-molecule HSA 最小示例。
- 第一次使用：按 Windows/Linux portable 安装指南操作；源码 ZIP 不等于二进制安装包。

## 运行架构与安装

PathPocket 只有一套 Linux 科学计算核心，提供两种安装方式：Linux 直接安装，以及 Windows 11 上通过 Ubuntu 24.04 + WSL2/WSLg 安装。Windows 包**不是 Windows 原生科学计算程序**；Windows 脚本负责部署、启动同一 Linux 核心，并在需要时将文件打开请求交给 Windows。

源码使用 Python ≥3.11，GUI 使用 PySide6 6.8.3。新生成还需要兼容的 NVIDIA 驱动、锁定的 CUDA/PyTorch 环境、fpocket 和官方 ED2Mol weights。portable 安装使用隔离 runtime，不修改用户 Conda base。[Windows 11 + WSL2 指南](docs/INSTALL_WINDOWS_ZH.md) · [Linux 直接安装指南](docs/INSTALL_LINUX_ZH.md)。

## 快速上手
阅读[中英文图文教程](docs/PathPocket_Tutorial_ZH.md)。GUI 打开历史 replay run，选择 RF_0011_state_B → Molecules → 分子 → Structure Location → Export。源码用户可运行 `python scripts/replay.py <run-directory>`。

## 示例、测试与输出
`examples/HSA_MINIMAL_10` 提供公开 HSA 输入和 10-molecule 验收条件；`examples/fixtures` 提供 HSA、7KWZ 与 NO_TARGETS 示例。执行 `python -m pytest tests` 检查工程契约，不需要重新生成分子。完整论文数据与 replay 单独存放。输出包括 run_manifest、区域/target 表、SDF、QC/化学空间 CSV，以及保留原坐标的 PDB/SDF/JSON 导出。

## 验证状态与已知边界

当前候选版保持论文基线 v1.0.6 的 GUI、流程、报告模板和科学参数。历史 Ubuntu 22.04/RTX 3080 Ti 证据属于旧 Linux 包，并明确记录了当时 NO_TARGETS 未修复，不能作为新候选包的通过证据。Windows 11/WSL2 R1 证据验证了安装与 HSA、7KWZ、NO_TARGETS 主流程，但直接打开报告按钮失败。当前源码含针对该问题的最小修复，仍待新一轮外部实机验证。详见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md) 和分平台验证记录。

## 引用与许可

PathPocket 自有源码与文档采用 [MIT License](LICENSE)，版权人为李瑞熙。第三方软件、字体、数据和模型资产继续适用各自条款；根许可证不会重新许可这些内容。使用 PathPocket 时请引用本软件；配套论文发表后再补入真实书目信息和 DOI，不预造尚未确定的信息。见[第三方声明](THIRD_PARTY_NOTICES.md)、`LICENSES/` 中保留的许可原文和 `third_party/README.md`。[English](README.md)。
