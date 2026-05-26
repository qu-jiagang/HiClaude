# FD14 Claude Code Pixel Fan Enclosure

为 DeepCool FD14 正向 140 mm 风扇设计的可 3D 打印外壳，外形参考 Claude Code 橙色像素小人：方头、黑色方眼、左右短臂、两条短腿。最终采用固定约 15° 仰角，不做可调支架。

## 最终设计方向

- **正面轮廓**：像素小人形态，橙色主体 + 头顶凸台 + 左右短臂 + 两只短腿。
- **风扇安装**：140 mm 风扇嵌在主体中央，大圆形开口，四角螺丝柱。
- **风道**：前后贯通，后壳做浅喇叭导流罩，不包死风扇。
- **固定角度**：底部两只腿的脚垫为固定 15° 斜切面，桌面自然仰吹。
- **稳定方式**：宽前脚 + 后部一体尾托形成三点支撑，不用后撑杆。
- **顶部线槽**：风扇顶部出线进入头顶凸台的下开口凹槽，避免线束跨扇叶。
- **控制区**：右肩集成控制舱，侧面露 USB-C 与旋钮，4-pin 接口留检修盖。

最终方向参考：

![固定 15° 最终方向](refs/concept-06-fixed-15deg.png)

## 设计迭代

| # | 方向 | 结果 |
| --- | --- | --- |
| 01 | [初始三方案](refs/concept-01-initial-options.png) | 探索期 |
| 02 | [可调支架](refs/concept-02-adjustable-stand.png) | 复杂度过高，放弃 |
| 03 | [像素小人外形](refs/concept-03-pixel-robot.png) | 确定整体造型 |
| 04 | [宽后撑板](refs/concept-04-wide-rear-support.png) | 外观太重，放弃 |
| 05 | [楔形脚](refs/concept-05-wedge-feet.png) | 最终方案基础 |
| 06 | [固定 15°](refs/concept-06-fixed-15deg.png) | **采用** |

预览与剖面：

![Preview](refs/preview.png)

![剖面 - 风扇配合](refs/section_fan_fit.png)

## 关键尺寸

当前 STEP 按通用 140 mm PC 风扇估算：

| 参数 | 数值 |
| --- | --- |
| 风扇外框 | 140 × 140 mm |
| 风扇厚度 | 26 mm |
| 安装孔距 | 124.5 × 124.5 mm |
| 螺丝孔直径 | 4.5 mm |
| 中央开口直径 | 132 mm |
| 外壳主体宽度 | 176 mm |
| 外壳主体高度 | 156 mm（含头顶凸台 142+ 凸台） |
| 头顶线槽凸台 | 104 × 32 mm |
| 固定仰角 | 15° |

实物打样前建议实测：FD14 四角孔径与孔距、风扇顶部出线口位置、4-pin 插头尺寸、PWM 小板尺寸与旋钮/USB-C 中心高度。

## 打印参数建议

- 壳体壁厚 1.8–2.0 mm，加强筋 1.2–1.6 mm
- 风扇螺丝柱：M4 热熔铜螺母或自攻螺丝二选一
- 材料：PLA+ / PETG
- 脚垫：黑色 TPU 或后贴硅胶条
- 打印方向：前盖正面朝上 / 后壳背面朝上，按切片支撑调整

## 装配

M4 通体螺丝串联：`front_cover → 风扇 → rear_shell`。
`control_pod / top_spine / wedge_feet / rear_heel` 粘接或 M3 螺丝固定到 `rear_shell`。

坐标系（见 `cad/make_step.py`）：
- +Z = 正面（观察者 / 出风方向）
- +Y = 头部方向，-Y = 腿部方向
- +X = 右侧（控制舱），-X = 左侧

## 文件

- `cad/make_step.py` —— CadQuery 参数化建模脚本，重新生成请运行此文件
- `cad/fd14_claude_pixel_fan_enclosure.step` —— 完整装配
- `cad/parts/*.step` —— 6 个独立零件：`front_cover` / `rear_shell` / `top_spine` / `control_pod` / `wedge_feet` / `rear_heel`
- `docs/refs/*.png` —— 概念迭代图与渲染预览
