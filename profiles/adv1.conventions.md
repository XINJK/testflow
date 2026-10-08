# adv1 框架约定（接口自动化进阶1）

每条结论附证据；`file:line` 指目标仓库（`profiles/adv1.yaml` 的 `target_repo`）内文件。

## 1. 运行方式

- 主命令：`python run.py` → `pytest.main(["-vs", "./testcases/test_runner.py", "--alluredir", "./report/json_report", "--clean-alluredir"])` 后生成 HTML（`run.py:7-8`）。
- 备用：`python -m pytest`（`pytest.ini` 仅配置日志，无 addopts）。
- 执行单元：`testcases/test_runner.py` 单一 `TestRunner.test_case`，`@pytest.mark.parametrize("case", data)` 逐行驱动（`testcases/test_runner.py:21-22`）。
- 顺序敏感：用例共享全局 `all`（`testcases/test_runner.py:26` 用 `eval(Template(str(case)).render(all))` 渲染），依赖前序提取变量；不要打乱现有行序。

## 2. 用例数据（Excel）

- 文件 `data/测试用例.xlsx`，Sheet `Sheet1`（`utils/excel_utils.py:7-8`）。
- 表头读第 2 行，数据从第 3 行起，`is_true` 为真值才执行（`utils/excel_utils.py:11-14`）。
- 单元格为 Python 字面量字符串（dict/tuple/list），运行时 `eval`/`ast` 解析。
- 列（第 2 行）：`id, feature, story, title, method, path, headers, params, data, json, files, check, expected, sql_check, sql_expected, jsonExData, sqlExData`。
- URL 拼接：`url = BASE_URL + case["path"]`（`utils/case_analyse.py:12`）。
- 模板变量：`{{var}}`，变量来自 `jsonExData`/`sqlExData` 提取结果（`testcases/test_runner.py:26`）。
- 验证码：单元格内可调用 `dddd_ocr_text("...")`（`utils/data_preprocessor.py:8`）。

## 3. 断言

- `check` 为空时用 `expected` 做子串断言；非空时为 dict：`{status_code, code, str, type, time}`（`utils/base_assert.py:39-68`）。
- 软断言 `pytest.assume`，单条失败不中断后续行（`utils/base_assert.py:43` 等）。
- `type` 支持 `{check_name, expected_type, index}`，`index=="all"` 或整数（`utils/base_assert.py:51-64`）。
- DB 断言/提取通过 `sql_check`/`sql_expected`/`sqlExData`（`utils/send_request.py:13` 之后链路 + `utils/database.py`）。

## 4. 数据清理

- 会话结束自动执行清理 SQL（`conftest.py:8-13`），SQL 常量在 `config/config.py:13-16`。
- 新增会写库/留痕的用例：必须同步向 `config/config.py` 增加清理语句并挂到 `conftest.py` 的 `destroy_data`；不改动既有 SQL。

## 5. 配置与安全

- `BASE_URL`、`EXCEL_FILE`、`SHEET_NAME`、DB 连接均为硬编码（`config/config.py:2-4` 与 DB_* 常量）；无环境切换机制。
- 密钥/口令不写入工件与日志；沿用仓库既有本地配置，不新增明文凭据。

## 6. 新增用例的兼容写法（automator 必读）

1. 默认在 `workspaces/automation/<run_id>/` 生成：`cases.xlsx`（同样列结构）或逐行数据文件 + 变更说明 `APPLY.md`（列出要追加到 `data/测试用例.xlsx` 的行、要追加的清理 SQL、受影响文件）。
2. 仅当用户显式设置写入目标时，才允许写 `target_repo`（external_directory: ask）。
3. 断言只覆盖 TC-A 中已声明的期望；不得为“跑绿”删改断言。
4. 运行日志必须原样归档到 `artifacts/70-automation/logs/`；未真实运行不得标 `passing`。
