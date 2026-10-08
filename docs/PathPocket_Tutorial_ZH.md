# PathPocket 第一次使用教程

本教程面向第一次打开 PathPocket 的研究者。没有合适的 NVIDIA GPU，也可以先用 replay 学习结果浏览。本目录是本地发布候选稿；公开下载地址、作者信息和最终许可证仍待确认。

## 1. 先理解你要做什么

PathPocket 把多个蛋白构象中的局部区域联系起来，再用预训练 ED2Mol 为选定区域生成候选分子。state（状态）是一组输入构象；region family（区域家族）代表相互对应的局部位置；target（生成目标）保存受体和中心坐标。

![真实结构概念总览](assets/tutorial/00_concept.png)

基本顺序是：导入结构 → 建立局部区域对应 → 选择 target → 生成分子 → 查看化学空间 → 定位到蛋白 → 导出坐标。候选区域和生成分子是后续研究的起点，不能直接当作已验证结合位点或配体。

## 2. 安装并启动

**Windows 11：** 从维护者获得已批准的 Windows GPU EasyDeploy 包，完整解压到可写目录，双击 `Setup_First_Run.bat`。首次启用 WSL2 时按提示授予管理员权限；如要求重启，重启后再次运行同一脚本。保持联网，等待私有 scientific runtime、固定版本组件与权重下载和检查结束。以后双击 `PathPocket_GUI.exe`。本次 source ZIP 是源码包，不是 EasyDeploy 安装包。

**原生 Ubuntu：** 解压已批准的 Linux portable 包，在该目录运行 `bash Setup_First_Run.sh`，以后运行 `bash PathPocket.sh`。科学计算使用包内私有 runtime，不使用系统 Conda/Python。先安装兼容的 NVIDIA 驱动。详见 [Windows 安装指南](INSTALL_WINDOWS_ZH.md) 和 [Linux 安装指南](INSTALL_LINUX_ZH.md)。

![真实 Linux 安装下载过程，已裁去身份信息](assets/tutorial/11_linux_install.png)
![真实 Linux 安装完成](assets/tutorial/12_linux_success.png)
![真实 Linux doctor 检查](assets/tutorial/13_linux_doctor.png)

**预期结果：** verification 显示 PASS，并能打开 GUI。上面三张图来自独立 Linux 机器；Windows 安装窗口不同。若提示重启或下载失败，保留日志并重试同一安装脚本。doctor 未通过时先解决环境问题，不要改科学参数绕过错误。

![启动界面](assets/tutorial/01_home.png)

## 3. 创建第一个项目

### 第一步：选择 workspace 并命名

点击 **New project（新建项目）**。根据输入选择单结构、多构象或 repeat/aggregate 模式。填写简短名称，例如 `My_HSA_Project`，选择一个可写工作目录。预览会显示 `20_PROJECTS` 下的新项目路径。工作目录放在程序目录之外，便于升级软件时保留结果。

![新建项目和工作目录](assets/tutorial/02_new_project.png)

**预期结果：** 新项目文件夹和配置文件。若项目重名，请换一个名字保留旧结果。图中灰框是为保护私人路径添加的遮挡，并非软件报错。

### 第二步：导入结构

进入 **Protein States（蛋白状态）**，点击 **Add PDB**，选择 state 和 PDB/CIF 文件。同一 state 下放属于同一条件的构象。练习时可使用公开 HSA 结构；使用本文提供的 HSA 最小示例时，直接打开准备好的项目，不需要自己重新挑选口袋。

![导入后的 HSA 结构](assets/tutorial/03_import_structures.png)

**预期结果：** 表格显示状态名称与结构路径。点击 **Validate（验证）**。如果身份映射存在歧义或置信度不足，应检查输入，不要凭猜测强行对应残基。

### 第三步：设置小规模 Fast Screening

进入 **Fast Screening Settings**。最小示例使用 **10 molecules、seed 42、iteration 2**，包含一个冻结 HSA 区域家族和一个 target。保存并验证。下面的 YAML 区域用于显示配置；普通用户不需要输入 Python 或 Conda 命令。

![10-molecule 参数](assets/tutorial/04_fast_settings.png)

### 第四步：检查环境，再运行

进入 **Run**，先点 **Backend doctor**。验证和环境检查通过后点击 **Run**，观察各阶段名称。已写入分子数不等于实时完成百分比。下面是运行前的真实控件截图；本次打包没有启动新的科学计算。

![运行前的控制页面](assets/tutorial/05_run_monitor.png)

**预期结果：** COMPLETE 状态、保存的 run 目录和结果表。GPU 不可用时应修复驱动/runtime，不要悄悄改用 CPU。失败日志也要保留。

## 4. 看懂结果

下面的截图来自**已归档的 20-molecule HSA replay**，不是新生成的 10-molecule 示例。

![结果概览](assets/tutorial/06_summary.png)

**Regions（区域）**：核对 target、state 和局部区域对应。occurrence 表示输入构象中的出现比例，不代表疾病相关概率。

![Regions 页面](assets/tutorial/07_regions.png)

**Molecules（分子）**：查看生成记录、描述符和 QC 标记。先选择分子，再打开结构位置。clash flag 表示几何检查发现重叠，是结果信息而不是绘图出错。分子 ID 必须和 target、run 一起使用。

![Molecules 页面](assets/tutorial/08_molecules.png)

**Chemical Space（化学空间）**：先选 target，再切换 PCA 或性质图。PCA 表示分子指纹差异，不是亲和力。**View molecules** 跟随当前 target，**Source CSV** 打开对应数据。

![Chemical Space 页面](assets/tutorial/09_chemical_space.png)

**Structure Location（结构位置）**：这是独立结构窗口。拖动旋转、滚轮缩放，用 **Focus region** 观察局部区域。点击 **Export Protein–Ligand Complex**，选择原 run 之外的新导出目录，保存 complex PDB、ligand SDF 和 info JSON。导出保留原坐标，不执行 docking 或能量最小化。

![结构窗口及导出按钮](assets/tutorial/10_structure_export.png)

**预期结果：** 画廊和结构窗口中的分子、target、state ID 一致。导出的 `info.json` 给出源记录和哈希。若 lining mapped 显示未成功映射，不应据此推断该区域不存在。

## 5. HSA 最小示例：有 GPU 时做新计算

使用源码包 `examples/HSA_MINIMAL_10`，或独立的 `03_MINIMAL_WORKING_EXAMPLE`。阅读中英文 README，在新的 workspace 准备项目，再用已安装 GUI 打开 `project.yml`。示例使用 HSA 1N5U chain A 的固定 **RF_0011 / RF_0011_state_B**，请求 10 个分子、seed 42、iteration 2。这是 prepared-target 的小规模流程检查，不等同于重做三结构 discovery benchmark。验收以 expected contract 为准，不要求跨 GPU 分子字节一致。

## 6. Replay：没有 GPU 也能体验

使用独立的 `04_REPLAY_DEMO`。已安装 GUI 中选择 **Open historical run (read-only)**，打开 `20_PROJECTS/HSA_REPLAY/runs/RUN_20260920_165815`。源码用户安装 viewer 依赖后，也可用仓库 `scripts/replay.py` 打开同一 run；该启动器禁止 backend 调用。这里有 20 个 valid unique 分子，其中 19 个通过 clash QC。

依次打开 Results → Molecules，选择 `RF_0011_state_B_M000001` → Structure Location；再到 Chemical Space 选择 `RF_0011_state_B`。把 complex 导出到原 run 之外的新文件夹。**预期结果：** 能交互查看和导出，不启动 ED2Mol。原 run 保持只读。

## 7. NO_TARGETS 不是崩溃

NO_TARGETS 表示选中目标集合为空。运行可以正常 COMPLETE，同时目标数为 0、ED2Mol 实际调用为 0、generation 为 SKIPPED。内置 NO_TARGETS 示例是从现有 GUI 入口运行的可信工程夹具，用于检查零目标流程；它不表示输入蛋白不存在口袋。普通项目自然筛选为空时也会安全结束，但不会启用工程夹具。

## 8. 输出文件在哪里

| 文件或目录 | 用途 |
|---|---|
| `run_manifest.json` | 状态、设置、运行溯源 |
| `03_REGION_DISCOVERY` / `04_REGION_MATCHING` | 检测实例与区域家族 |
| `05_TARGET_SELECTION/targets.json` | target、中心与受体信息 |
| `06_CHEMICAL_CHALLENGE/<target>/raw/output.sdf` | 原始生成分子记录 |
| `molecule_qc.csv` / `07_ANALYSIS` | QC、描述符、身份、聚类和嵌入 |
| `08_REPORT/summary.json` | GUI 使用的结果摘要 |
| 导出 `complex.pdb` | 受体和选定配体坐标 |
| 导出 `ligand.sdf` | 选定分子的原始记录 |
| 导出 `info.json` | 源 ID、哈希和导出信息 |

## 9. 常见问题

| 问题 | 回答 |
|---|---|
| 为什么没有选中区域？ | 先看结构验证和对应结果，再看已记录的选择标准；允许正常空结果。 |
| 为什么有 clash flag？ | heavy-atom 几何 QC 检出了受体或分子内部重叠；结合结构和描述符一起查看。 |
| Qnorm 是什么？能当亲和力吗？ | Qnorm = Qraw/(重原子数 × 密度网格最大值)，是归一化模型密度分数，不是亲和力，也未校准为跨不同 target 的统一排名。 |
| fpocket volume 为什么略有变化？ | 体积估计含随机采样；区域匹配使用中心距离和 lining residue 相似性，volume 是辅助描述符。 |
| 软件做 docking 吗？ | 本 Fast workflow 没有 docking 步骤。 |
| 导出会最小化吗？ | 不会；保留选定记录的原坐标。 |
| 只有 CPU 可以吗？为什么需要 NVIDIA？ | CPU 可以浏览和导出 replay；新的预训练生成需要经过测试的 CUDA/NVIDIA runtime，不会静默 CPU fallback。 |
| 可以用自己的 PDB 吗？ | 可以；先验证身份、状态分组，并保存原文件和映射记录。 |
| 可以处理 amyloid/repeat 吗？ | 选 repeat/aggregate 模式，检查保存的 repeat mapping 和 local unit；真实 7KWZ 示例说明了这一使用方式。 |

## 源码用户补充

在新的 Python 环境执行 `python -m pip install .`，再执行 `python -m pip install -r requirements-viewer.txt`，用 `python scripts/replay.py <replay-run-directory>` 打开结果。源码安装和普通用户 portable 安装是两条路径；上述命令不会下载模型权重。科学生成 runtime 与第三方锁定信息见安装指南。
