"""
LilyGo T5-ePaper-S3 4.7" display mounted in the redrawn stand/shell.

Presentation STEP: the printable part is cad/lilygo_t5_47_desk_stand.step.
The display is kept as multiple solids so front/back/side views show the real
reference features instead of a single fused slab.

Output:
    cad/lilygo_t5_47_mounted.step
"""

from pathlib import Path
import cadquery as cq

board_w = 114.0
board_h = 63.0
board_t = 8.0
active_screen_w = 91.0
active_screen_h = 57.0
right_shoulder_w = board_w - active_screen_w
fit_clearance = 1.6

lean_angle = 72.0
shell_tilt = lean_angle - 90.0
base_w = 154.0
base_d = 82.0
base_t = 6.0
frame_w = board_w + 19.0
frame_h = board_h + 16.0
frame_t = 7.0
frame_y = 17.0
frame_z = base_t / 2 + frame_h / 2 - 1.0
front_lip_h = 13.0
front_lip_d = 12.0
rear_stop_h = 7.0
rear_stop_d = 4.0
tray_gap = board_t + fit_clearance

rear_window_w = 108.0
rear_window_h = 51.0
screw_boss_r = 4.8
screw_hole_r = 1.55
screw_head_r = 3.3
screw_head_depth = 1.4
screw_x = frame_w / 2 - 8.5
screw_z = frame_h / 2 - 8.0
kick_w = 28.0
kick_d = 43.0
kick_h = 38.0
side_rib_w = 6.0
side_rib_d = 43.0
side_rib_h = 42.0
side_rib_x = board_w / 2 - 14.0

OUT = Path(__file__).parent if "__file__" in globals() else None


def rounded_box(width, depth, height, radius):
    safe_radius = min(radius, width / 2 - 0.05, depth / 2 - 0.05)
    box = cq.Workplane("XY").box(width, depth, height)
    if safe_radius <= 0:
        return box
    return box.edges("|Z").fillet(safe_radius)


def place_on_frame(part, x=0.0, y=0.0, z=0.0):
    return (
        part.translate((x, y, z))
        .rotate((0, 0, 0), (1, 0, 0), shell_tilt)
        .translate((0, frame_y, frame_z))
    )


def frame_cylinder(radius, depth, x, z):
    return place_on_frame(cq.Workplane("XZ").circle(radius).extrude(depth), x=x, z=z)


def screw_boss(x, z):
    return frame_cylinder(screw_boss_r, frame_t + 1.0, x, z)


def screw_cut(x, z):
    through = frame_cylinder(screw_hole_r, frame_t + 10.0, x, z)
    head = frame_cylinder(screw_head_r, screw_head_depth + 1.0, x, z)
    return through.union(head)


def triangular_side_rib(x):
    y0 = -base_d / 2 + front_lip_d + tray_gap + 8.0
    y1 = y0 + side_rib_d
    z0 = base_t / 2
    z1 = z0 + side_rib_h
    return (
        cq.Workplane("YZ")
        .polyline([(y0, z0), (y1, z0), (y1, z1), (y0 + 7.0, z0 + 5.0)])
        .close()
        .extrude(side_rib_w, both=True)
        .translate((x, 0, 0))
    )


def rear_kickstand():
    y0 = -base_d / 2 + front_lip_d + tray_gap + 12.0
    y1 = y0 + kick_d
    z0 = base_t / 2
    z1 = z0 + kick_h
    return (
        cq.Workplane("YZ")
        .polyline([(y0, z0), (y1, z0), (y1, z1), (y0 + 8.0, z0 + 6.0)])
        .close()
        .extrude(kick_w, both=True)
        .edges("|X")
        .fillet(2.0)
    )


base = rounded_box(base_w, base_d, base_t, 5.0)
front_lip = rounded_box(base_w - 10.0, front_lip_d, front_lip_h, 3.0).translate(
    (0, -base_d / 2 + front_lip_d / 2, base_t / 2 + front_lip_h / 2)
)
front_lip = front_lip.cut(
    rounded_box(34.0, front_lip_d + 4.0, front_lip_h + 2.0, 3.0).translate(
        (0, -base_d / 2 + front_lip_d / 2, base_t / 2 + front_lip_h - 1.5)
    )
)
rear_stop = rounded_box(base_w - 26.0, rear_stop_d, rear_stop_h, 1.2).translate(
    (
        0,
        -base_d / 2 + front_lip_d + tray_gap + rear_stop_d / 2,
        base_t / 2 + rear_stop_h / 2,
    )
)
frame_outer = place_on_frame(rounded_box(frame_w, frame_t, frame_h, 2.4))
frame = (
    frame_outer.union(screw_boss(-screw_x, screw_z))
    .union(screw_boss(screw_x, screw_z))
    .union(screw_boss(-screw_x, -screw_z))
    .union(screw_boss(screw_x, -screw_z))
    .cut(place_on_frame(rounded_box(rear_window_w, frame_t + 34.0, rear_window_h, 3.0), x=-1.0))
    .cut(screw_cut(-screw_x, screw_z))
    .cut(screw_cut(screw_x, screw_z))
    .cut(screw_cut(-screw_x, -screw_z))
    .cut(screw_cut(screw_x, -screw_z))
    .cut(place_on_frame(rounded_box(31.0, frame_t + 42.0, 18.0, 2.0), x=frame_w / 2 - 4.0, z=-frame_h / 2 + 23.0))
    .cut(place_on_frame(rounded_box(25.0, frame_t + 42.0, 10.0, 1.4), x=-8.0, z=-frame_h / 2 + 8.0))
    .cut(place_on_frame(rounded_box(38.0, frame_t + 42.0, 8.0, 1.4), x=30.0, z=-frame_h / 2 + 8.0))
    .cut(place_on_frame(rounded_box(23.0, frame_t + 42.0, 15.0, 2.0), x=frame_w / 2 - 16.0, z=-frame_h / 2 + 7.0))
)
stand = (
    base.union(front_lip)
    .union(rear_stop)
    .union(frame)
    .union(rear_kickstand())
    .union(triangular_side_rib(-side_rib_x))
    .union(triangular_side_rib(side_rib_x))
)

# Local display coordinates: X width, Y normal, Z height.
front_y = -frame_t / 2 - 5.2
back_y = frame_t / 2 + 2.0
paper = rounded_box(board_w, 1.4, board_h, 2.0).translate((0, front_y, 0))
active_x = -(right_shoulder_w - 4.0) / 2
active = rounded_box(active_screen_w, 1.0, active_screen_h, 0.5).translate((active_x, front_y - 1.2, 0))
right_shoulder = rounded_box(right_shoulder_w + 2.0, 1.2, active_screen_h, 0.5).translate(
    (board_w / 2 - (right_shoulder_w + 2.0) / 2 - 2.0, front_y - 1.4, 0)
)
screen_outline = []
outline_x = active_x
outline_w = active_screen_w + 2.0
outline_h = active_screen_h + 2.0
screen_outline.append(rounded_box(outline_w, 0.8, 1.2, 0.2).translate((outline_x, front_y - 2.0, outline_h / 2)))
screen_outline.append(rounded_box(outline_w, 0.8, 1.2, 0.2).translate((outline_x, front_y - 2.0, -outline_h / 2)))
screen_outline.append(rounded_box(1.2, 0.8, outline_h, 0.2).translate((outline_x - outline_w / 2, front_y - 2.0, 0)))
screen_outline.append(rounded_box(1.2, 0.8, outline_h, 0.2).translate((outline_x + outline_w / 2, front_y - 2.0, 0)))
logo_mark = rounded_box(7.5, 0.7, 2.0, 0.2).translate((board_w / 2 - 10.5, front_y - 2.2, board_h / 2 - 9.0))

pcb = rounded_box(board_w, 1.6, board_h, 2.6).translate((0, back_y, 0))
header = rounded_box(86.0, 3.0, 4.0, 0.6).translate((-7.0, back_y + 2.0, board_h / 2 - 5.0))
pin_parts = []
for i in range(22):
    pin_parts.append(
        rounded_box(1.8, 2.0, 2.0, 0.2).translate((-48.0 + i * 4.0, back_y + 4.0, board_h / 2 - 5.0))
    )
esp32 = rounded_box(20.0, 4.0, 16.0, 0.8).translate((board_w / 2 - 18.0, back_y + 4.0, board_h / 2 - 18.0))
usb_c = rounded_box(10.0, 6.0, 7.0, 0.8).translate((board_w / 2 + 1.0, back_y + 4.5, -board_h / 2 + 19.0))
tf_slot = rounded_box(17.0, 3.0, 14.0, 0.8).translate((-4.0, back_y + 3.2, -board_h / 2 + 9.0))
buttons = []
for x in (16.0, 28.0, 40.0):
    buttons.append(rounded_box(6.5, 3.0, 4.5, 0.7).translate((x, back_y + 3.5, -board_h / 2 + 5.0)))
jst = rounded_box(8.0, 6.0, 7.0, 0.7).translate((board_w / 2 - 21.0, back_y + 4.5, -board_h / 2 + 15.0))
battery_wire = rounded_box(18.0, 2.0, 2.0, 0.6).translate((board_w / 2 - 7.0, back_y + 6.0, -board_h / 2 + 12.0))

local_parts = [
    paper,
    active,
    right_shoulder,
    logo_mark,
    pcb,
    header,
    esp32,
    usb_c,
    tf_slot,
    jst,
    battery_wire,
    *screen_outline,
    *pin_parts,
    *buttons,
]
device_parts = [place_on_frame(part).val() for part in local_parts]

result = cq.Compound.makeCompound([stand.val(), *device_parts])

if OUT is not None:
    cq.exporters.export(result, str(OUT / "lilygo_t5_47_mounted.step"))
    face_count = len(stand.faces().vals()) + sum(len(part.Faces()) for part in device_parts)
    print("STEP -> cad/lilygo_t5_47_mounted.step")
    print("Parts: redrawn stand/shell + separated LilyGo T5-ePaper-S3 reference geometry")
    print(f"Faces: {face_count}")
