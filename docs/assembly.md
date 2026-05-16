# 组装和安装流程

## 1. 树莓派准备

1. 烧录 Raspberry Pi OS Lite。
2. 配好 Wi-Fi 和 SSH。
3. 启用 SPI：

```bash
sudo raspi-config
```

选择 `Interface Options` -> `SPI` -> enable。

4. 安装 Python 依赖：

```bash
sudo apt update
sudo apt install -y python3-pip python3-pil python3-numpy git fonts-noto-cjk
python3 -m pip install requests spidev RPi.GPIO
```

5. 安装微雪 Python 驱动，按商品页 wiki 操作，确保能 `import waveshare_epd.epd4in2_V2`。

## 2. 接线

微雪 SPI 屏常用引脚：

| 屏幕 | 树莓派 |
| --- | --- |
| VCC | 3.3V 或 5V，按屏幕说明 |
| GND | GND |
| DIN | GPIO10 / MOSI |
| CLK | GPIO11 / SCLK |
| CS | GPIO8 / CE0 |
| DC | GPIO25 |
| RST | GPIO17 |
| BUSY | GPIO24 |
| PWR | GPIO18，若模块有该脚 |

如果是 HAT，直接插 40pin 即可。

## 3. 本机状态服务

在你的电脑上运行：

```bash
cd /home/midea/GithubRepository/HiClaude
PYTHONPATH=src python3 -m agent_epaper.cli demo
PYTHONPATH=src python3 -m agent_epaper.server --host 0.0.0.0 --port 8765
```

找到电脑局域网 IP：

```bash
ip -brief addr
```

树莓派访问：

```bash
curl http://电脑IP:8765/state.json
```

## 4. 树莓派刷新屏幕

把本仓库复制到树莓派，运行：

```bash
cd HiClaude
PYTHONPATH=src python3 -m agent_epaper.display --url http://电脑IP:8765/state.json --screen waveshare_4in2 --interval 60
```

7.5 寸普通版：

```bash
PYTHONPATH=src python3 -m agent_epaper.display --url http://电脑IP:8765/state.json --screen waveshare_7in5 --interval 60
```

7.5 寸 HD：

```bash
PYTHONPATH=src python3 -m agent_epaper.display --url http://电脑IP:8765/state.json --screen waveshare_7in5_hd --interval 60
```

## 5. 自启动

创建 systemd 服务：

```ini
[Unit]
Description=Agent E-Paper Display
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/pi/HiClaude
Environment=PYTHONPATH=/home/pi/HiClaude/src
ExecStart=/usr/bin/python3 -m agent_epaper.display --url http://电脑IP:8765/state.json --screen waveshare_4in2 --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

保存为 `/etc/systemd/system/agent-epaper.service` 后：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agent-epaper.service
```
