# 额度和任务状态采集

## 任务状态

第一版采用显式更新，最稳定：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli task --name "当前任务" --status thinking --progress 20 --detail "正在分析代码"
```

建议在常用 agent 工作流中手动或脚本化调用：

- 开始任务：`thinking` 或 `running`
- 等待用户：`needs_action`
- 完成：`done`
- 失败：`failed`

后续可接入 Claude Code hooks、Codex CLI wrapper、TaskCabin 或你自己的任务队列，只要最终写入同一个 `state.json`。

## 额度

Claude Code 和 Codex 的订阅/会话额度没有稳定公开 API 可保证长期可用，所以第一版不要把项目绑定到网页结构或私有接口。

当前实现提供稳定兜底：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli quota --agent claude --label "Claude Code" --used 42 --limit 100 --reset "明日 08:00"
PYTHONPATH=src python3 -m agent_epaper.cli quota --agent codex --label "Codex" --used 18 --limit 50 --reset "明日 08:00"
```

可扩展采集方式：

- 如果本机安装了可输出 JSON 的用量统计工具，可写一个 cron 定时转换为 `quota` 命令。
- 如果某个 CLI 将剩余额度打印在终端，可以用 wrapper 捕获并更新状态。
- 如果以后官方提供 API，只需要新增 adapter，不需要改屏幕端。

## 状态文件

默认路径：

```text
~/.agent-epaper/state.json
```

可通过环境变量覆盖：

```bash
AGENT_EPAPER_STATE=/tmp/agent-epaper.json PYTHONPATH=src python3 -m agent_epaper.cli demo
```
