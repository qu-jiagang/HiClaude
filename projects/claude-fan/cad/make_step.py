"""FD14 Claude Pixel Fan Enclosure — multi-piece printable assembly.

Generated via the zero-to-cad skill (Z2C agentic CAD synthesis loop).

Reference: design.md + concept-06-fixed-15deg.png in this directory.

Assembly method: M4 through-screws clamp front_cover -> fan -> rear_shell;
                 control_pod / top_spine / wedge_feet / rear_heel are bonded
                 (or M3 screwed) to the rear_shell.

Coordinate system:
    +Z = front (toward viewer / fan air-output direction)
    +Y = head direction, -Y = leg direction
    +X = right (control pod) side, -X = left

Outputs (next to this file):
    fd14_claude_pixel_fan_enclosure.step  — full assembly
    parts/front_cover.step / .stl
    parts/rear_shell.step  / .stl
    parts/top_spine.step   / .stl
    parts/control_pod.step / .stl
    parts/wedge_feet.step  / .stl
    parts/rear_heel.step   / .stl
"""
from __future__ import annotations

from math import radians, tan
from pathlib import Path

import cadquery as cq

# === Parameters (mm, all traceable to design.md or FD14 datasheet) ===
# FD14 fan
fan_w = 140.0
fan_h = 140.0
fan_thick = 26.0
fan_hole_pitch = 124.5
fan_bore_dia = 132.0

# Pixel-robot silhouette (design.md, body_h widened from 138 → 142 so the
# 140 mm fan clears the head/leg seams with 1 mm/side)
body_w = 176.0
body_h = 142.0
body_cy = 10.0
head_w = 104.0
head_h = 32.0
head_cy = 95.0
arm_w = 28.0
arm_h = 42.0
arm_dx = 102.0
arm_cy = 34.0
leg_w = 30.0
leg_h = 42.0
leg_dx = 42.0
leg_cy = -80.0
fillet_r = 3.0

# Z layout (~70 mm total) with 0.3 mm fan-thickness tolerance per side
fan_z_clearance = 0.3
front_thick = 4.0
front_z = fan_thick / 2.0 + fan_z_clearance      # +13.3
rear_thick = 24.0
rear_z_top = -fan_thick / 2.0 - fan_z_clearance  # -13.3
duct_len = 15.0

# Internal cable conduit cross-section
cable_w = 8.0
cable_h = 6.0

# M4 fan mounting
boss_dia = 11.0
boss_inner = 4.4
boss_positions = [
    (-fan_hole_pitch / 2, body_cy - fan_hole_pitch / 2),
    ( fan_hole_pitch / 2, body_cy - fan_hole_pitch / 2),
    (-fan_hole_pitch / 2, body_cy + fan_hole_pitch / 2),
    ( fan_hole_pitch / 2, body_cy + fan_hole_pitch / 2),
]

assembly_method = "m4_through_clamp"

ORANGE = cq.Color(0.95, 0.42, 0.18, 1.0)
DARK   = cq.Color(0.10, 0.10, 0.10, 1.0)


def silhouette(thickness: float, base_z: float):
    """Pixel-robot silhouette extruded thickness mm, bottom face at base_z."""
    parts = [
        (0,        body_cy, body_w, body_h),
        (0,        head_cy, head_w, head_h),
        (-arm_dx,  arm_cy,  arm_w,  arm_h),
        ( arm_dx,  arm_cy,  arm_w,  arm_h),
        (-leg_dx,  leg_cy,  leg_w,  leg_h),
        ( leg_dx,  leg_cy,  leg_w,  leg_h),
    ]
    s = None
    for cx, cy, w, h in parts:
        block = (cq.Workplane("XY")
                 .center(cx, cy)
                 .box(w, h, thickness, centered=(True, True, False)))
        s = block if s is None else s.union(block)
    s = s.edges("|Z").fillet(fillet_r)
    return s.translate((0, 0, base_z))


# --- Front cover ---
def make_front_cover():
    cover = silhouette(front_thick, front_z)
    cover = (cover.faces(">Z").workplane()
             .center(0, body_cy).circle(fan_bore_dia / 2 - 4).cutThruAll())
    for ex in (-26, 26):
        cover = (cover.faces(">Z").workplane()
                 .center(ex, head_cy + 2).rect(12, 12).cutThruAll())
    for x, y in boss_positions:
        cover = (cover.faces(">Z").workplane()
                 .center(x, y).circle(boss_inner / 2).cutThruAll())
    # Sparse radial grille bars across the fan bore
    bar_th = 3.0
    bar_len = fan_bore_dia - 20
    rib_extrude = front_thick - 1.0
    ribs = None
    for ang_deg in (0, 60, 120):
        rib = (cq.Workplane("XY")
               .rect(bar_len, bar_th)
               .extrude(rib_extrude)
               .translate((0, body_cy, front_z + 0.5))
               .rotate((0, body_cy, 0), (0, body_cy, 1), ang_deg))
        ribs = rib if ribs is None else ribs.union(rib)
    bore_mask = (cq.Workplane("XY").center(0, body_cy)
                 .circle(fan_bore_dia / 2 - 5)
                 .extrude(front_thick + 2)
                 .translate((0, 0, front_z - 1)))
    ribs = ribs.intersect(bore_mask)
    return cover.union(ribs)


# --- Rear shell ---
def make_rear_shell():
    shell = silhouette(rear_thick, rear_z_top - rear_thick)
    pocket_depth = rear_thick - 3.0
    fan_pocket = (cq.Workplane("XY").center(0, body_cy)
                  .box(fan_w + 2, fan_h + 2, pocket_depth, centered=(True, True, False))
                  .translate((0, 0, rear_z_top - pocket_depth)))
    shell = shell.cut(fan_pocket)
    shell = (shell.faces("<Z").workplane()
             .center(0, body_cy).circle(fan_bore_dia / 2 - 2).cutThruAll())
    for x, y in boss_positions:
        boss = (cq.Workplane("XY").center(x, y)
                .circle(boss_dia / 2)
                .extrude(pocket_depth)
                .translate((0, 0, rear_z_top - pocket_depth)))
        shell = shell.union(boss)
    for x, y in boss_positions:
        shell = (shell.faces("<Z").workplane()
                 .center(x, y).circle(boss_inner / 2).cutThruAll())
    # Flared exhaust duct — outer cone minus inner cone for an annular flare
    duct_z0 = rear_z_top - rear_thick
    outer = (cq.Workplane("XY").center(0, body_cy)
             .circle(fan_bore_dia / 2 + 2)
             .workplane(offset=-duct_len)
             .circle(fan_bore_dia / 2 + 14)
             .loft(combine=False)
             .translate((0, 0, duct_z0)))
    inner = (cq.Workplane("XY").center(0, body_cy)
             .circle(fan_bore_dia / 2 - 2)
             .workplane(offset=-duct_len)
             .circle(fan_bore_dia / 2 + 10)
             .loft(combine=False)
             .translate((0, 0, duct_z0)))
    return shell.union(outer.cut(inner))


# --- Top cable spine ---
def make_top_spine():
    """Spine on top of the head, with a hidden cable channel that opens
    DOWNWARD so the fan cable enters from the fan-zone air below and is
    hidden under a 5 mm top cover."""
    spine_w = 100.0
    spine_h_y = 22.0
    spine_thick = 16.0
    spine_cy = head_cy + head_h / 2 - 4
    spine_cz = front_z - 2
    spine = (cq.Workplane("XY").center(0, spine_cy)
             .box(spine_w, spine_h_y, spine_thick)
             .translate((0, 0, spine_cz)))
    spine = spine.edges("|Z").fillet(2.5)
    # Channel cut from -Z face, 11 mm deep, leaves 5 mm top cover
    channel = (cq.Workplane("XY").center(0, spine_cy)
               .box(spine_w - 12, cable_h + 1, 11, centered=(True, True, False))
               .translate((0, 0, spine_cz - spine_thick / 2 - 0.1)))
    return spine.cut(channel)


# --- Right-side control pod ---
def make_control_pod():
    """Hollow shoulder pod hosting the controller PCB.
    Service access opens on -Z (back); cable feed-through on -X (toward body)."""
    pod_w = 30.0
    pod_h_y = 52.0
    pod_thick = 38.0
    pod_cx = arm_dx + arm_w / 2 + pod_w / 2 - 8
    pod_cy = arm_cy
    wall = 3.0
    pod = (cq.Workplane("XY").center(pod_cx, pod_cy)
           .box(pod_w, pod_h_y, pod_thick))
    pod = pod.edges("|Z").fillet(3.0)
    # Internal PCB cavity (24 × 46 × 28)
    cavity = (cq.Workplane("XY").center(pod_cx, pod_cy)
              .box(pod_w - 2 * wall, pod_h_y - 2 * wall, pod_thick - 2 * wall - 4))
    pod = pod.cut(cavity)
    # Cable feed-through on -X face (faces body / fan-zone air)
    cable_in = (cq.Workplane("YZ").rect(14, 10).extrude(6)
                .translate((pod_cx - pod_w / 2 - 1, pod_cy - 8, 0)))
    pod = pod.cut(cable_in)
    # Service access on -Z face (full-cavity-size opening; external snap cover)
    service = (cq.Workplane("XY").center(pod_cx, pod_cy)
               .rect(pod_w - 2 * wall - 1, pod_h_y - 2 * wall - 1).extrude(6)
               .translate((0, 0, -pod_thick / 2 - 1)))
    pod = pod.cut(service)
    # USB-C through-hole (right face +X)
    usb = (cq.Workplane("YZ").rect(10, 4).extrude(8)
           .translate((pod_cx + pod_w / 2 - 4, pod_cy + 14, 8)))
    pod = pod.cut(usb)
    # Knob through-hole (right face +X)
    knob = (cq.Workplane("YZ").circle(5).extrude(8)
            .translate((pod_cx + pod_w / 2 - 4, pod_cy - 4, -8)))
    return pod.cut(knob)


# --- Wedge feet (fixed 15° tilt) ---
def make_wedge_feet():
    tilt = radians(15)
    foot_w = 36.0
    fy0 = leg_cy - leg_h / 2
    fy1 = leg_cy + leg_h / 2
    foot_depth = fy1 - fy0
    foot_back = 8.0
    foot_front = foot_back + foot_depth * tan(tilt)
    z_top = rear_z_top - rear_thick + 0.1
    pts = [
        (fy0, z_top),
        (fy1, z_top),
        (fy1, z_top - foot_back),
        (fy0, z_top - foot_front),
    ]
    feet = None
    for x_center in (-leg_dx, leg_dx):
        prof = cq.Workplane("YZ").polyline(pts).close()
        foot = prof.extrude(foot_w).translate((x_center - foot_w / 2, 0, 0))
        foot = foot.edges("|X").fillet(1.5)
        feet = foot if feet is None else feet.union(foot)
    return feet


# --- Rear heel (third support point under legs) ---
def make_rear_heel():
    heel_w = 2 * leg_dx + leg_w + 6
    heel_h_y = 28.0
    heel_thick = 16.0
    heel_cy = leg_cy + 4
    heel_cz = rear_z_top - rear_thick - heel_thick / 2 + 6
    heel = (cq.Workplane("XY").center(0, heel_cy)
            .box(heel_w, heel_h_y, heel_thick)
            .translate((0, 0, heel_cz)))
    return heel.edges("|Z").fillet(5.0)


# --- Export ---
PARTS = [
    ("front_cover",  make_front_cover, ORANGE),
    ("rear_shell",   make_rear_shell,  ORANGE),
    ("top_spine",    make_top_spine,   ORANGE),
    ("control_pod",  make_control_pod, ORANGE),
    ("wedge_feet",   make_wedge_feet,  DARK),
    ("rear_heel",    make_rear_heel,   DARK),
]


def build_assembly():
    asm = cq.Assembly(name="FD14_Claude_Pixel_Fan_Enclosure")
    for name, maker, color in PARTS:
        asm.add(maker(), name=name, color=color)
    return asm


def main():
    here = Path(__file__).parent
    parts_dir = here / "parts"
    parts_dir.mkdir(exist_ok=True)
    print("Building parts ...")
    built = []
    for name, maker, color in PARTS:
        part = maker()
        cq.exporters.export(part, str(parts_dir / f"{name}.step"))
        cq.exporters.export(part, str(parts_dir / f"{name}.stl"), tolerance=0.2)
        built.append((name, part, color))
        print(f"  {name}: OK")
    asm = cq.Assembly(name="FD14_Claude_Pixel_Fan_Enclosure")
    for name, part, color in built:
        asm.add(part, name=name, color=color)
    out = here / "fd14_claude_pixel_fan_enclosure.step"
    asm.save(str(out))
    print(f"\nWrote assembly: {out}")
    print(f"Wrote {len(PARTS)} parts -> {parts_dir}")


if __name__ == "__main__":
    main()
