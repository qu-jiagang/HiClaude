# hiClaude 墨水屏状态牌

这是一个给 Claude Code / Codex 任务状态和额度做桌面展示的电子墨水屏项目，目标硬件是 LilyGo `T5-ePaper-S3 4.7"`。

项目目前包含三部分：

- 电脑端 Python 状态服务：维护任务、额度、提示信息，并提供 `state.json`、`screen.svg` 和浏览器预览。
- LilyGo 固件：连接 Wi-Fi，访问电脑端状态服务，解析 JSON，并刷新 960x540 墨水屏。
- CAD 和文档：LilyGo T5 4.7 寸桌面支架/外壳参考资料。

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
- `docs/reference/lilygo_t5_47_reference.md`
- `cad/lilygo_t5_47_desk_stand.step`
- `cad/lilygo_t5_47_mounted.step`

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
pytest: 3 passed
pio run: SUCCESS
pio upload: SUCCESS
LilyGo GET /state.json: 200
```

后续要做：

- 继续看实机屏幕显示效果，按外壳遮挡和观看距离微调字号、边距、灰度。
- 后续如果需要更多任务队列信息，再考虑分页或服务端渲染图片。
- 后续再验证电池供电和休眠刷新。

## Python 环境

推荐在项目根目录创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev,display]"
```

如果只想直接运行状态服务，也可以不用安装包，直接用 `PYTHONPATH=src`。

生成演示状态：

```bash
PYTHONPATH=src python3 -m agent_epaper.cli --state .agent-epaper-demo/state.json demo
```

启动状态服务：

```bash
PYTHONPATH=src python3 -m agent_epaper.server --host 0.0.0.0 --port 18765 --state .agent-epaper-demo/state.json
```

浏览器打开：

```text
http://127.0.0.1:18765/
http://127.0.0.1:18765/state.json
http://127.0.0.1:18765/screen.svg
```

说明：本机 `8765` 端口已经被其他 Node 服务占用，所以这里使用 `18765`。如果你机器上 `18765` 也被占用，可以换成其他端口，但固件里的 `STATE_URL` 也要同步改。

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
firmware/lilygo_t5_47/
```

关键文件：

```text
firmware/lilygo_t5_47/platformio.ini
firmware/lilygo_t5_47/boards/T5-ePaper-S3.json
firmware/lilygo_t5_47/src/main.cpp
firmware/lilygo_t5_47/src/config_private.example.h
firmware/lilygo_t5_47/src/config_private.h
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
firmware/lilygo_t5_47/boards/T5-ePaper-S3.json
```

这点很重要。通用 `esp32-s3-devkitc-1` 目标可以编译和上传，但 Flash/PSRAM 参数不完全匹配，实测会导致板子反复从 ROM 启动。

本项目当前把 PlatformIO 安装在 `.venv`，并把 PlatformIO core 放在项目内 `.platformio-core`，避免写入 `~/.platformio`。

编译：

```bash
cd firmware/lilygo_t5_47
PLATFORMIO_CORE_DIR=../../.platformio-core ../../.venv/bin/pio run
```

上传：

```bash
cd firmware/lilygo_t5_47
PLATFORMIO_CORE_DIR=../../.platformio-core ../../.venv/bin/pio run -t upload --upload-port /dev/cu.usbmodem1301
```

查看串口日志：

```bash
cd firmware/lilygo_t5_47
PLATFORMIO_CORE_DIR=../../.platformio-core ../../.venv/bin/pio device monitor --port /dev/cu.usbmodem1301 --baud 115200
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
PYTHONPATH=src python3 -m agent_epaper.server --host 0.0.0.0 --port 18765 --state .agent-epaper-demo/state.json
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
3 passed
```

## 项目结构

```text
src/agent_epaper/       Python CLI、状态模型、HTTP 服务、渲染逻辑
firmware/lilygo_t5_47/  LilyGo T5-ePaper-S3 固件
cad/                    CadQuery 源文件和 STEP/STL 导出
docs/                   本地实施指南、参考资料和图片
tests/                  Python 单元测试
```

## 备注

- 当前没有假设 Claude Code / Codex 有稳定公开额度 API，额度先通过 CLI 写入。
- 固件第一版渲染偏基础，重点是验证 Wi-Fi、HTTP、JSON、PSRAM 和刷屏链路。
- 固件侧已加入 U8g2 中文字体，继续保持拉取 JSON 后在设备端渲染。
- 首次调试建议保持 USB-C 连接，电池和休眠放到后续阶段验证。
