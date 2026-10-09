# PathPocket

PathPocket 是一套桌面工作流，用于比较蛋白不同构象或重复单元中的对应局部区域、选择代表性计算目标、调用预训练 ED2Mol 生成候选分子，并查看相关化学空间和结构位置。

本仓库提供 PathPocket 的首次公开发布版本 v1.0.6。

[English](README.md)

## 主要功能

- 结合几何和规范残基身份匹配蛋白局部区域，同时保留构象、状态与重复单元信息。
- 通过封装的科学计算流程生成候选分子，并记录目标、分子、源文件和参数来源。
- 查看生成分子的二维结构及化学空间关系。
- 在来源蛋白结构中定位候选分子，并导出保留坐标的 PDB、SDF、JSON、CSV 和报告文件。
- 重新打开已经完成的运行，便于检查和复现。

PathPocket 不重新训练 ED2Mol。生成的候选分子不能视为已获得实验验证的结合分子，Qnorm 也不是结合亲和力测量值。

## 支持的安装方式

PathPocket 支持：

- **Linux 直接安装**：使用 Linux 发行包安装和运行。
- **Windows 11 通过 WSL2 安装和运行**：使用 Ubuntu 24.04 与 WSLg。Windows 与 Linux 共用同一套 Linux 科学计算核心；Windows 包提供 WSL2 安装、启动、快捷方式和文件打开集成。

新分子生成需要兼容的 NVIDIA GPU 与驱动，以及锁定的 CUDA/PyTorch 环境、fpocket 和官方 ED2Mol 资源。发行安装器使用隔离运行环境，不修改用户的 Conda base 环境。

请从 [v1.0.6 Release](https://github.com/lrxmp3/PathPocket/releases/tag/v1.0.6) 下载对应安装包，使用 `SHA256SUMS.txt` 校验后阅读平台指南：

- [Linux 安装指南](docs/INSTALL_LINUX_ZH.md)
- [Windows 11 / WSL2 安装指南](docs/INSTALL_WINDOWS_ZH.md)
- [Linux installation guide](docs/INSTALL_LINUX_EN.md)
- [Windows 11 / WSL2 installation guide](docs/INSTALL_WINDOWS_EN.md)

若要从源码检查或开发，需要 Python 3.11 或更高版本。可用 `python -m pip install .` 安装 Python 包；可选查看器依赖见 `requirements-viewer.txt`。

## 快速入门

1. 按相应平台指南安装 PathPocket，并运行包内安装验证程序。
2. 从正式启动器或桌面快捷方式启动 v1.0.6 GUI。
3. 选择位于软件安装目录之外、可写的项目保存位置。
4. 打开随包示例，确认其预设参数后开始运行。
5. 在“结果”页面查看区域、目标、分子、化学空间、报告和导出文件。

完整操作流程见[中文图文教程](docs/PathPocket_Tutorial_ZH.md)和 [English tutorial](docs/PathPocket_Tutorial_EN.md)。

## 示例

- **Conventional HSA**：标准蛋白区域分析与候选分子生成流程。
- **Repeat Aggregate 7KWZ**：重复或聚集结构的区域对应与分子空间定位。
- **NO_TARGETS**：选中目标为空时的正常工程测试用例；该运行不会调用 ED2Mol，也不会生成分子。
- `examples/HSA_MINIMAL_10`：供 GPU 环境检查使用的精简 HSA 输入和 10 分子预期契约。

可运行 `python -m pytest tests` 检查仓库的单元与流程契约。不同受支持 GPU 环境的生成结果可能有差异，应按文档中的结果契约判断，不要求分子文件哈希完全相同。

## 验证状态

发布验收覆盖了 Linux 直接安装和 Windows 11/WSL2 安装，以及主要 HSA、7KWZ 与 NO_TARGETS 示例流程。各项检查的实际环境和范围见 [Linux 验证记录](docs/VALIDATION_LINUX.md)、[Windows/WSL2 验证记录](docs/VALIDATION_WINDOWS_WSL2.md)和[验证摘要](docs/VALIDATION_STATUS_2026-10-08.md)。这些结果仅适用于记录的配置，不代表所有 Linux 发行版、Windows 配置、GPU 或外部查看软件均已验证。

报告打开限制和仍需外部复测的项目见 [Known issues](KNOWN_ISSUES.md)。

## 引用

使用 PathPocket 时请引用本软件版本；配套论文书目信息公布后，也请引用论文。机器可读的引用信息位于 [`CITATION.cff`](CITATION.cff)。尚未确定的 DOI 与论文信息保持为空，不做推测。

## 许可证与第三方软件

PathPocket 自有源码和文档采用 [MIT License](LICENSE)，版权人为李瑞熙。第三方软件、字体、数据、模型资源和下载的运行组件继续适用各自条款，不因 PathPocket 的许可证而被重新许可。

详见[贡献者](AUTHORS.md)、[第三方声明](THIRD_PARTY_NOTICES.md)、[`LICENSES/`](LICENSES/) 中的许可原文及 [`third_party/README.md`](third_party/README.md)。
