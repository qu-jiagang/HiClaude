"""FD14 Claude Pixel Fan Enclosure — multi-piece printable assembly.

Generated via the zero-to-cad skill (Z2C agentic CAD synthesis loop).

Reference: design.md + concept-06-fixed-15deg.png in this directory.

Assembly method: M4 fan screws clamp front_cover -> fan -> rear_shell bosses;
                 fan/controller wiring is routed through a serviceable
                 right-side gutter into a directly imported reference
                 controller shell. top_spine / wedge_feet / rear_heel are
                 bonded to the rear_shell.

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

# === Parameters (mm) ===
# FD14 fan
fan_w = 140.0
fan_h = 140.0
fan_thick = 26.0
fan_bore_dia = 132.0

# Pixel-robot silhouette
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

# Printable fan clamping hardware, estimated from the common 140 mm PC fan
# pattern. Use M4 fan screws through the front cover and fan frame into the
# rear-shell pilot bosses.
fan_mount_spacing_est = 124.5
fan_mount_points = (
    (-fan_mount_spacing_est / 2.0, body_cy - fan_mount_spacing_est / 2.0),
    ( fan_mount_spacing_est / 2.0, body_cy - fan_mount_spacing_est / 2.0),
    (-fan_mount_spacing_est / 2.0, body_cy + fan_mount_spacing_est / 2.0),
    ( fan_mount_spacing_est / 2.0, body_cy + fan_mount_spacing_est / 2.0),
)
front_screw_clearance_dia = 4.6
front_screw_counterbore_dia = 8.8
front_screw_counterbore_depth = 2.2
rear_screw_boss_dia = 13.0
rear_screw_boss_pilot_dia = 3.2

# Z layout
fan_z_clearance = 0.3
front_thick = 4.0
front_z = fan_thick / 2.0 + fan_z_clearance      # +13.3
rear_thick = 24.0
rear_z_top = -fan_thick / 2.0 - fan_z_clearance  # -13.3
duct_len = 15.0

# Wiring path, estimated from the user's controller/fan photos.
cable_w_est = 8.0
cable_h_est = 6.0
wire_gutter_w_est = 12.0
wire_gutter_len_est = 126.0
wire_gutter_depth_est = 4.2
wire_gutter_x = fan_w / 2 + 8.5
wire_gutter_y = body_cy - 5.0
wire_gutter_z = rear_z_top - wire_gutter_depth_est / 2.0 + 0.2
wire_clip_w_est = 18.0
wire_clip_len_est = 3.0
wire_clip_thick_est = 2.0
wire_clip_y_positions = (-42.0, 4.0, 48.0)
plug_pocket_w_est = 15.5
plug_pocket_len_est = 24.0
plug_pocket_depth_est = 5.5
plug_pocket_y = -52.0
side_exit_w_est = 10.0
side_exit_h_est = 8.0
side_exit_y = 8.0

# Controller shell copied directly from docs/refs/标准A_快充A_3PIN版.STEP.
controller_reference_step = "标准A_快充A_3PIN版.STEP"
controller_reference_center = (-4.6276190937115995, 6.2111530019138685, 45.15000000000001)
controller_reference_rotation_deg = 90.0
controller_reference_target = (
    body_w / 2.0 + 26.777470862199387 / 2.0 + 2.0,
    side_exit_y,
    -2.0,
)

# Fixed 15° tilt — shared by wedge_feet and rear_heel so both bottom faces
# lie on the same desk plane and provide real 3-point support
tilt_deg = 15.0
foot_back = 8.0
foot_depth = leg_h                                # 42 (wedge length along Y)
foot_front = foot_back + foot_depth * tan(radians(tilt_deg))
foot_z_top = rear_z_top - rear_thick + 0.1
foot_fy0 = leg_cy - leg_h / 2                     # -101
foot_fy1 = leg_cy + leg_h / 2                     # -59

# Desk plane: z = desk_a + desk_b * y (derived from foot bottom corners)
desk_b = (foot_front - foot_back) / (foot_fy1 - foot_fy0)
desk_a = (foot_z_top - foot_back) - desk_b * foot_fy1


def desk_z(y: float) -> float:
    return desk_a + desk_b * y


assembly_method = "m4_clamp_side_gutter_to_imported_controller_shell"

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
    # Four printable screw clearances aligned to the common 140 mm fan mount
    # pattern. M4 fan screws pass through the cover and fan frame, then bite
    # into the rear shell bosses added below.
    for hx, hy in fan_mount_points:
        through = (cq.Workplane("XY")
                   .center(hx, hy)
                   .circle(front_screw_clearance_dia / 2.0)
                   .extrude(front_thick + 2.0)
                   .translate((0, 0, front_z - 1.0)))
        counterbore = (cq.Workplane("XY")
                       .center(hx, hy)
                       .circle(front_screw_counterbore_dia / 2.0)
                       .extrude(front_screw_counterbore_depth + 0.2)
                       .translate((0, 0, front_z + front_thick - front_screw_counterbore_depth)))
        cover = cover.cut(through).cut(counterbore)
    # Blind eye pockets (2 mm deep) — gives the 黑色方眼 look without exposing
    # the fan blades. Fill with black paint or do a filament swap on the top
    # 2 mm of the print.
    eye_depth = 2.0
    for ex in (-26, 26):
        eye_cut = (cq.Workplane("XY")
                   .center(ex, head_cy + 2)
                   .box(12, 12, eye_depth, centered=(True, True, False))
                   .translate((0, 0, front_z + front_thick - eye_depth)))
        cover = cover.cut(eye_cut)
    # Grille: 6 radial bars (30°) + concentric ring at r=30 + small hub.
    # The ring splits each 30° wedge into smaller openings and braces the
    # cover centre against finger / airflow deflection.
    bar_th = 3.0
    bar_len = fan_bore_dia - 20
    rib_extrude = front_thick - 1.0
    ribs = None
    for ang_deg in (0, 30, 60, 90, 120, 150):
        rib = (cq.Workplane("XY")
               .rect(bar_len, bar_th)
               .extrude(rib_extrude)
               .translate((0, body_cy, front_z + 0.5))
               .rotate((0, body_cy, 0), (0, body_cy, 1), ang_deg))
        ribs = rib if ribs is None else ribs.union(rib)
    ring_r = 30.0
    ring = (cq.Workplane("XY").center(0, body_cy)
            .circle(ring_r + bar_th / 2).circle(ring_r - bar_th / 2)
            .extrude(rib_extrude)
            .translate((0, 0, front_z + 0.5)))
    ribs = ribs.union(ring)
    hub = (cq.Workplane("XY").center(0, body_cy)
           .circle(8.0).extrude(rib_extrude)
           .translate((0, 0, front_z + 0.5)))
    ribs = ribs.union(hub)
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
    # Serviceable wiring gutter. The user's photos show the fan harness and
    # PWM controller living along one fan side, so the cable path is kept in
    # the right side rail instead of crossing the blade opening or climbing
    # into the head.
    wire_gutter = (cq.Workplane("XY")
                   .center(wire_gutter_x, wire_gutter_y)
                   .box(wire_gutter_w_est,
                        wire_gutter_len_est,
                        wire_gutter_depth_est,
                        centered=True)
                   .translate((0, 0, wire_gutter_z)))
    shell = shell.cut(wire_gutter)
    plug_pocket = (cq.Workplane("XY")
                   .center(wire_gutter_x, plug_pocket_y)
                   .box(plug_pocket_w_est,
                        plug_pocket_len_est,
                        plug_pocket_depth_est,
                        centered=True)
                   .translate((0, 0, rear_z_top - plug_pocket_depth_est / 2.0 + 0.2)))
    shell = shell.cut(plug_pocket)
    side_exit = (cq.Workplane("XY")
                 .center(body_w / 2.0 + 2.0, side_exit_y)
                 .box(16.0, side_exit_w_est, side_exit_h_est, centered=True)
                 .translate((0, 0, rear_z_top - side_exit_h_est / 2.0 + 1.0)))
    shell = shell.cut(side_exit)
    boss_height = rear_thick - 0.2
    boss_base_z = rear_z_top - rear_thick + 0.1
    for hx, hy in fan_mount_points:
        boss = (cq.Workplane("XY")
                .center(hx, hy)
                .circle(rear_screw_boss_dia / 2.0)
                .extrude(boss_height)
                .translate((0, 0, boss_base_z)))
        pilot = (cq.Workplane("XY")
                 .center(hx, hy)
                 .circle(rear_screw_boss_pilot_dia / 2.0)
                 .extrude(boss_height + 2.0)
                 .translate((0, 0, boss_base_z - 1.0)))
        shell = shell.union(boss).cut(pilot)
    for clip_y in wire_clip_y_positions:
        clip = (cq.Workplane("XY")
                .center(wire_gutter_x, clip_y)
                .box(wire_clip_w_est, wire_clip_len_est, wire_clip_thick_est, centered=True)
                .translate((0, 0, rear_z_top - 0.2)))
        shell = shell.union(clip)
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
    """Spine on top of the head, slightly wider than the head so the seam
    reads as an intentional brow / ledge rather than a separate add-on.
    The former main cable route moved to the side gutter; this remains a small
    optional downward relief channel for future LED or sensor wires."""
    spine_w = head_w + 6.0                  # 110 — slightly wider than head
    spine_h_y = 22.0
    spine_thick = 16.0
    spine_cy = head_cy + head_h / 2 - 4
    spine_cz = rear_z_top + spine_thick / 2.0 - 0.2
    spine = (cq.Workplane("XY").center(0, spine_cy)
             .box(spine_w, spine_h_y, spine_thick)
             .translate((0, 0, spine_cz)))
    spine = spine.edges("|Z").fillet(2.5)
    channel = (cq.Workplane("XY").center(0, spine_cy)
               .box(spine_w - 12, cable_h_est + 1, 11, centered=(True, True, False))
               .translate((0, 0, spine_cz - spine_thick / 2 - 0.1)))
    return spine.cut(channel)


# --- Right-side control pod ---
def make_control_pod():
    """Imported controller reference shell, placed on the right side."""
    ref_path = Path(__file__).parent.parent / "docs" / "refs" / controller_reference_step
    pod = cq.importers.importStep(str(ref_path))
    pod = pod.translate(tuple(-v for v in controller_reference_center))
    pod = pod.rotate((0, 0, 0), (0, 0, 1), controller_reference_rotation_deg)
    return pod.translate(controller_reference_target)


# --- Wedge feet (fixed 15° tilt) ---
def make_wedge_feet():
    foot_w_x = 36.0
    pts = [
        (foot_fy0, foot_z_top),
        (foot_fy1, foot_z_top),
        (foot_fy1, foot_z_top - foot_back),
        (foot_fy0, foot_z_top - foot_front),
    ]
    feet = None
    for x_center in (-leg_dx, leg_dx):
        prof = cq.Workplane("YZ").polyline(pts).close()
        foot = prof.extrude(foot_w_x).translate((x_center - foot_w_x / 2, 0, 0))
        foot = foot.edges("|X").fillet(1.5)
        feet = foot if feet is None else feet.union(foot)
    return feet


# --- Rear heel (third support point) ---
def make_rear_heel():
    """Tilted heel whose bottom face lies on the same 15° desk plane as the
    wedge feet — so the device gets real three-point support instead of
    rocking on the feet. Narrowed to fit between the legs (no overlap with
    the wedge feet)."""
    heel_w = 2 * (leg_dx - leg_w / 2) - 8           # 46 — clears both feet
    heel_h_y = 28.0
    heel_cy = leg_cy + 4
    fy0 = heel_cy - heel_h_y / 2                    # -90
    fy1 = heel_cy + heel_h_y / 2                    # -62
    z_top = foot_z_top
    pts = [
        (fy0, z_top),
        (fy1, z_top),
        (fy1, desk_z(fy1)),
        (fy0, desk_z(fy0)),
    ]
    prof = cq.Workplane("YZ").polyline(pts).close()
    heel = prof.extrude(heel_w).translate((-heel_w / 2, 0, 0))
    heel = heel.edges("|X").fillet(2.0)
    return heel


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
