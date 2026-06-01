"""FD14 Claude Pixel Fan Enclosure — multi-piece printable assembly.

Generated via the zero-to-cad skill (Z2C agentic CAD synthesis loop).

Reference: design.md + concept-06-fixed-15deg.png in this directory.

Assembly method: the fan sits in the rear_shell pocket without screw holes;
                 a separate dark radial grille seats over the front opening.
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
    parts/front_grille.step / .stl
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
# DeepCool FD14 official frame dimensions: 140 × 140 × 25 mm.
# 12_14CM_DesktopFan.3mf reference Mainbody inner side planes:
# X = ±70.952 mm -> 141.904 mm usable fan slot width.
fan_w = 140.0
fan_h = 140.0
fan_thick = 25.0
fan_slot_w_ref = 141.904
fan_slot_h_ref = 141.904
fan_xy_clearance_ref = (fan_slot_w_ref - fan_w) / 2.0
fan_bore_dia = 132.0

# Fixed dark front grille styled after concept-05-wedge-feet.png.
front_grille_outer_dia = 128.0
front_grille_ring_w = 2.8
front_grille_ring_radii = (22.0, 40.0, 58.0)
front_grille_spoke_w = 2.8
front_grille_spoke_count = 12
front_grille_hub_dia = 18.0
front_grille_thick = 2.8

# Pixel-robot silhouette, redesigned around the fan as the face center.
body_w = 184.0
body_h = 164.0
body_cy = 2.0
head_w = 178.0
head_h = 30.0
head_cy = 88.0
eye_dx = 62.0
eye_cy = 88.0
eye_size = 16.0
arm_w = 28.0
arm_h = 42.0
arm_dx = 106.0
arm_cy = 22.0
leg_w = 30.0
leg_h = 42.0
leg_dx = 42.0
leg_cy = -88.0
fillet_r = 1.25

# Z layout
fan_z_clearance = 0.3
front_thick = 4.0
front_z = fan_thick / 2.0 + fan_z_clearance      # +13.3
rear_thick = 24.0
rear_z_top = -fan_thick / 2.0 - fan_z_clearance  # -13.3
rear_duct_depth = 10.0
rear_duct_outer_dia = 148.0
rear_duct_inner_dia = 126.0
rear_duct_attach_overlap = 1.5
rear_guard_bar_w = 3.4
rear_guard_thick = 2.4

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
side_exit_y = 0.0

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


assembly_method = "fan_pocket_side_gutter_to_imported_controller_shell"

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
    front_bore = (cq.Workplane("XY")
                  .center(0, body_cy)
                  .circle(fan_bore_dia / 2 - 4)
                  .extrude(front_thick + 2.0)
                  .translate((0, 0, front_z - 1.0)))
    cover = cover.cut(front_bore)
    # Blind eye pockets (2 mm deep) — gives the 黑色方眼 look without exposing
    # the fan blades. Fill with black paint or do a filament swap on the top
    # 2 mm of the print.
    eye_depth = 2.0
    for ex in (-eye_dx, eye_dx):
        eye_cut = (cq.Workplane("XY")
                   .center(ex, eye_cy)
                   .box(eye_size, eye_size, eye_depth, centered=(True, True, False))
                   .translate((0, 0, front_z + front_thick - eye_depth)))
        cover = cover.cut(eye_cut)
    return cover


# --- Dark circular front grille ---
def make_front_grille():
    """Separate radial grille matching the concept image's fan-forward face."""
    grille_z = front_z + front_thick + 0.4
    outer_r = front_grille_outer_dia / 2.0
    outer_ring = (cq.Workplane("XY").center(0, body_cy)
                  .circle(outer_r)
                  .circle(outer_r - front_grille_ring_w)
                  .extrude(front_grille_thick)
                  .translate((0, 0, grille_z)))
    grille = outer_ring
    for ring_r in front_grille_ring_radii:
        ring = (cq.Workplane("XY").center(0, body_cy)
                .circle(ring_r + front_grille_ring_w / 2.0)
                .circle(ring_r - front_grille_ring_w / 2.0)
                .extrude(front_grille_thick)
                .translate((0, 0, grille_z)))
        grille = grille.union(ring)
    for index in range(front_grille_spoke_count):
        angle_deg = index * 360.0 / front_grille_spoke_count
        spoke = (cq.Workplane("XY")
                 .rect(front_grille_outer_dia - 2.0 * front_grille_ring_w,
                       front_grille_spoke_w)
                 .extrude(front_grille_thick)
                 .translate((0, body_cy, grille_z))
                 .rotate((0, body_cy, 0), (0, body_cy, 1), angle_deg))
        grille = grille.union(spoke)
    hub = (cq.Workplane("XY").center(0, body_cy)
           .circle(front_grille_hub_dia / 2.0)
           .extrude(front_grille_thick)
           .translate((0, 0, grille_z)))
    mask = (cq.Workplane("XY").center(0, body_cy)
            .circle(outer_r)
            .extrude(front_grille_thick + 1.0)
            .translate((0, 0, grille_z - 0.5)))
    return grille.union(hub).intersect(mask)


# --- Rear shell ---
def make_rear_shell():
    shell = silhouette(rear_thick, rear_z_top - rear_thick)
    pocket_depth = rear_thick - 3.0
    fan_pocket = (cq.Workplane("XY").center(0, body_cy)
                  .box(fan_slot_w_ref,
                       fan_slot_h_ref,
                       pocket_depth,
                       centered=(True, True, False))
                  .translate((0, 0, rear_z_top - pocket_depth)))
    shell = shell.cut(fan_pocket)
    rear_bore = (cq.Workplane("XY")
                 .center(0, body_cy)
                 .circle(fan_bore_dia / 2 - 2)
                 .extrude(rear_thick + 4.0)
                 .translate((0, 0, rear_z_top - rear_thick - 2.0)))
    shell = shell.cut(rear_bore)
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
    for clip_y in wire_clip_y_positions:
        clip = (cq.Workplane("XY")
                .center(wire_gutter_x, clip_y)
                .box(wire_clip_w_est, wire_clip_len_est, wire_clip_thick_est, centered=True)
                .translate((0, 0, rear_z_top - 0.2)))
        shell = shell.union(clip)
    # Low-profile rear exhaust cage. This replaces the separate-looking
    # flared cone with a short fan-like back ring that shares the same center
    # as the front opening and overlaps the shell bottom for a true fused body.
    duct_z0 = rear_z_top - rear_thick + rear_duct_attach_overlap
    duct_back_z = duct_z0 - rear_duct_depth
    rear_ring = (cq.Workplane("XY").center(0, body_cy)
                 .circle(rear_duct_outer_dia / 2.0)
                 .circle(rear_duct_inner_dia / 2.0)
                 .extrude(rear_duct_depth)
                 .translate((0, 0, duct_back_z)))
    guard = None
    for ang_deg in (0, 30, 60, 90, 120, 150):
        bar = (cq.Workplane("XY")
               .rect(rear_duct_outer_dia - 8.0, rear_guard_bar_w)
               .extrude(rear_guard_thick)
               .translate((0, body_cy, duct_back_z))
               .rotate((0, body_cy, 0), (0, body_cy, 1), ang_deg))
        guard = bar if guard is None else guard.union(bar)
    rear_hub = (cq.Workplane("XY").center(0, body_cy)
                .circle(10.0)
                .extrude(rear_guard_thick)
                .translate((0, 0, duct_back_z)))
    rear_mask = (cq.Workplane("XY").center(0, body_cy)
                 .circle(rear_duct_inner_dia / 2.0 + 2.0)
                 .extrude(rear_guard_thick + 1.0)
                 .translate((0, 0, duct_back_z - 0.5)))
    guard = guard.union(rear_hub).intersect(rear_mask)
    return shell.union(rear_ring).union(guard)


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
    ("front_grille", make_front_grille, DARK),
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
