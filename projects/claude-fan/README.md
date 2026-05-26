# Claude Code Pixel Fan (FD14)

为 DeepCool FD14 140 mm 正向风扇设计的 Claude Code 像素小人外形 3D 打印外壳。

固定 15° 仰角桌面摆放；橙色主体 + 黑色脚垫双材料/双色方案；M4 通体螺丝夹固风扇。

![预览](docs/refs/preview.png)

## 目录

- `cad/` —— CadQuery 脚本 + 装配 STEP
  - `make_step.py`：参数化建模主脚本
  - `fd14_claude_pixel_fan_enclosure.step`：完整装配
  - `parts/`：6 个独立零件 STEP（front_cover / rear_shell / top_spine / control_pod / wedge_feet / rear_heel）
- `docs/design.md` —— 设计说明（尺寸、装配、打印参数、迭代历史）
- `docs/refs/` —— 概念迭代图与渲染图

## 重新生成 STEP

```bash
cd projects/claude-fan/cad
python make_step.py
```

依赖：`cadquery`（项目 `.venv` 内）。生成物：`fd14_claude_pixel_fan_enclosure.step` 与 `parts/*.step,*.stl`。STL 默认不入库，可由 STEP 切片或脚本现场导出。

## 状态

- [x] CAD 主装配与零件 STEP
- [x] 设计文档与迭代记录
- [ ] FD14 实物孔距实测核对
- [ ] PWM 控制板 + 旋钮 + USB-C 实物尺寸核对
- [ ] 首版打印 + 装配验证
