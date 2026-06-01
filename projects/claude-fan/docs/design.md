# FD14 Claude Code Pixel Fan Enclosure

为 DeepCool FD14 正向 140 mm 风扇设计的可 3D 打印外壳，外形参考 Claude Code 橙色像素小人：方头、黑色方眼、左右短臂、两条短腿。最终采用固定约 15° 仰角，不做可调支架。

## 最终设计方向

- **正面轮廓**：参考 `concept-05-wedge-feet.png` 的比例，风扇位于 Claude 正面中心，宽上额与左右方眼压在风扇上方。
- **风扇安装**：140 mm 风扇嵌在主体中央，大圆形开口；后壳不做螺丝孔/螺丝柱。
- **风道**：前后贯通，后壳改为低矮圆形后风道 + 背部护网，不再做外凸喇叭罩。
- **固定角度**：底部两只腿的脚垫为固定 15° 斜切面，桌面自然仰吹。
- **稳定方式**：宽前脚 + 后部一体尾托形成三点支撑，不用后撑杆。
- **走线**：按实物照片改为右侧边梁走线槽，带 4-pin 插头缓冲腔、侧向出线口和三处压线桥，避免线束跨扇叶。
- **控制区**：右侧 `control_pod` 直接导入 `标准A_快充A_3PIN版.STEP`，只做旋转和平移，不重建外壳细节。
- **正面格栅**：按 `concept-05-wedge-feet.png` 改为独立深色圆形格栅：外圈、三层同心环、12 根放射支撑和中心毂。

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

当前 STEP 结合 DeepCool FD14 官方规格与
`refs/12_14CM_DesktopFan.3mf` 主体网格实测：

| 参数 | 数值 |
| --- | --- |
| FD14 官方外框 | 140 × 140 × 25 mm |
| 参考 3MF 主体外宽 | 147.964 mm |
| 风扇槽 | 141.904 × 141.904 mm |
| 风扇槽单边余量 | 0.952 mm |
| 前盖到后壳风扇空间 | 25.600 mm（相对 FD14 厚度总余量 0.600 mm） |
| 安装孔距 | 不使用，不在后壳建孔 |
| 螺丝孔/螺丝柱 | 无 |
| 中央开口直径 | 132 mm |
| 外壳正面包络 | 240 × 212 mm（含侧臂、宽上额、腿部和脚位） |
| 右侧走线槽 | 约 12 × 126 × 4.2 mm（按照片估算） |
| 控制器外壳 | 45.00 × 26.78 × 22.60 mm（直接导入 `标准A_快充A_3PIN版.STEP`） |
| 头顶宽上额 | 178 × 30 mm（眼睛中心约 X=±62, Y=88） |
| 后风道/护网 | 外径 148 mm，深 10 mm，与后壳重叠 1.5 mm 融合 |
| 深色前格栅 | 外径 128 mm，厚 2.8 mm，三层同心环，12 根放射支撑 |
| 固定仰角 | 15° |

实物打样前建议实测：FD14 风扇外框厚度、出线口位置、4-pin 插头尺寸、PWM 小板尺寸与旋钮/USB-C 中心高度。

## 打印参数

- 壳体壁厚 1.8–2.0 mm，加强筋 1.2–1.6 mm
- 材料：PLA+ / PETG（主体）+ 黑色 PETG/TPU（脚垫与鞋跟）
- 鞋跟/脚垫：本身用深色材料打印；防滑可后贴硅胶条
- 层高 0.2 mm，外圈 3，顶/底层 4–5

### 各零件打印方向（推荐）

| 零件 | 朝向（朝下面） | 是否需要支撑 |
| --- | --- | --- |
| `front_cover` | **正面朝下**（眼睛朝下，平整背面朝上） | 否 |
| `front_grille` | **平放** | 否 |
| `rear_shell` | **风道喇叭朝上**（后壳背面朝下） | 风扇舱悬空段需 tree 支撑 |
| `top_spine` | **凹槽开口朝上**（5 mm 盖朝下） | 否 |
| `control_pod` | **检修口朝上**（开放面朝上） | 否 |
| `wedge_feet` | **斜面朝下**（即 15° 接触面贴床） | 否；斜面会自动作为第一层 |
| `rear_heel` | **斜面朝下**（同 wedge_feet） | 否 |

## 装配

### 固定方式

当前版本默认风扇放入 `rear_shell` 的方形腔内，后壳不生成风扇螺丝孔或螺丝柱。后风道前端向主体内重叠 1.5 mm，切片时应与 `rear_shell` 主体连成一个实体。

导入的控制器外壳作为独立 `control_pod` 摆在右侧，与后壳侧边接触；实物固定可用环氧胶、泡棉胶或后续追加小压片。

### 步骤

1. 把 FD14 风扇放入 `rear_shell` 的方形腔。
2. 风扇线束沿 `rear_shell` 右侧边梁的开放走线槽下行，4-pin 插头和余线放入下方缓冲腔，三处压线桥用于轻压线束。
3. 线束从侧向出线口接到右侧 `control_pod`；该零件保持参考 STEP 的原始两件式外壳细节。
4. 把深色 `front_grille` 固定到 `front_cover` 圆形窗口前方。
5. `front_cover` 扣到 `rear_shell` 前面。
6. `top_spine` / `control_pod` / `wedge_feet` / `rear_heel` 用环氧或泡棉胶固定到 `rear_shell`。

### 三点支撑

`wedge_feet` 两只 + `rear_heel` 一只共同决定 15° 仰角桌面平面。三个底面同处一个倾斜平面（`make_step.py` 中 `desk_z(y)` 函数定义），不要单独修改任一脚的 z。

坐标系（见 `cad/make_step.py`）：
- +Z = 正面（观察者 / 出风方向）
- +Y = 头部方向，-Y = 腿部方向
- +X = 右侧（控制舱），-X = 左侧

### 美化建议

- **眼睛**：盲腔深 2 mm，可在打印时做 filament swap，最上 2 mm 换黑色；或后涂黑色丙烯/亚克力。
- **风扇前盖中心**：独立深色圆格栅提供外圈、同心环、放射支撑与中心毂，视觉关系接近参考图。

## 文件

- `cad/make_step.py` —— CadQuery 参数化建模脚本，重新生成请运行此文件
- `cad/fd14_claude_pixel_fan_enclosure.step` —— 完整装配
- `cad/parts/*.step` —— 7 个独立零件：`front_cover` / `front_grille` / `rear_shell` / `top_spine` / `control_pod` / `wedge_feet` / `rear_heel`
- `docs/refs/*.png` —— 概念迭代图与渲染预览
