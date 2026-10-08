# testflow.0.1

面向测试全流程的 opencode 多代理方案：需求理解 → 评审 → 测试点 → 功能用例 / 接口用例 → 自动化。核心原则是**文件即契约、条目可溯源、人工关卡显式化**，每个子代理都可被单独点名使用。

## 目录

```
.opencode/agents/   1 个主代理（testflow）+ 10 个子代理
AGENTS.md           全局协作协议（所有代理必读）
standards/          工件契约 + 测试设计规范（从 prd_to_xmind 复制）
profiles/           自动化框架档案（adv1 = 接口自动化进阶1）
tools/              extract_input.py（文档提取）/ export_xlsx.py（用例导出）
artifacts/          00-input 输入 | 10~70 各阶段工件 | 90-qa | STATUS.md
workspaces/         自动化代码与用例数据落点
```

## 快速开始

1. 用 opencode 打开本目录，Tab 切到 **testflow** 主代理（或直接 `@test-req-analyst` 单跑某环节）。
2. 把 PRD/接口文档放进 `artifacts/00-input/`，补全 `artifacts/00-input/source.md`。
3. 提取文本：`python tools/extract_input.py`（PDF → `#p页码`，Word → `#P段落`，md/txt → `#L行号`）。
4. 对 testflow 说「盘点现状，开始跑需求分析」；它会建议下一步，你同意后调用子代理。

## 常用手动调用

```
@test-req-analyst 读取 artifacts/00-input/extracted/xxx.md，走标准流程
@test-api-analyst 分析 artifacts/00-input/xxx-openapi.json
@test-api-case-writer 基于 50-api-contract 最新工件生成 TC-A
@test-api-automator 基于 60-cases-api 最新工件 + profiles/adv1.yaml 执行
@test-qa-gatekeeper review 模式检查 30-testpoints 最新工件
@test-framework-profiler 给 C:/path/to/new-framework 建档
```

## 人工关卡（G1/G2/G3）

- 关卡前必须由 `test-qa-gatekeeper` 检查，`rework` 不得送审。
- 代理把工件置为 `awaiting-confirm` 并在对话中给出清单；你回复「确认 <artifact_id>」后才变为 `confirmed`，已确认工件不可改，修订走新 run + `supersedes`。

## 自动化档案

- 默认档案 `profiles/adv1.yaml`（对齐 `接口自动化进阶1`：Excel 驱动 + pytest + 软断言 + allure）。`status: confirmed` 前 automator 拒绝执行。
- 新框架接入：`@test-framework-profiler` 建档 → 你确认 → 使用；不需要模型"记住"任何框架。
- 生成的用例数据/脚本默认落在 `workspaces/automation/<run_id>/`；并入真实仓库需在 `APPLY.md` 中确认后手动执行（或显式授权写 `target_repo`）。

## 约束

- 原始输入只增不改；每个代理只写自己的目录；`artifacts/STATUS.md` 由主代理独占。
- 防幻觉底线：每条事实带来源摘录，下游引用必须真实存在的上游 ID，不确定必须落到 QST/ASM/blocked。
