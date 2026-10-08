# 工件契约（artifact-contract）

本文件定义所有工件的统一 frontmatter 与各阶段正文模板。模板中 `|` 表格的列顺序与列名不得增删（新增列需先改本文件并重跑 QA）。所有路径使用正斜杠。

## 1. 统一 frontmatter（所有阶段）

```yaml
---
schema_version: "0.1"
artifact_id: RUN-20261006-01-req      # 与文件名一致
run_id: RUN-20261006-01
stage: requirement                    # 见 AGENTS.md 目录表
status: draft                         # draft | awaiting-confirm | confirmed | blocked | deprecated
created_by: test-req-analyst
created_at: 2026-10-06T10:00:00+08:00
confirmed_by:                         # confirmed 时填写，默认"用户"
confirmed_at:                         # confirmed 时填写，ISO8601
source_artifacts:                     # 消费的上游文件相对路径
  - artifacts/00-input/source.md
supersedes: []                        # 被本工件取代的旧 artifact_id
trace:
  upstream: []                        # 本工件消费的上游条目 ID（如 REQ-001、TP-007）
  downstream: []                      # 一律留空；影响面见 90-qa 工件的 affected_ids
coverage:
  expected: []                        # 按阶段规则定义的上游条目 ID 全集
  covered: []                         # 实际覆盖到的上游条目 ID
  uncovered: []                       # expected 中未覆盖的 ID；必须逐条说明或为空
gate:                                 # 仅 90-qa 工件使用：pass | conditional | rework
---
```

## 2. 阶段正文模板

### 2.1 requirement（`10-requirement/`，代理 test-req-analyst）

```markdown
## 需求清单
| ID | 标题 | 描述 | 模块 | 优先级 | 依赖 | 歧义 | 来源 |
|---|---|---|---|---|---|---|---|
| REQ-001 | ... | ... | ... | P0/P1/P2 | REQ-000 或 - | none/minor/major | 路径#锚点 \| "原文摘录" |

## 疑问清单
| ID | 问题 | 关联REQ | 类别 | 是否阻塞 | 建议解答人 | 来源 |
|---|---|---|---|---|---|---|
| QST-REQ-001 | ... | REQ-001 | 业务规则/字段/流程/其他 | 是/否 | 产品/开发/业务 | ... |

## 假设清单
| ID | 假设 | 依据 | 是否需确认 |
|---|---|---|---|
| ASM-REQ-001 | ... | ... | 是 |
```

coverage：`expected` = 本文工件中 REQ ID 全集；`covered` = 有来源且歧义不为 major 的 REQ；`uncovered` = 无来源被拒收的条目说明。
规则：粒度 = 一个可独立验收的功能行为；`歧义=major` 必须对应一条 `是否阻塞=是` 的 QST。

### 2.2 review（`20-review/`，代理 test-review-scribe）

```markdown
## 会议信息
- 会议主题：
- 时间：
- 参会人：
- 纪要来源：<文件路径#锚点 | "摘录">

## 会前问题清单            <!-- mode: prepare 时填写 -->
| QST | 问题 | 关联REQ | 建议提问对象 |
|---|---|---|---|

## 评审决策                <!-- mode: decision 时填写 -->
| ID | 对应QST | 对应REQ | 决策 | 理由 | 负责人 | 状态 | 来源 |
|---|---|---|---|---|---|---|---|
| DEC-001 | QST-REQ-001 | REQ-001 | ... | ... | ... | final/tentative | ... |

## 遗留问题
| QST | 问题 | 未决原因 | 下一步 |
|---|---|---|---|
```

frontmatter 增加 `mode: prepare | decision`。规则：每条 QST 必须出现在"评审决策"或"遗留问题"中；`final` 决策必须有来源（纪要摘录或"用户口述 + 时间"）。

### 2.3 testpoints（`30-testpoints/`，代理 test-point-designer）

```markdown
## 功能点清单
| ID | 名称 | 关联REQ | 优先级 | 来源 |
|---|---|---|---|---|
| FP-001 | ... | REQ-001 | P0 | ... |

## 测试点清单
| ID | 名称 | 关联FP | 类型 | 设计方法 | 接口标记 | 优先级 | 前置条件 | 测试数据提示 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| TP-001 | ... | FP-001 | 功能/边界/异常/场景/状态 | 正向/反向/边界值/等价类/场景法/状态 | 是/否 | P0 | ... | ... | ... |
```

coverage：`expected` = 上游 REQ ID 全集；`covered` = 被至少一个 FP 关联的 REQ；另在正文 `## 覆盖统计` 列出每个 FP 的 TP 数。规则参见 `standards/test-design-standard.md`：每个可校验输入至少一条异常/边界 TP；`接口标记=是` 的 TP 交由 api 分支消费。

### 2.4 func-cases（`40-cases-functional/`，代理 test-case-writer）

```markdown
## 用例清单
| ID | 标题 | 关联TP | 优先级 | 设计方法 | 前置条件 | 步骤与预期 | 测试数据 | 后置条件 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| TC-F-001 | ... | TP-001 | P0 | 正向 | ... | 1. 操作 → 预期：...<br>2. 操作 → 预期：... | ... | ... | ... |
```

coverage：`expected` = TP 中 `接口标记=否` 的 ID 全集；`uncovered` 必须逐条说明。
规则：每条"预期"可观察可判定；测试数据无法从上游得到时写 `<TBD:说明>` 并登记 QST；不得写"功能正常"。

### 2.5 api-contract（`50-api-contract/`，代理 test-api-analyst）

```markdown
## 接口清单
| ID | 名称 | 方法 | 路径 | 鉴权 | 请求头 | 请求参数 | 响应 | 错误码 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| API-001 | ... | POST | /api/... | ... | ... | 字段名(类型,必填,约束,示例) | ... | 错误码(含义) | ... |

## 接口疑问
| ID | 问题 | 关联API | 类别 | 是否阻塞 | 来源 |
|---|---|---|---|---|---|
| QST-API-001 | ... | API-001 | 字段/错误码/鉴权/流程 | 是/否 | ... |
```

规则：字段、错误码逐字摘录并带来源；文档中的示例值不算约束，约束缺失写 `<未说明>` 并登记 QST；文档自相矛盾时保留双方原话并登记阻塞 QST。

### 2.6 api-cases（`60-cases-api/`，代理 test-api-case-writer）

```markdown
## 用例清单
| ID | 标题 | 关联API | 关联TP | 类型 | 请求方法与路径 | 请求数据 | 断言 | 测试数据 | 前置条件 | 清理 | 来源 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-A-001 | ... | API-001 | TP-007 或 - | 正向/参数异常/边界/鉴权/错误码/流程 | POST /api/... | 字段=值<br>... | 状态码=200<br>code==0<br>data.token 存在 | ... | ... | ... | ... |
```

coverage：`expected` = API ID 全集（若上游给了 `接口标记=是` 的 TP，则并入其 ID）；
规则：路径、参数、错误码只能来自 api-contract 工件；未知写 `<TBD>` 并登记 `QST-API-xxx`；期望与文档冲突时保留冲突并登记阻塞 QST。

### 2.7 automation（`70-automation/`，代理 test-api-automator）

```markdown
## 执行档案
- profile: <name>@sha256:<hash>
- 目标仓库: <target_repo 或 "workspaces 隔离输出">
- 运行命令: <实际执行命令>

## 自动化资产
| ID | 关联TC-A | 文件路径 | 类型 | 状态 | 失败原因 |
|---|---|---|---|---|---|
| AUTO-001 | TC-A-001 | workspaces/automation/<run_id>/... | data/code | pending/passing/failing/blocked | ... |

## 执行报告
| 命令 | 通过 | 失败 | 跳过 | 日志路径 |
|---|---|---|---|---|
| pytest ... | 0 | 0 | 0 | artifacts/70-automation/logs/... |
```

coverage：`expected` = TC-A ID 全集；`uncovered` = 未实现自动化的 TC-A 及原因。
规则：没有真实运行日志不得标 `passing`；禁止篡改断言求绿；密钥只走环境变量；profile 未 confirmed 时返回 blocked。

### 2.8 qa（`90-qa/`，代理 test-qa-gatekeeper）

```markdown
## 检查结果
| 规则 | 结果 |
|---|---|
| envelope | pass/fail |
| id_unique | ... |
| trace_integrity | ... |
| source_citation | ... |
| coverage | ... |
| contradiction | ... |
| fabrication_risk | ... |
| boundary | ... |
| status_transition | ... |
| id_namespace | ... |
| qst_resolution | ... |

## 发现
| ID | 严重级 | 工件 | 目标ID | 规则 | 证据 | 修复建议 |
|---|---|---|---|---|---|---|
| QA-001 | blocker/major/minor | 路径 | TP-007 | source_citation | ... | ... |

## 影响面                     <!-- impact 模式 -->
- changed_ids: [...]
- affected_ids: [...]
- closure_verified: true/false
```

规则：任一 blocker → `gate: rework`；仅 major → `conditional`；无 blocker 且无 major → `pass`。每条发现必须给出可定位证据。

## 3. 阶段间映射速查

| 上游 | 下游 | 传递字段 |
|---|---|---|
| REQ | FP、TP | 关联REQ 列 / trace.upstream |
| QST | DEC、遗留问题 | 对应QST 列 |
| FP | TP | 关联FP 列 |
| TP（接口标记=是） | TC-A | 关联TP 列 |
| TP（接口标记=否） | TC-F | 关联TP 列 |
| API | TC-A | 关联API 列 |
| TC-A | AUTO | 关联TC-A 列 |
| 任意工件 | QA | 文件路径 + 条目 ID |
