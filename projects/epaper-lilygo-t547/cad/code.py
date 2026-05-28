import cadquery as cq
import math

# LilyGo Screen-4.7-S3 flush-screen enclosure v17.
# Strict dimensional reference: refs/h716_032n_4.stp
#   - h716_032n_001 (screen):  66.5 x 120 x 2.2 mm
#   - h716_032n_4   (board):   63 x 118.5 PCB body, four M3 holes at the
#                              corner positions used below
# The case outer footprint matches the screen exactly; the screen sits on top
# of the wall edges and is bonded with adhesive. From above, the screen is
# the only visible surface.

# Outer envelope (= screen outline, perfectly flush).
screen_width = 66.5
screen_length = 120.0
screen_thickness = 2.2
screen_corner_radius = 1.2
outer_width = screen_width
outer_length = screen_length
outer_radius = screen_corner_radius

# PCB envelope (bottom face) measured from refs/h716_032n_4.stp solid #0.
pcb_width = 63.0
pcb_length = 118.5
pcb_clearance = 0.1
inner_cavity_width = pcb_width + 2.0 * pcb_clearance
inner_cavity_length = pcb_length + 2.0 * pcb_clearance

# Wall thicknesses computed automatically (X is generous, Y is intentionally
# slim because the screen barely overhangs the PCB on the short ends).
side_wall = (outer_width - inner_cavity_width) / 2.0
end_wall = (outer_length - inner_cavity_length) / 2.0

# Rear cover plus shell. Screen sits *above* the shell, so shell_height is
# total_device_height minus rear cover and minus screen thickness.
rear_cover_thickness = 2.1
shell_height = 13.2
total_device_height = rear_cover_thickness + shell_height + screen_thickness

# Battery cell (kept at user-specified 51 x 82 x 4; the STEP reference battery
# at 48.68 x 85.2 x 7.4 is too thick for the compact 16.5 mm shell).
battery_cell_width = 51.0
battery_cell_length = 82.0
battery_cell_thickness = 4.0
battery_clearance = 0.8
battery_pocket_width = battery_cell_width + 2.0 * battery_clearance
battery_pocket_length = battery_cell_length + 2.0 * battery_clearance
battery_pocket_x = 0.0
battery_pocket_y = 0.0
battery_rail_thickness = 1.4
battery_rail_height = battery_cell_thickness
battery_rail_fillet_radius = 0.12
battery_rail_outer_width = battery_pocket_width + battery_rail_thickness
battery_rail_outer_length = battery_pocket_length + battery_rail_thickness

# Rear ventilation slots live in the narrow side bands outside the centered
# battery pocket.
rear_vent_slot_width = 2.2
rear_vent_slot_length = 9.5
rear_vent_slot_radius = 0.9
rear_vent_cut_depth = rear_cover_thickness + 1.0
rear_vent_x_positions = (-30.0, 30.0)
rear_vent_y_positions = (-28.0, -12.0, 4.0, 20.0, 36.0)

# Adhesive-bonded screen + PCB stack.
adhesive_tape_thickness = 0.2
screen_board_stack_height = 8.7

# Four PCB mount bosses transferred from h716_032n_4.stp (centered to the
# enclosure origin). The +X bottom corner is offset inward to clear the
# USB-C connector on the development board.
m3_boss_positions = (
    (-27.0, -54.25),
    (+16.5, -54.25),
    (-27.0, +54.25),
    (+27.0, +54.25),
)
m3_boss_outer_diameter = 7.6
m3_boss_pilot_diameter = 2.5
m3_clearance_diameter = 3.4
m3_countersink_top_diameter = 6.3
m3_countersink_depth = 1.65
m3_boss_top_z = total_device_height - screen_board_stack_height
m3_boss_height = m3_boss_top_z - rear_cover_thickness

# Connector and control cutouts transferred from h716_032n_frm.stl. Local
# frame is 76 x 128 x 15.7 with center frame x[-38,38], y[-64,64],
# z[-2.55,13.15].
h716_frame_width = 76.0
h716_frame_length = 128.0
h716_frame_z_min = -2.55
h716_frame_height = 15.7
h716_pcb_bottom_z = 6.95
h716_z_offset = m3_boss_top_z - h716_pcb_bottom_z
h716_io_z_lift = 4.0


def h716_x(value):
    return value


def h716_y(value):
    return value


def h716_z(value):
    return value + h716_z_offset


def h716_io_z(value):
    return h716_z(value) + h716_io_z_lift


h716_left_side_cutouts = [
    ("sd_slot", -9.75, 4.75, -2.55, 8.05),
    ("button_1", 8.05, 13.15, 1.516, 8.05),
    ("button_2", 16.55, 21.65, 1.516, 8.05),
    ("button_3", 26.05, 31.15, 1.516, 8.05),
]
h716_end_side_cutouts = [
    ("wide_end_opening", -15.30, -0.70, 1.25, 10.05),
]

button_cut_length = h716_y(13.15 - 8.05)
button_cut_height = h716_io_z(8.05) - h716_io_z(1.516)
button_y_positions = tuple(
    h716_y((y_min + y_max) / 2.0)
    for name, y_min, y_max, _z_min, _z_max in h716_left_side_cutouts
    if name.startswith("button")
)
button_cut_z = (h716_io_z(1.516) + h716_io_z(8.05)) / 2.0
button_cap_depth = 3.2
button_cap_length = 4.4
button_cap_height = 4.2
button_carrier_depth = 1.8
button_carrier_length = 25.0
button_carrier_height = 2.0
button_switch_center_x = -30.15
button_switch_center_z = h716_io_z((4.95 + 6.95) / 2.0)
button_cap_center_z = button_switch_center_z
button_flex_gap = 1.1
button_stem_depth = 6.0
button_stem_length = 2.4
button_stem_height = 2.2
button_stem_center_x = button_switch_center_x
button_stem_center_z = button_switch_center_z
button_motion_clearance_depth = button_stem_depth + 0.9
button_motion_clearance_length = button_stem_length + 0.9
button_motion_clearance_height = button_stem_height + 0.9
button_heat_stake_diameter = 1.6
button_heat_stake_hole_diameter = 1.95
button_heat_stake_length = 2.2
button_heat_stake_tip_allowance = 0.45

side_opening_depth = 7.0

# Separate removable side-clip feet. These are exported as an independent
# accessory STEP and are not fused into the enclosure body.
clip_clearance = 0.18
clip_grip_height = rear_cover_thickness + shell_height
clip_span_y = 20.0
clip_y_positions = (-38.0, 38.0)
clip_profile_x0 = -3.8
clip_profile_x1 = 17.0
clip_base_height_z = 3.4
clip_display_tilt_deg = 18.0
clip_front_roll_radius = 2.2
clip_back_wall_x0 = 2.0
clip_back_wall_x1 = 5.0
clip_back_wall_height_z = 15.0
clip_back_top_radius = 1.3

# Validation-only bridges to make a single connected assembly for zero-to-cad.
validation_bridge_width = 1.0
validation_bridge_length = 4.0
validation_bridge_height = 1.0


def rounded_prism(width, length, height, radius):
    r = min(radius, width / 2.0 - 0.05, length / 2.0 - 0.05)
    body = cq.Workplane("XY").rect(width - 2.0 * r, length).extrude(height)
    body = body.union(cq.Workplane("XY").rect(width, length - 2.0 * r).extrude(height))
    for x in (-width / 2.0 + r, width / 2.0 - r):
        for y in (-length / 2.0 + r, length / 2.0 - r):
            corner = cq.Workplane("XY").circle(r).extrude(height).translate((x, y, 0))
            body = body.union(corner)
    return body


def rounded_box(width, length, height, radius):
    return rounded_prism(width, length, height, radius)


def rounded_cutter(width, length, height, radius, center):
    return rounded_prism(width, length, height, radius).translate(center)


def rear_vent_cutter(x, y):
    return rounded_prism(
        rear_vent_slot_width,
        rear_vent_slot_length,
        rear_vent_cut_depth,
        rear_vent_slot_radius,
    ).translate((x, y, -0.5))


def side_clip_foot(y_center):
    side_x = outer_width / 2.0
    tilt_drop = (clip_profile_x1 - clip_profile_x0) * math.tan(math.radians(clip_display_tilt_deg))
    base_bottom_inner_z = -clip_base_height_z - clip_clearance
    base_bottom_outer_z = base_bottom_inner_z - tilt_drop
    profile = (
        cq.Workplane("XZ")
        .polyline(
            [
                (side_x + clip_profile_x0, base_bottom_inner_z),
                (side_x + clip_profile_x1, base_bottom_outer_z),
                (side_x + clip_profile_x1, -clip_clearance),
                (side_x + clip_back_wall_x1, -clip_clearance),
                (side_x + clip_back_wall_x1, clip_back_wall_height_z - clip_back_top_radius),
                (side_x + clip_back_wall_x1 - 0.35, clip_back_wall_height_z),
                (side_x + clip_back_wall_x0 + 0.35, clip_back_wall_height_z),
                (side_x + clip_back_wall_x0, clip_back_wall_height_z - clip_back_top_radius),
                (side_x + clip_back_wall_x0, 0.75),
                (side_x + 0.25, 0.75),
                (side_x + 0.25, -clip_clearance),
                (side_x + clip_profile_x0, -clip_clearance),
            ]
        )
        .close()
        .extrude(clip_span_y)
        .translate((0.0, y_center + clip_span_y / 2.0, 0.0))
    )
    front_roll = (
        cq.Workplane("XZ")
        .circle(clip_front_roll_radius)
        .extrude(clip_span_y)
        .translate((side_x + clip_profile_x0 + clip_front_roll_radius, y_center + clip_span_y / 2.0, -clip_front_roll_radius - clip_clearance))
    )
    back_top_round = (
        cq.Workplane("XZ")
        .circle(clip_back_top_radius)
        .extrude(clip_span_y)
        .translate((side_x + (clip_back_wall_x0 + clip_back_wall_x1) / 2.0, y_center + clip_span_y / 2.0, clip_back_wall_height_z - clip_back_top_radius))
    )
    foot = profile.union(front_roll, clean=False).union(back_top_round, clean=False)
    try:
        foot = foot.edges("|Y").fillet(0.35)
    except Exception:
        pass
    return foot


def m3_through_cutter(boss_x, boss_y):
    # Cone-shape countersink for an M3 flat-head, followed by a cylindrical
    # clearance shaft, and a self-tap pilot up through the boss.
    over_top = (
        cq.Workplane("XY")
        .circle(m3_countersink_top_diameter / 2.0)
        .extrude(0.1)
        .translate((boss_x, boss_y, -0.1))
    )
    countersink = (
        cq.Workplane("XY")
        .circle(m3_countersink_top_diameter / 2.0)
        .workplane(offset=m3_countersink_depth)
        .circle(m3_clearance_diameter / 2.0)
        .loft(combine=True)
        .translate((boss_x, boss_y, 0))
    )
    clearance = (
        cq.Workplane("XY")
        .circle(m3_clearance_diameter / 2.0)
        .extrude(rear_cover_thickness - m3_countersink_depth + 0.1)
        .translate((boss_x, boss_y, m3_countersink_depth))
    )
    pilot = (
        cq.Workplane("XY")
        .circle(m3_boss_pilot_diameter / 2.0)
        .extrude(m3_boss_height + 0.2)
        .translate((boss_x, boss_y, rear_cover_thickness))
    )
    return over_top.union(countersink).union(clearance).union(pilot)


# ---------------------------------------------------------------------------
# Main side shell. Cavity sized for the PCB; open on top so the bonded
# screen/PCB stack drops in from above and the screen rests on the wall edges.
# ---------------------------------------------------------------------------
inner_cavity_radius = max(0.6, outer_radius - min(side_wall, end_wall))
side_shell = rounded_box(outer_width, outer_length, shell_height, outer_radius).translate((0, 0, rear_cover_thickness))
side_cavity = rounded_cutter(
    inner_cavity_width,
    inner_cavity_length,
    shell_height + 2.0,
    inner_cavity_radius,
    (0, 0, rear_cover_thickness - 0.5),
)
main_body = side_shell.cut(side_cavity)

front_z = rear_cover_thickness + shell_height
right_edge_x = outer_width / 2.0
left_edge_x = -outer_width / 2.0
side_opening_cutters = []
end_opening_cutters = []

for name, y_min, y_max, z_min, z_max in h716_left_side_cutouts:
    cut_center_y = h716_y((y_min + y_max) / 2.0)
    cut_length = h716_y(y_max - y_min)
    cut_center_z = (h716_io_z(z_min) + h716_io_z(z_max)) / 2.0
    cut_height = h716_io_z(z_max) - h716_io_z(z_min)
    side_cut = (
        cq.Workplane("XY")
        .box(side_opening_depth, cut_length, cut_height, centered=True)
        .translate((left_edge_x, cut_center_y, cut_center_z))
    )
    side_opening_cutters.append(side_cut)
    main_body = main_body.cut(side_cut)

for name, x_min, x_max, z_min, z_max in h716_end_side_cutouts:
    cut_center_x = h716_x((x_min + x_max) / 2.0)
    cut_width = h716_x(x_max - x_min)
    cut_center_z = (h716_io_z(z_min) + h716_io_z(z_max)) / 2.0
    cut_height = h716_io_z(z_max) - h716_io_z(z_min)
    end_cut = (
        cq.Workplane("XY")
        .box(cut_width, side_opening_depth, cut_height, centered=True)
        .translate((cut_center_x, outer_length / 2.0, cut_center_z))
    )
    end_opening_cutters.append(end_cut)
    main_body = main_body.cut(end_cut)

# Local motion clearance for the separate button insert.
for button_y in button_y_positions:
    motion_clearance = (
        cq.Workplane("XY")
        .box(
            button_motion_clearance_depth,
            button_motion_clearance_length,
            button_motion_clearance_height,
            centered=True,
        )
        .translate((button_stem_center_x, button_y, button_stem_center_z))
    )
    main_body = main_body.cut(motion_clearance)

# Three-button heat-stake posts on the main body and the matching insert.
button_center_y = sum(button_y_positions) / len(button_y_positions)
button_carrier_center_x = left_edge_x + side_wall + button_flex_gap
button_carrier_center_z = button_stem_center_z
button_cut_y_ranges = tuple(
    (h716_y(y_min), h716_y(y_max))
    for name, y_min, y_max, _z_min, _z_max in h716_left_side_cutouts
    if name.startswith("button")
)
button_heat_stake_y_positions = (
    (button_cut_y_ranges[0][1] + button_cut_y_ranges[1][0]) / 2.0,
    (button_cut_y_ranges[1][1] + button_cut_y_ranges[2][0]) / 2.0,
)
button_heat_stake_start_x = left_edge_x + side_wall - 0.15

for stake_y in button_heat_stake_y_positions:
    stake = (
        cq.Workplane("YZ")
        .circle(button_heat_stake_diameter / 2.0)
        .extrude(button_heat_stake_length)
        .translate((button_heat_stake_start_x, stake_y, button_carrier_center_z))
    )
    main_body = main_body.union(stake)

button_bar = (
    cq.Workplane("XY")
    .box(button_carrier_depth, button_carrier_length, button_carrier_height, centered=True)
    .translate((button_carrier_center_x, button_center_y, button_carrier_center_z))
)
for button_y in button_y_positions:
    stem = (
        cq.Workplane("XY")
        .box(button_stem_depth, button_stem_length, button_stem_height, centered=True)
        .translate((button_stem_center_x, button_y, button_stem_center_z))
    )
    cap = (
        cq.Workplane("XY")
        .box(button_cap_depth, button_cap_length, button_cap_height, centered=True)
        .translate((left_edge_x - button_cap_depth / 2.0 + 0.25, button_y, button_cap_center_z))
    )
    button_bar = button_bar.union(stem).union(cap)

for stake_y in button_heat_stake_y_positions:
    stake_hole = (
        cq.Workplane("YZ")
        .circle(button_heat_stake_hole_diameter / 2.0)
        .extrude(button_carrier_depth + button_heat_stake_tip_allowance + 0.6)
        .translate((button_carrier_center_x - button_carrier_depth / 2.0 - 0.3, stake_y, button_carrier_center_z))
    )
    button_bar = button_bar.cut(stake_hole)

side_clip_feet = side_clip_foot(clip_y_positions[0]).union(side_clip_foot(clip_y_positions[1]), clean=False)

# ---------------------------------------------------------------------------
# Rear cover (solid). The battery, rails, and four M3 bosses now live on
# the inside; the outside face shows only the four flush countersinks.
# ---------------------------------------------------------------------------
rear_cover = rounded_box(outer_width, outer_length, rear_cover_thickness, outer_radius)

# Battery retainer rails, attached to the inside of the rear cover.
rail_z_center = rear_cover_thickness + battery_rail_height / 2.0
for x in (
    battery_pocket_x - battery_pocket_width / 2.0,
    battery_pocket_x + battery_pocket_width / 2.0,
):
    rail = (
        cq.Workplane("XY")
        .box(battery_rail_thickness, battery_rail_outer_length, battery_rail_height, centered=True)
        .translate((x, battery_pocket_y, rail_z_center))
    )
    rear_cover = rear_cover.union(rail)

for y in (
    battery_pocket_y - battery_pocket_length / 2.0,
    battery_pocket_y + battery_pocket_length / 2.0,
):
    rail = (
        cq.Workplane("XY")
        .box(battery_rail_outer_width, battery_rail_thickness, battery_rail_height, centered=True)
        .translate((battery_pocket_x, y, rail_z_center))
    )
    rear_cover = rear_cover.union(rail)

for vent_x in rear_vent_x_positions:
    for vent_y in rear_vent_y_positions:
        rear_cover = rear_cover.cut(rear_vent_cutter(vent_x, vent_y))

# Four M3 mount bosses and matching countersink + clearance cuts.
for boss_x, boss_y in m3_boss_positions:
    boss = (
        cq.Workplane("XY")
        .circle(m3_boss_outer_diameter / 2.0)
        .extrude(m3_boss_height)
        .translate((boss_x, boss_y, rear_cover_thickness))
    )
    rear_cover = rear_cover.union(boss)
    rear_cover = rear_cover.cut(m3_through_cutter(boss_x, boss_y))

# ---------------------------------------------------------------------------
# Final assembly.
# ---------------------------------------------------------------------------
enclosure_body = main_body.union(rear_cover, clean=False)
for opening_cut in side_opening_cutters + end_opening_cutters:
    enclosure_body = enclosure_body.cut(opening_cut, clean=False)

# Single validation bridge connecting the separate button insert to the main
# body. Spans the small gap between the side wall inner face and the carrier
# outer face at a y-position between button_1 and button_2 where the wall has
# no cutout.
_wall_inner_x = left_edge_x + side_wall
_carrier_outer_x = button_carrier_center_x - button_carrier_depth / 2.0
button_validation_bridge = (
    cq.Workplane("XY")
    .box(_carrier_outer_x - _wall_inner_x + 1.0, 2.0, 1.0, centered=True)
    .translate(((_wall_inner_x + _carrier_outer_x) / 2.0, button_heat_stake_y_positions[0], button_carrier_center_z))
)

result = (
    enclosure_body
    .union(button_bar, clean=False)
    .union(button_validation_bridge, clean=False)
)
