# Epaper LilyGo T5 4.7"

基于 LilyGo T5-ePaper-S3 (4.7" 黑白墨水屏) 的 Claude agent 显示终端。

## 目录

- `cad/` —— 全包外壳 STEP 模型（主体、按键、电池仓门）与 CadQuery 脚本
- `firmware/` —— PlatformIO 固件工程（ESP32-S3，刷写到设备）
- `docs/` —— 官方参考资料：原厂引脚图、原理图 PDF、`REFERENCE.md`

## 快速开始

固件构建（在 `firmware/` 下）：

```bash
cd projects/epaper-lilygo-t547/firmware
pio run                  # 编译
pio run -t upload        # 烧录
pio device monitor       # 串口
```

详见仓库根 `README.md` 的「固件」章节。
