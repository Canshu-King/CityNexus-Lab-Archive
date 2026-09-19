# Luna Max Overnight Goal 启动与断线恢复

## 推荐启动方式

1. 使用 **原生 Codex 的 Luna Max**，不要用 GPT Web bridge 跑整夜 Goal。
2. 在同一个 CityNexus project 中开一个新的 Codex 窗口，工作目录保持 `D:\moodle\CityNexus`。
3. 不要关闭/清理现有工作树。先让 Goal 自己执行 `git status --short` 和 `git diff --stat`。
4. 把本 Assist ZIP 解压到 CityNexus repo 之外，例如：

   `D:\moodle\CityNexus-Tools\GPT-Assist\Overnight-Agent-Foundation-20260910\`

5. 在 Goal 模式中粘贴 `LUNA_MAX_OVERNIGHT_GOAL.txt` 全文。若 Codex 能直接读取附件，也可以同时把 Assist ZIP 添加给该任务。
6. Goal 首先完成 Solver SRH-01..05；只有 Solver hardening 通过后才允许修改 Agent runtime。
7. Hermes live integration 是 optional。不得为了安装、登录、网络或模型凭证问题阻塞整夜任务。

## 为什么用新窗口

长任务最怕把旧窗口里已经经历很多 compaction / bridge 状态的上下文继续拖着跑。新的原生 Luna Max 窗口共享同一个项目文件，但任务上下文干净，更适合 Goal。

## 断线/Goal 中断恢复

主 Goal 每完成一个阶段必须更新：

`D:\moodle\CityNexus\reports\overnight\GOAL_PROGRESS.md`

如果 Goal 中断，不要从头重跑，也不要 reset 工作树。新开同项目 Luna Max 窗口，粘贴下面这段：

```text
继续 CityNexus Overnight Agent Foundation Goal。

工作目录：D:\moodle\CityNexus

先读取：
- reports\overnight\GOAL_PROGRESS.md
- reports\overnight\00_WORKTREE_BASELINE.txt
- git status --short
- git diff --stat

不要 reset/checkout/clean，不要重新做已经标记 PASS 的 phase。
从 GOAL_PROGRESS.md 中第一个未完成或失败的 phase 接着执行。
继续遵守原 Goal 的 authority、测试 Gate、Hermes optional integration、禁止范围和最终 checkpoint 要求。
如果某个 live external dependency 不可用，标记 SKIPPED_EXTERNAL_DEPENDENCY 并继续其他不依赖任务。
最终仍需生成 CityNexus-Overnight-Agent-Foundation-Checkpoint-20260911.zip 并 fresh-extract 验证。
```

## 早晨不要只看 Goal 最后一条聊天

优先看实际文件和测试：

- `reports\overnight\GOAL_PROGRESS.md`
- `CURRENT_STATUS.md`
- `BLOCKERS.md`
- `TEST_RESULTS.md`
- `CHANGED_FILES.txt`
- 最终 checkpoint ZIP

聊天里的“完成”没有测试证据值钱。这个项目已经为这条朴素事实贡献了足够多 token。
