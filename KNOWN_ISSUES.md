# Known issues and limitations

- Generated candidates and geometric checks do not establish binding or experimental activity.
- If a report or SDF does not open, check the result folder and the operating system's file associations. Preserve the original run.
- ED2Mol v1.1 weights and the locked `smina.static` are not bundled or downloaded automatically. Their external-asset license scope still needs explicit rightsholder confirmation; a matching user-supplied file does not itself settle that question.
- A native Linux source-run check against one archived v1.0.6 engine failed because the engine directory lacked Git metadata required by provenance collection. The same engine's monitoring script uses a WSL-specific `nvidia-smi` path that was absent on the tested host. A later generation check used a temporary local adapter; unadapted generation with this archived engine is not verified. Preserve the original logs if either error occurs. Engine provenance and a supported solution remain under review.
- See `THIRD_PARTY_NOTICES.md` for component notices and retained license texts.

## 已知问题和限制

- 生成的候选及几何检查结果不能证明结合或实验活性。
- ED2Mol 权重和锁定的 `smina.static` 不随包提供，也不会自动下载；资产授权范围仍需权利人明确，文件哈希一致不代表已获授权。
- 在一次 Linux 源码运行检查中，v1.0.6 归档引擎目录缺少来源记录所需的 Git 元数据，导致任务失败；该引擎的监控脚本还使用了测试主机不存在的 WSL 专用 `nvidia-smi` 路径。后续生成检查使用了临时本机适配，尚未验证该归档引擎在不适配时能正常生成。如遇到这些错误，请保留原始日志。引擎来源和受支持的解决方案仍在核查。
- 第三方组件说明和保留的许可文本见 `THIRD_PARTY_NOTICES.md`。
