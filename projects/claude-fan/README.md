# Claude Code Pixel Fan (FD14)

为 DeepCool FD14 140 mm 正向风扇设计的 Claude Code 像素小人外形 3D 打印外壳。

固定 15° 仰角桌面摆放；橙色主体 + 黑色脚垫双材料/双色方案；风扇作为 Claude 正脸中心，后壳不做螺丝孔/螺丝柱，背面改为低矮一体后风道护网；右侧走线槽接直接导入的控制器参考 STEP。

14 cm 风扇位已按 `docs/refs/12_14CM_DesktopFan.3mf` 调整：槽位为
`141.904 × 141.904 mm`，用于容纳官方规格 `140 × 140 × 25 mm` 的
DeepCool FD14。

正面按 `docs/refs/concept-05-wedge-feet.png` 的造型改为独立深色圆形格栅：
外圈 + 三层同心环 + 12 根放射支撑 + 中心毂。

![预览](docs/refs/preview.png)

## 目录

- `cad/` —— CadQuery 脚本 + 装配 STEP
  - `make_step.py`：参数化建模主脚本
  - `fd14_claude_pixel_fan_enclosure.step`：完整装配
  - `parts/`：7 个独立零件 STEP（含独立深色 front_grille）
- `docs/design.md` —— 设计说明（尺寸、装配、打印参数、迭代历史）
- `docs/refs/` —— 概念迭代图与渲染图

## 重新生成 STEP

```bash
cd projects/claude-fan/cad
python make_step.py
```

依赖：`cadquery`（项目 `.venv` 内）。生成物：`fd14_claude_pixel_fan_enclosure.step` 与 `parts/*.step,*.stl`。STL 默认不入库，可由 STEP 切片或脚本现场导出。

## 状态

- [x] CAD 主装配与零件 STEP/STL
- [x] 正面比例和后风道重新设计
- [x] 参考 `12_14CM_DesktopFan.3mf` 校准 14 cm 风扇槽
- [x] 按参考图改为独立深色圆形前格栅
- [x] 后壳无风扇螺丝孔/螺丝柱
- [x] 设计文档与迭代记录
- [ ] FD14 实物外框与线束位置核对
- [ ] PWM 控制板 + 旋钮 + USB-C 实物尺寸核对
- [ ] 首版打印 + 装配验证
