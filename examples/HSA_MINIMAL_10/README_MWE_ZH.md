# HSA minimal example

HSA 1N5U chain A；1 个固定家族 RF_0011；1 个 target RF_0011_state_B；请求 10 个分子，seed 42，iteration 2。

用源码仓库 scripts/run_mwe.py 在新 workspace 准备项目，或由维护者将此示例导入已安装 portable GUI。准备后打开项目，Validate → Backend doctor → Run。此示例依赖完成安装的 GPU scientific runtime；本轮只验证输入、配置和路径，不重新生成。expected/contract.json 是结构性验收条件，不规定逐字节分子输出。


Preparation command from the source repository: `python scripts/run_mwe.py --workspace <new-workspace> --runtime <installed-PathPocket_Linux-root>`. It creates a new `20_PROJECTS/HSA_MINIMAL_10` project and resolves local receptor paths. On Linux/WSL, add `--run` only when you intend to run the installed doctor and generate molecules; this was not executed during packaging.


Preparation command from the source repository: `python scripts/run_mwe.py --workspace <new-workspace> --runtime <installed-PathPocket_Linux-root>`. It creates a new `20_PROJECTS/HSA_MINIMAL_10` project and resolves local receptor paths. On Linux/WSL, add `--run` only when you intend to run the installed doctor and generate molecules; this was not executed during packaging.
