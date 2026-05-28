# hiClaude 墨水屏状态牌

这是一个给 Claude Code / Codex 任务状态和额度做桌面展示的电子墨水屏项目，目标硬件是 LilyGo `T5-ePaper-S3 4.7"`。

项目目前包含两部分：

- 电脑端 Python 状态服务：维护任务、额度、提示信息，并提供 `state.json`、`screen.svg` 和浏览器预览。
- LilyGo 固件：连接 Wi-Fi，访问电脑端状态服务，解析 JSON，并刷新 960x540 墨水屏。

## 硬件

目标板子：

```text
LilyGo T5-ePaper-S3 4.7"
ESP32-S3R8
16MB Flash
8MB OPI PSRAM
960x540 e-paper
```

本机已识别到的串口：

```text
/dev/cu.usbmodem1301
```

本机当前局域网 IP：

```text
192.168.31.127
```

已验证的状态服务地址：

```text
http://192.168.31.127:18765/state.json
```

本地参考文件：

- `docs/index.html`
- `projects/epaper-lilygo-t547/docs/REFERENCE.md`

## 当前状态

已完成：

- Python 状态模型、CLI、HTTP 服务。
- 浏览器 SVG 预览。
- LilyGO T5-ePaper-S3 固件骨架。
- PlatformIO 项目配置。
- 使用 LilyGo 官方 `T5-ePaper-S3` board 定义。
- 固件端中文字体渲染。
- 面向 4.7 寸 960x540 实机的状态看板布局。
- 固件已成功编译和上传到 `/dev/cu.usbmodem1301`。
- LilyGo 已通过 Wi-Fi 成功访问电脑端 `/state.json`，服务日志返回 `200`。

已验证：

```text
pytest: 10 passed
pio run: SUCCESS
pio upload: SUCCESS
LilyGo GET /state.json: 200
```

后续要做：

- 继续看实机屏幕显示效果，按外壳遮挡和观看距离微调字号、边距、灰度。
- 后续如果需要更多任务队列信息，再考虑分页或服务端渲染图片。
- 后续再验证电池供电和休眠刷新。

## 电脑端状态服务

推荐在项目根目录创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev,display]"
```

如果只想直接运行状态服务，也可以不用安装包，直接用 `PYTHONPATH=src`。

### 演示状态

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json demo
```

启动静态演示服务：

```bash
PYTHONPATH=src python3 -m agent_epaper.server --host 0.0.0.0 --port 18765 --state .agent-epaper-demo/state.json
```

`--state` 模式读取一个固定 JSON 文件，适合演示和手动写状态；屏幕内容不会自动跟随本机 Claude Code / Codex 会话变化。

### 实时采集服务

前台运行：

```bash
PYTHONPATH=src python3 -m agent_epaper.server --host 0.0.0.0 --port 18765 --collect
```

`--collect` 模式会在每次 HTTP 请求时从本机 Claude Code / Codex 会话和额度缓存实时生成状态，适合实机长期运行。

推荐使用 systemd 用户服务在后台运行：

```bash
mkdir -p ~/.config/systemd/user
cp hiclaude-18765.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start hiclaude-18765.service
```

开机自动启动：

```bash
systemctl --user enable hiclaude-18765.service
```

停止服务：

```bash
systemctl --user stop hiclaude-18765.service
```

取消开机自动启动：

```bash
systemctl --user disable hiclaude-18765.service
```

查看状态和日志：

```bash
systemctl --user status hiclaude-18765.service --no-pager
journalctl --user -u hiclaude-18765.service -f
```

修改 `hiclaude-18765.service` 或 `scripts/start-hiclaude-18765.sh` 后重新加载并重启：

```bash
cp hiclaude-18765.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user restart hiclaude-18765.service
```

访问地址：

```text
http://127.0.0.1:18765/
http://127.0.0.1:18765/state.json
http://127.0.0.1:18765/screen.svg
```

说明：本机 `8765` 端口已经被其他 Node 服务占用，所以这里使用 `18765`。如果你机器上 `18765` 也被占用，可以换成其他端口，但固件里的 `STATE_URL` 也要同步改。

## Claude Code / Codex 采集原理

实时采集入口是 `src/agent_epaper/collector.py`。HTTP 服务使用 `--collect` 时，每次访问 `/state.json` 都会调用 `collect()`，分别生成 `claude_code` 和 `codex` 两组数据：

```json
{
  "claude_code": {
    "label": "Claude Code",
    "quota": {},
    "tasks": []
  },
  "codex": {
    "label": "Codex",
    "quota": {},
    "tasks": []
  }
}
```

### Claude Code 任务

Claude Code 的任务来自本机 Claude transcript，而不是网络 API。

采集步骤：

1. 扫描 `~/.claude/sessions/*.json`。
2. 读取每个 session 的 `pid` 和 `sessionId`。
3. 用 `os.kill(pid, 0)` 判断进程是否还存在。
4. 在 `~/.claude/projects/**/{sessionId}.jsonl` 中找到对应 transcript。
5. 如果有多个活跃 transcript，选择最近修改的那个。
6. 倒序读取 JSONL，找到最新一条真正的用户文本作为任务名。

Claude transcript 中会混入一些不是人类任务的 `user` 记录，例如工具结果和内部 meta prompt。采集器会跳过：

- `isMeta: true` 的内部提示，例如 `/loop` 展开的系统文本。
- `message.content` 里只有 `tool_result` 的工具返回。
- 没有可显示文本的记录。

状态判断：

- 最新有效事件是 assistant，且 `stop_reason` 不是 `tool_use`，并且不是刚刚结束的 20 秒内响应，则标记为 `needs_action`。
- 否则标记为 `running`。
- 没有活跃 session 或解析失败时，显示 fallback：`等待任务` / `idle`。

### Codex 任务

Codex 的任务优先来自本机 Codex JSONL session。

采集步骤：

1. 扫描 `~/.codex/sessions/**/*.jsonl`。
2. 读取每个 session 第一行，只保留 `payload.source == "vscode"` 的主会话，避免把 subagent 会话当主任务。
3. 选择最近的主会话 JSONL。
4. 顺序读取 `event_msg`：
   - `payload.type == "user_message"` 时记录最近的用户消息。
   - `payload.type == "task_started"` 时标记任务运行中。
   - `payload.type == "task_complete"` 时标记等待用户操作。
5. 用最近的 `user_message` 作为 Codex 任务名。

状态判断：

- 最近任务事件是 `task_started`：`running`。
- 最近任务事件是 `task_complete`：`needs_action`。
- 没有任务事件但有用户消息：`idle`。

如果找不到可用 JSONL，会退回读取 `~/.codex/state_5.sqlite` 里的最新线程。但 SQLite 里只有 `first_user_message`，它通常是整条线程最早的用户消息，不适合表示当前任务，所以只是兜底。

### 额度采集

额度采集和任务采集是两条独立路径。

Claude Code：

- 从系统 keychain 的 `Claude Code-credentials` 读取 OAuth token。
- 请求 `https://api.anthropic.com/api/oauth/usage`。
- 映射：
  - `five_hour` -> `five_hour` / `5小时额度`
  - `seven_day` -> `weekly` / `7日额度`

Codex：

- 从 Codex session JSONL 里的 `token_count` 事件读取 `rate_limits`。
- 映射：
  - `primary` -> `five_hour` / `5小时额度`
  - `secondary` -> `weekly` / `7日额度`

额度结果会缓存 10 分钟：

```text
~/.agent-epaper/quota-cache.json
```

如果实时请求失败，会尽量使用内存缓存或文件缓存，避免屏幕突然清空额度。

### 限制和注意事项

- 这套逻辑依赖本机 Claude Code / Codex 的当前文件结构，属于本地集成，不是稳定公开协议。
- Claude Code 的 PID 在沙箱、容器或不同命名空间中可能判断不一致；如果任务显示不对，优先检查 `~/.claude/sessions/*.json` 和对应 transcript 的修改时间。
- Codex 任务名只显示最近用户消息的前 50 个字符，固件端也会继续做省略显示。
- 实机要显示实时内容，必须启动 `--collect` 服务；如果用 `--state .agent-epaper-demo/state.json`，屏幕会一直显示 demo 或手动写入的静态状态。

## 更新显示状态

更新当前任务：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json task \
  --agent claude \
  --name "实现 LilyGo 固件" \
  --status running \
  --detail "正在通过 Wi-Fi 拉取 state.json"
```

更新 Claude Code 5 小时额度：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json quota \
  --agent claude \
  --window 5h \
  --label "5小时额度" \
  --used 42 \
  --limit 100 \
  --reset "明日 08:00"
```

更新 Codex 周额度：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json quota \
  --agent codex \
  --window week \
  --label "周额度" \
  --used 95 \
  --limit 250 \
  --reset "周一 08:00"
```

查看 JSON：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json show
```

查看 SVG：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json show --svg
```

生成 LilyGo 960x540 预览图：

```bash
PYTHONPATH=src .venv/bin/python -m agent_epaper.display \
  --state .agent-epaper-demo/state.json \
  --screen lilygo_t5_47 \
  --once \
  --output .agent-epaper-demo/lilygo-preview.png
```

说明：当前设备协议仍然是 LilyGo 拉取 `state.json` 后在 ESP32 上渲染；这张预览图只是电脑端用同一份 JSON 生成的效果参考，不会直接发送到屏幕。

## LilyGo 首次验证

第一次拿到板子时，建议先跑 LilyGo 官方示例，确认硬件、屏幕、PSRAM、USB 串口都正常。这样可以把硬件/工具链问题和本项目代码问题分开。

Arduino IDE 官方建议配置：

```text
Board: ESP32S3 Dev Module
USB CDC On Boot: Enable
CPU Frequency: 240MHz WiFi
Flash Size: 16MB
Flash Mode: QIO 80MHz
Partition Scheme: 16M Flash
PSRAM: OPI PSRAM
Upload Mode: UART0/Hardware CDC
USB Mode: Hardware CDC and JTAG
Upload Speed: 921600
```

如果上传失败，可以手动进入下载模式：

```text
按住 BOOT/IO0
按一下 RST
松开 RST
松开 BOOT/IO0
重新上传
```

## 固件

固件目录：

```text
projects/epaper-lilygo-t547/firmware/
```

关键文件：

```text
projects/epaper-lilygo-t547/firmware/platformio.ini
projects/epaper-lilygo-t547/firmware/boards/T5-ePaper-S3.json
projects/epaper-lilygo-t547/firmware/src/main.cpp
projects/epaper-lilygo-t547/firmware/src/config_private.example.h
projects/epaper-lilygo-t547/firmware/src/config_private.h
```

`config_private.h` 是本地私密配置，已被 `.gitignore` 忽略，不要提交。

配置示例：

```cpp
#define WIFI_SSID "你的 Wi-Fi 名称"
#define WIFI_PASSWORD "你的 Wi-Fi 密码"
#define STATE_URL "http://192.168.31.127:18765/state.json"
```

注意：`STATE_URL` 必须使用电脑的局域网 IP，不能使用 `127.0.0.1`。在 ESP32 上，`127.0.0.1` 指的是 ESP32 自己，不是你的电脑。

### 中文字体

设备端仍然只拉取 `state.json`，不接收整屏图片。中文显示由 ESP32 本地渲染完成：

- `Adafruit GFX Library` 提供 framebuffer 绘制接口。
- `U8g2_for_Adafruit_GFX` 提供 UTF-8 文本绘制。
- 固件使用 `u8g2_font_wqy14_t_gb2312`、`u8g2_font_wqy16_t_gb2312` 显示中文。
- 4.7 寸 960x540 屏幕像素密度较高，固件对主要文本做了 2 倍像素缩放和轻微加粗，布局按“桌面远看”减少信息密度。
- 实机外壳/边框可能遮挡边缘，状态页左右保留约 20px 安全边距，底部保留更大余量；最小正文使用 14px 中文字体，不再使用 12px 小字。
- 当前 JSON 协议顶层固定 `claude_code` 和 `codex` 两组；每组下面有 `quota` 和 `tasks` 两大类；`quota` 中固定 `five_hour` 和 `weekly` 两个窗口，任务不再使用不可量化的 `progress`。
- 当前固件版式是双列 agent 看板：Claude Code / Codex 各占一列，任务区显示各自前 3 条任务，每行只显示状态短词和任务名称；还有更多任务时显示 `+N 任务运行中`。

注意：GB2312 字体覆盖常用简体中文。如果后续要显示 GB2312 之外的生僻字或 emoji，需要换更大的 Unicode 字体，或者改成电脑端渲染图片方案。

## PlatformIO

本项目使用 LilyGo 官方 `T5-ePaper-S3` board 定义：

```text
projects/epaper-lilygo-t547/firmware/boards/T5-ePaper-S3.json
```

这点很重要。通用 `esp32-s3-devkitc-1` 目标可以编译和上传，但 Flash/PSRAM 参数不完全匹配，实测会导致板子反复从 ROM 启动。

本项目当前把 PlatformIO 安装在 `.venv`，并把 PlatformIO core 放在项目内 `.platformio-core`，避免写入 `~/.platformio`。

编译：

```bash
cd projects/epaper-lilygo-t547/firmware
PLATFORMIO_CORE_DIR=../../../.platformio-core ../../../.venv/bin/pio run
```

上传：

```bash
cd projects/epaper-lilygo-t547/firmware
PLATFORMIO_CORE_DIR=../../../.platformio-core ../../../.venv/bin/pio run -t upload --upload-port /dev/cu.usbmodem1301
```

查看串口日志：

```bash
cd projects/epaper-lilygo-t547/firmware
PLATFORMIO_CORE_DIR=../../../.platformio-core ../../../.venv/bin/pio device monitor --port /dev/cu.usbmodem1301 --baud 115200
```

已验证上传日志里会识别到：

```text
Chip is ESP32-S3
Features: WiFi, BLE, Embedded PSRAM 8MB
Flash: 16MB
```

## 实机运行

确认电脑端服务正在运行：

```bash
systemctl --user status hiclaude-18765.service --no-pager
curl http://127.0.0.1:18765/state.json
```

LilyGo 成功访问时，服务端日志会出现类似：

```text
192.168.31.165 - "GET /state.json HTTP/1.1" 200 -
```

串口日志会出现类似：

```text
Fetching http://192.168.31.127:18765/state.json
```

## 测试

运行 Python 测试：

```bash
.venv/bin/python -m pytest
```

当前验证结果：

```text
10 passed
```

## 项目结构

```text
src/agent_epaper/                       Python CLI、状态模型、HTTP 服务、渲染逻辑
scripts/start-hiclaude-18765.sh         systemd 调用的 18765 实时采集服务启动脚本
hiclaude-18765.service                  systemd 用户服务定义
projects/epaper-lilygo-t547/cad/        墨水屏全包外壳 STEP / CadQuery
projects/epaper-lilygo-t547/firmware/   LilyGo T5-ePaper-S3 固件
projects/epaper-lilygo-t547/docs/       原厂引脚图、原理图、REFERENCE.md
projects/claude-fan/                    Claude Code 像素小人外形 FD14 140mm 风扇外壳（CadQuery + STEP，待打印验证）
docs/                                   仓库首页和共享文档
tests/                                  Python 单元测试
```

## 备注

- 当前没有假设 Claude Code / Codex 的本地会话文件格式是稳定公开协议；采集逻辑跟随本机工具实际文件结构维护。
- 固件第一版渲染偏基础，重点是验证 Wi-Fi、HTTP、JSON、PSRAM 和刷屏链路。
- 固件侧已加入 U8g2 中文字体，继续保持拉取 JSON 后在设备端渲染。
- 首次调试建议保持 USB-C 连接，电池和休眠放到后续阶段验证。
