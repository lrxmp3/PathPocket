# PathPocket

比较蛋白不同构象或重复单元中的对应局部区域，用预训练 ED2Mol 生成候选分子，再查看化学空间、原始结构位置和可追溯导出。

## 能做什么
结合几何和规范残基身份建立区域对应，保留 state/repeat 信息，记录 target、分子与源文件。PathPocket 不重新训练 ED2Mol；生成分子不是已验证 binder，Qnorm 不是亲和力。

## 从哪里开始
- 没有 GPU：使用预计算 HSA replay，浏览分子、化学空间、结构并导出 complex。
- 有兼容 NVIDIA GPU：安装 scientific runtime 后运行单 target、10-molecule HSA 最小示例。
- 第一次使用：按 Windows/Linux portable 安装指南操作；源码 ZIP 不等于二进制安装包。

## 系统与安装
源码使用 Python ≥3.11，界面使用 PySide6 6.8.3；新的生成需要测试过的 CUDA/NVIDIA runtime、官方 ED2Mol weights 和 fpocket。源码安装 `python -m pip install .`，界面依赖 `python -m pip install -r requirements-viewer.txt`。普通用户 portable 安装使用私有 runtime。[Windows](docs/INSTALL_WINDOWS_ZH.md) · [Linux](docs/INSTALL_LINUX_ZH.md)。

## 快速上手
阅读[中英文图文教程](docs/PathPocket_Tutorial_ZH.md)。GUI 打开历史 replay run，选择 RF_0011_state_B → Molecules → 分子 → Structure Location → Export。源码用户可运行 `python scripts/replay.py <run-directory>`。

## 示例、测试与输出
`examples/HSA_MINIMAL_10` 提供公开 HSA 输入和 10-molecule 验收条件；`examples/fixtures` 提供 HSA、7KWZ 与 NO_TARGETS 示例。执行 `python -m pytest tests` 检查工程契约，不需要重新生成分子。完整论文数据与 replay 单独存放。输出包括 run_manifest、区域/target 表、SDF、QC/化学空间 CSV，以及保留原坐标的 PDB/SDF/JSON 导出。

## 引用与许可证
见 `CITATION.cff`；作者信息和软件 DOI 待最终确认。源码许可证确定前不能公开本仓库。第三方组件保持各自许可条款，见 `THIRD_PARTY_NOTICES.md` 和 `third_party/README.md`。[English](README.md)。
