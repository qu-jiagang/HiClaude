# 验证流程

## 1. 本机无硬件验证

```bash
cd /home/midea/GithubRepository/HiClaude
PYTHONPATH=src python3 -m agent_epaper.cli demo
PYTHONPATH=src python3 -m agent_epaper.cli show
PYTHONPATH=src python3 -m agent_epaper.cli show --svg > /tmp/agent-epaper.svg
PYTHONPATH=src python3 -m agent_epaper.server --host 127.0.0.1 --port 8765
```

浏览器打开：

```text
http://127.0.0.1:8765/
```

验收标准：

- 能看到 `Agent Desk`。
- 能看到任务名称、状态、进度条。
- 能看到 Claude Code / Codex 两条额度。
- 修改 CLI 状态后刷新页面能变化。

## 2. PNG 渲染验证

安装 Pillow 后：

```bash
python3 -m pip install pillow
PYTHONPATH=src python3 -m agent_epaper.display --state /tmp/agent-epaper-state.json --screen waveshare_4in2 --output /tmp/agent-epaper.png
```

验收标准：

- PNG 尺寸为 400x300。
- 黑白显示清晰，无文字大面积重叠。

## 3. 树莓派联通验证

在树莓派：

```bash
curl http://电脑IP:8765/state.json
```

验收标准：

- 返回 JSON。
- `task.status_label` 是中文状态。
- `quotas` 中有 Claude Code / Codex。

## 4. 实屏验证

```bash
PYTHONPATH=src python3 -m agent_epaper.display --url http://电脑IP:8765/state.json --screen waveshare_4in2 --once
```

验收标准：

- 屏幕完成一次全刷。
- 断电后内容保留。
- 更新本机状态后再次运行，屏幕内容同步变化。

## 5. 支架验证

用 OpenSCAD 打开：

```text
cad/agent_epaper_stand.scad
```

设置：

- `screen = "4in2"` 或 `screen = "7in5"`
- `part = "all"` 预览整体
- `part = "front"` 导出前框 STL
- `part = "back"` 导出后壳 STL
- `part = "kickstand"` 导出支脚 STL

验收标准：

- 屏幕外形尺寸能放入前框。
- USB 线从背部或侧边留孔穿出。
- 后仰角稳定，桌面不明显晃动。
