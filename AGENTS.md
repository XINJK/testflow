# testflow.0.1 代理协作协议（全局强制）

本文件是 `testflow.0.1` 项目内所有代理（主代理与子代理）共同遵守的协议。每个代理在开始工作前必须先读本文件与 `standards/artifact-contract.md`。角色专属规则写在各代理自己的 prompt 里；发生冲突时，以本文件为准。

## 1. 路径与目录

所有路径相对项目根目录，工件内统一使用正斜杠。

| 目录 | stage | 文件名片段 | 产出代理 |
|---|---|---|---|
| `artifacts/00-input/` | input | — | 人（投放）；`tools/extract_input.py` 提取 |
| `artifacts/10-requirement/` | requirement | `req` | test-req-analyst |
| `artifacts/20-review/` | review | `review` | test-review-scribe |
| `artifacts/30-testpoints/` | testpoints | `tp` | test-point-designer |
| `artifacts/40-cases-functional/` | func-cases | `tcf` | test-case-writer |
| `artifacts/50-api-contract/` | api-contract | `api` | test-api-analyst |
| `artifacts/60-cases-api/` | api-cases | `tca` | test-api-case-writer |
| `artifacts/70-automation/` | automation | `auto` | test-api-automator |
| `artifacts/90-qa/` | qa | `qa` | test-qa-gatekeeper |

- 原始输入只增不改：文件放 `artifacts/00-input/`，元数据放 `artifacts/00-input/source.md`，提取文本放 `artifacts/00-input/extracted/`。
- 自动化代码与用例数据落在 `workspaces/automation/<run_id>/`；执行日志落在 `artifacts/70-automation/logs/`。
- `artifacts/STATUS.md` 只允许主代理 `testflow` 写入，其余代理只读。
- 每个代理只写自己 stage 的目录，禁止跨目录写工件。
- 派生视图（如 `RUN-*.outline.xmind.md`、`*.xmind.md` 导出）不是工件：无 frontmatter、不进关卡与 STATUS；由 `test-outline-writer` 写入对应阶段目录，其他代理只读勿改。

## 2. 工件文件与命名

- 工件文件名：`RUN-<YYYYMMDD>-<NN>-<片段>.md`，例如 `RUN-20261006-01-req.md`。
- `artifact_id` = 文件名去掉 `.md`，例如 `RUN-20261006-01-req`；`run_id` = `RUN-<YYYYMMDD>-<NN>`。
- `<NN>` 是当日全局递增序号：开工前 `list` 当天已有工件，取未用过的序号；同一次运行的所有阶段共享同一 `run_id`。
- 一个工件一个文件；正文按 `standards/artifact-contract.md` 的对应模板书写。

## 3. 状态机（frontmatter `status`）

```
draft → awaiting-confirm → confirmed
  ↓            ↓
blocked     draft（返工）
confirmed → deprecated（被新 run 取代）
```

- `draft`：代理正在产出，未自检完成。
- `awaiting-confirm`：自检完成，等待人工关卡确认；代理必须用 question 工具或 HANDOFF 明确指出待确认的 `artifact_id`。
- `confirmed`：只有用户在对话中明确回复"确认 <artifact_id>"后，才可把状态改为 `confirmed`，并填写 `confirmed_by`（用户称呼，默认"用户"）与 `confirmed_at`。更新动作由产出代理执行；若确认发生在主代理会话且产出代理不在场，允许主代理 `testflow` 代记（只改 `status/confirmed_by/confirmed_at` 三个字段）。任何代理禁止在未经用户明确确认时自行确认、禁止代用户确认。
- `blocked`：缺关键输入或阻塞问题未决；写明原因与解除条件。
- `deprecated`：仅当新工件 `supersedes` 它时，由产出代理标记。

已 `confirmed` 的工件不可修改。修订 = 新 run 新工件 + `supersedes: [旧 artifact_id]`，正文首行写明"变更点：…"。

## 4. ID 规范

条目 ID 在项目内全局唯一，格式 `<前缀>-<NNN>`（三位补零）。QST 与 ASM 可能由多个阶段产出，格式为 `<前缀>-<来源阶段代码>-<NNN>`（如 `QST-REQ-001`、`QST-API-002`、`ASM-TP-001`）。

| 前缀 | 含义 | 产出阶段 |
|---|---|---|
| REQ | 需求条目 | 10-requirement |
| QST | 疑问 | 各阶段（带来源阶段代码） |
| ASM | 假设 | 各阶段（带来源阶段代码） |
| DEC | 评审决策 | 20-review |
| FP | 功能点 | 30-testpoints |
| TP | 测试点 | 30-testpoints |
| TC-F | 功能测试用例 | 40-cases-functional |
| API | 接口 | 50-api-contract |
| TC-A | 接口测试用例 | 60-cases-api |
| AUTO | 自动化资产 | 70-automation |
| QA | 质检发现 | 90-qa |

Trace 规则：
- 上游引用：本条数据条目依赖的上游条目 ID（如 TP 引用 FP、REQ；TC-A 引用 API、TP）。
- trace 中引用的每个 ID 必须真实存在于对应工件的正文条目表中，禁止幽灵 ID。
- 只能引用状态为 `confirmed` 或当前 run `draft/awaiting-confirm` 的工件；`deprecated` 工件及其条目不可引用。
- `trace.downstream` 一律留空、禁止手写；跨阶段影响面由 `test-qa-gatekeeper` 在 90-qa 工件的 `affected_ids` 中计算（gatekeeper 只读，不回填被检工件）。

## 5. 来源引用格式（防幻觉底线）

任何事实性内容（需求描述、字段、约束、错误码、期望结果、业务规则）都必须可回溯：

```
来源列格式：<文件相对路径>#<锚点> | "<原文逐字摘录，≤120字，省略用 …>"
锚点规则：PDF → #p<页码>；Word → #P<段落序号>；md/txt → #L<行号>
示例：00-input/extracted/prd.md#p3 | "订单提交后 30 分钟内未支付自动取消"
```

引用必须来自 `artifacts/00-input/` 下的原文或提取文本；禁止引用模型记忆、网络传言、推测结论。

## 6. 防幻觉铁律

1. 没有来源的事实：删除，或降级为 ASM（`needs_confirmation: true`）。
2. 禁止编造需求条文、业务规则、字段、错误码、阈值、接口、期望结果、测试数据。
3. 上游缺失或说法冲突：写入 QST（阻塞则标 `blocking: true`），保留双方原话，禁止自行取舍。
4. 不确定必须显式化（QST/ASM/blocked），禁止静默假设。
5. 期望结果必须可观察、可判定；禁止"功能正常/符合预期"式空断言。
6. 覆盖率必须按规则重算，`uncovered` 要么为空，要么逐条给出原因与处理建议。
7. 只报告真正读到的内容；禁止根据文件名、标题或直觉推断工件内容。
8. 不越权：不替业务方拍板、不修改上游工件、不修改 `00-input` 原文、不写其他代理的目录。

## 7. 人工关卡

| 关卡 | 确认对象 | 通过后才能 |
|---|---|---|
| G1 需求与问题清单 | `10-requirement` 工件 | 进入评审/测试点设计 |
| G2 决策与测试点 | `20-review`（若存在）+ `30-testpoints` 工件 | 进入用例编写 |
| G3 用例 | `40-cases-functional`（若存在）+ `60-cases-api`（若存在）工件 | 进入自动化/交付 |

- 关卡前必须先跑 `test-qa-gatekeeper`；QA 结论为 `rework` 时不得送审。
- 代理把工件置为 `awaiting-confirm` 后，在对话中给出确认清单（ID + 一句话摘要 + 未决问题），等待用户回复"确认 <artifact_id>"。
- 代码资产不做逐行人工关卡：由真实执行日志 + QA 兜底。

## 8. 手动调用契约

- 每个子代理都可被用户 `@` 直接点名，或被主代理调度；两种方式行为一致。
- 每个代理在 prompt 中声明"最小输入 / 理想输入"。最小输入不满足时：先用 question 工具询问用户是否降级运行；用户同意降级才可继续，产物必须标 `draft`，缺项写入 ASM 且 `coverage.uncovered` 显式列出；用户不同意则返回 `blocked`。
- 调度方在任务提示中必须包含：`run_id`、输出目录、精确的上游工件相对路径、本次目标与约束，并要求子代理"先落盘骨架、按模块/条目分批补齐"（见 §12）。
- 禁止为了"跑通流程"而虚构缺失输入。

## 9. Profile（自动化技术栈档案）

- `test-api-automator` 只按 `profiles/<name>.yaml` 指定的框架约定产出，不做主观猜测。
- 只有 `status: confirmed` 的 profile 可用；未确认时 automator 返回 `blocked` 并提示先确认档案（关卡见 test-framework-profiler）。
- 新框架接入 = 让 `test-framework-profiler` 对目标仓库建档 → 用户确认 → 使用；不依赖任何模型记忆。
- AUTO 工件 frontmatter 的 `source_artifacts` 中必须包含 profile 路径，并在正文记录 `profile: <name>@sha256:<hash>`。

## 10. 提交前自检（每个代理 HANDOFF 之前执行）

1. frontmatter 字段齐全、status 合法、artifact_id 与文件名一致。
2. 条目 ID 唯一且格式正确；trace 引用的 ID 全部真实存在。
3. 每条事实有来源或已降级为 ASM；无来源内容为零。
4. coverage 已按 expected/covered/uncovered 重算。
5. 正文表格列与 `standards/artifact-contract.md` 模板一致。
6. 未触碰他人目录、未修改 00-input、未手写 downstream。

## 11. 固定交接回复

每次任务结束，最后输出：

```
HANDOFF
- artifact: <工件相对路径>
- id: <artifact_id>
- status: draft | awaiting-confirm | confirmed | blocked | deprecated
- counts: <条目统计，如 REQ=12, QST=4, ASM=2>
- blocking_questions: [<ID 列表>]
- coverage: expected=<n>, covered=<n>, uncovered=<n>
- gate: pass | conditional | rework        # 仅 QA 工件
- next: <建议的下一步代理 / 等待人工确认 / 无>
```

## 12. 落盘纪律（运行时硬约束）

- 本环境单次生成超过约 120 秒会被截断且丢失工具调用：大工件必须分块落盘。
- 强制顺序：① 先 write 骨架（frontmatter + 小节标题）；② 再用 edit 分批补齐，每次 edit 追加 ≤4 行条目、总长 ≤600 字符；条目行保持紧凑。
- 禁止把工件正文放进聊天回复；结束消息只输出 HANDOFF。
- 若一轮生成返回为空/失败：缩小批次（降到 2 行）重试，不得放弃落盘。
- 确认类小改动（status/confirmed_by/confirmed_at）合并为一次 edit 完成。
- 所有代理：每步只处理一个模块/一批条目（先落盘、再规划下一步）；禁止在单步内起草整篇工件。
- 调度兜底：子代理返回为空或未落盘时，调度方（`testflow`）先以"缩小批次、先落盘骨架"的提示重试一次；仍失败再上报用户。
