import cadquery as cq

# LilyGo Screen-4.7-S3 compact enclosure v15.
# Assembly split:
#   enclosure_body = fused side shell and rear cover
#   battery_door/buttons = separate removable/service parts

# Compact footprint driven directly by the user's measured 120 x 66 mm front.
screen_width = 66.0
screen_length = 120.0
compact_outer_delta = 3.8
outer_shrink_width = 1.5
outer_shrink_length = 1.5
outer_width = screen_width + compact_outer_delta - outer_shrink_width
outer_length = screen_length + compact_outer_delta - outer_shrink_length
screen_corner_radius = 1.2
outer_radius = 1.5

# Fit and wall parameters.
screen_press_clearance = 0.65
screen_opening_width = screen_width + screen_press_clearance
screen_opening_length = screen_length + screen_press_clearance
side_wall = (outer_width - screen_opening_width) / 2.0
rear_cover_thickness = 2.1
shell_height = 14.4
total_height = rear_cover_thickness + shell_height

# Rear cover inside features.
rear_lip_height = 1.0
rear_lip_clearance = 0.45
rear_lip_outer_width = screen_opening_width - rear_lip_clearance
rear_lip_outer_length = screen_opening_length - rear_lip_clearance
rear_lip_wall = 1.0
rear_lip_radius = screen_corner_radius - 0.4

battery_cell_width = 51.0
battery_cell_length = 82.0
battery_cell_thickness = 4.0
battery_clearance = 0.8
thermal_barrier_thickness = 1.0
battery_pocket_width = battery_cell_width + 2.0 * battery_clearance
battery_pocket_length = battery_cell_length + 2.0 * battery_clearance
battery_pocket_x = 0.0
battery_pocket_y = 0.0
battery_rail_thickness = 1.4
battery_rail_height = 4.0
battery_rail_fillet_radius = 0.12
battery_rail_outer_width = battery_pocket_width + battery_rail_thickness
battery_rail_outer_length = battery_pocket_length + battery_rail_thickness

# Centered removable battery door. The rear cover has an outside shallow seat,
# a smaller through opening, and the separate cover has a locating plug.
battery_door_opening_width = battery_pocket_width + 4.0
battery_door_opening_length = battery_pocket_length + 4.0
battery_door_recess_margin = 2.0
battery_door_recess_width = battery_door_opening_width + 2.0 * battery_door_recess_margin
battery_door_recess_length = battery_door_opening_length + 2.0 * battery_door_recess_margin
battery_door_recess_depth = 1.1
battery_door_panel_clearance = 0.35
battery_door_panel_thickness = battery_door_recess_depth - 0.1
battery_door_panel_width = battery_door_recess_width - 2.0 * battery_door_panel_clearance
battery_door_panel_length = battery_door_recess_length - 2.0 * battery_door_panel_clearance
battery_door_plug_clearance = 0.35
battery_door_plug_width = battery_door_opening_width - 2.0 * battery_door_plug_clearance
battery_door_plug_length = battery_door_opening_length - 2.0 * battery_door_plug_clearance
battery_door_plug_height = rear_cover_thickness - battery_door_recess_depth
battery_door_radius = 1.2
battery_door_finger_notch_width = 14.0
battery_door_finger_notch_length = 5.0
battery_door_grip_y = -battery_door_panel_length / 2.0 + 5.0
battery_door_tab_width = 10.0
battery_door_tab_length = 2.0
battery_door_tab_height = 0.8
battery_door_tab_x_offset = 13.5
battery_door_tab_overlap = 1.6
battery_door_receiver_clearance = 0.35
battery_door_snap_width = 9.0
battery_door_snap_length = 1.4
battery_door_snap_height = 0.45
battery_door_snap_overlap = 0.9
battery_door_latch_chamfer = 0.15
battery_door_flex_slot_width = 1.8
battery_door_flex_slot_length = 24.0
battery_door_flex_slot_x_offset = 8.0

# Rear-cover perimeter vents are intentionally empty now: after the battery
# door was centered, the side bands became too narrow for useful vents.
rear_vent_cut_height = rear_cover_thickness + 0.6
rear_vent_cut_z = -0.3
rear_vent_slots = []

# Vent pattern on the removable battery door itself. These through-slots sit
# away from the finger notch, latch ribs, and battery retaining rails.
battery_door_vent_slot_width = 2.4
battery_door_vent_slot_length = 8.0
battery_door_vent_cut_height = battery_door_panel_thickness + battery_door_plug_height + 0.8
battery_door_vent_cut_z = -0.4
battery_door_vent_slots = [
    # width, length, x, y
    (battery_door_vent_slot_width, battery_door_vent_slot_length, -12.0, -24.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 0.0, -24.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 12.0, -24.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, -12.0, -12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 0.0, -12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 12.0, -12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, -12.0, 0.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 0.0, 0.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 12.0, 0.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, -12.0, 12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 0.0, 12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 12.0, 12.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, -12.0, 24.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 0.0, 24.0),
    (battery_door_vent_slot_width, battery_door_vent_slot_length, 12.0, 24.0),
]

# Board support/mount bosses were removed from the main body. The screen/PCB
# stack is retained by its front fit and adhesive instead of four internal
# posts that conflict with the battery bay and add unnecessary print detail.
adhesive_tape_thickness = 0.2
screen_board_stack_height = 8.2

bat_pad_x = -1.0
bat_pad_y = 4.0
wire_channel_width = 3.2
wire_channel_depth = 0.7
side_opening_depth = 7.0

# No front snap retention in this revision. Screen and PCB are first bonded as
# one stack, then seated into the flush front opening.

# Connector and control cutouts in the side shell. These boxes are transferred
# directly from h716_032n_frm.stl, whose frame is 76 x 128 x 15.7 mm and has a
# local center frame of x[-38, 38], y[-64, 64], z[-2.55, 13.15].
h716_frame_width = 76.0
h716_frame_length = 128.0
h716_frame_z_min = -2.55
h716_frame_height = 15.7


def h716_x(value):
    return value


def h716_y(value):
    return value


def h716_z(value):
    return value - h716_frame_z_min


# Side features copied from the H716 frame. Some are bottom-open notches rather
# than fully enclosed holes, so the cutter spans from the lower edge upward.
h716_left_side_cutouts = [
    # name, local y min, local y max, local z min, local z max
    ("sd_slot", -9.75, 4.75, -2.55, 8.05),
    ("button_1", 8.05, 13.15, 1.516, 8.05),
    ("button_2", 16.55, 21.65, 1.516, 8.05),
    ("button_3", 26.05, 31.15, 1.516, 8.05),
]
h716_end_side_cutouts = [
    # name, local x min, local x max, local z min, local z max
    ("wide_end_opening", -15.30, -0.70, 1.25, 10.05),
]

button_cut_length = h716_y(13.15 - 8.05)
button_cut_height = h716_z(8.05) - h716_z(1.516)
button_y_positions = tuple(
    h716_y((y_min + y_max) / 2.0)
    for name, y_min, y_max, _z_min, _z_max in h716_left_side_cutouts
    if name.startswith("button")
)
button_cut_z = (h716_z(1.516) + h716_z(8.05)) / 2.0
button_cap_depth = 3.2
button_cap_length = 4.4
button_cap_height = 4.2
button_carrier_depth = 1.8
button_carrier_length = 25.0
button_carrier_height = 2.0
button_carrier_z_offset = -2.35
button_flex_gap = 1.1
button_stem_depth = 2.4
button_stem_length = 2.4
button_stem_height = 2.2
button_stem_z_offset = -2.1
button_motion_clearance_depth = button_stem_depth + 0.9
button_motion_clearance_length = button_stem_length + 0.9
button_motion_clearance_height = button_stem_height + 0.9
button_heat_stake_diameter = 1.6
button_heat_stake_hole_diameter = 1.95
button_heat_stake_length = 2.2
button_heat_stake_tip_allowance = 0.45

# Validation-only bridges are not exported in the separate printable parts.
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


def cut_centered_box(body, width, length, height, center):
    box = cq.Workplane("XY").box(width, length, height, centered=True).translate(center)
    return body.cut(box)


# ---------------------------------------------------------------------------
# Main side shell: flush side wall. The bonded screen/PCB stack is installed
# from the front and retained by the close flush fit plus adhesive.
# ---------------------------------------------------------------------------
side_shell = rounded_box(outer_width, outer_length, shell_height, outer_radius).translate((0, 0, rear_cover_thickness))
side_cavity = rounded_cutter(
    screen_opening_width,
    screen_opening_length,
    shell_height + 2.0,
    screen_corner_radius,
    (0, 0, rear_cover_thickness - 0.5),
)
main_body = side_shell.cut(side_cavity)

front_z = rear_cover_thickness + shell_height

# H716-derived side openings in main body.
# Layout:
#   -X long side: SD/long slot, then three button openings.
#   +Y short side: one wide end opening.
right_edge_x = outer_width / 2.0
left_edge_x = -outer_width / 2.0
side_opening_cutters = []
end_opening_cutters = []

for name, y_min, y_max, z_min, z_max in h716_left_side_cutouts:
    cut_center_y = h716_y((y_min + y_max) / 2.0)
    cut_length = h716_y(y_max - y_min)
    cut_center_z = (h716_z(z_min) + h716_z(z_max)) / 2.0
    cut_height = h716_z(z_max) - h716_z(z_min)
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
    cut_center_z = (h716_z(z_min) + h716_z(z_max)) / 2.0
    cut_height = h716_z(z_max) - h716_z(z_min)
    end_cut = (
        cq.Workplane("XY")
        .box(cut_width, side_opening_depth, cut_height, centered=True)
        .translate((cut_center_x, outer_length / 2.0, cut_center_z))
    )
    end_opening_cutters.append(end_cut)
    main_body = main_body.cut(end_cut)

# Local motion clearance for the separate button insert. The H716-derived side
# notches define the visible openings; these inner pockets keep each button
# stem from intersecting the shell wall during assembly and actuation.
for button_y in button_y_positions:
    motion_clearance = (
        cq.Workplane("XY")
        .box(
            button_motion_clearance_depth,
            button_motion_clearance_length,
            button_motion_clearance_height,
            centered=True,
        )
        .translate((left_edge_x + side_wall / 2.0, button_y, button_cut_z + button_stem_z_offset))
    )
    main_body = main_body.cut(motion_clearance)

# Separate three-button insert inspired by the H716 side-button part: three
# proud caps connected by a thin internal carrier strip. The strip is retained
# by two heat-stake posts molded into the main body, not by glue.
button_center_y = sum(button_y_positions) / len(button_y_positions)
button_carrier_center_x = left_edge_x + side_wall + button_flex_gap
button_carrier_center_z = button_cut_z + button_carrier_z_offset
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
        .translate((left_edge_x + side_wall / 2.0, button_y, button_cut_z + button_stem_z_offset))
    )
    cap = (
        cq.Workplane("XY")
        .box(button_cap_depth, button_cap_length, button_cap_height, centered=True)
        .translate((left_edge_x - button_cap_depth / 2.0 + 0.25, button_y, button_cut_z))
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

# ---------------------------------------------------------------------------
# Rear cover geometry: fused into the main enclosure body after its features
# are added. It is no longer exported as a separate part.
# ---------------------------------------------------------------------------
rear_cover = rounded_box(outer_width, outer_length, rear_cover_thickness, outer_radius)

battery_door_recess = rounded_cutter(
    battery_door_recess_width,
    battery_door_recess_length,
    battery_door_recess_depth + 0.2,
    battery_door_radius,
    (battery_pocket_x, battery_pocket_y, -0.1),
)
battery_door_opening = rounded_cutter(
    battery_door_opening_width,
    battery_door_opening_length,
    rear_cover_thickness + 0.8,
    battery_door_radius,
    (battery_pocket_x, battery_pocket_y, -0.4),
)
rear_cover = rear_cover.cut(battery_door_recess).cut(battery_door_opening)

# Internal receiver pockets for the sliding battery door: two upper insertion
# tongues slide under the cover edge, and one lower snap tooth catches here.
tab_receiver_y = battery_door_opening_length / 2.0 + battery_door_tab_overlap / 2.0
snap_receiver_y = -battery_door_opening_length / 2.0 - battery_door_snap_overlap / 2.0
receiver_z = battery_door_panel_thickness + battery_door_tab_height / 2.0 + 0.2
for tab_x in (-battery_door_tab_x_offset, battery_door_tab_x_offset):
    tab_receiver = (
        cq.Workplane("XY")
        .box(
            battery_door_tab_width + 2.0 * battery_door_receiver_clearance,
            battery_door_tab_overlap + 2.0 * battery_door_receiver_clearance,
            battery_door_tab_height + 0.5,
            centered=True,
        )
        .translate((tab_x, tab_receiver_y, receiver_z))
    )
    rear_cover = rear_cover.cut(tab_receiver)

snap_receiver = rounded_cutter(
    battery_door_snap_width + 2.0 * battery_door_receiver_clearance,
    battery_door_snap_overlap + 2.0 * battery_door_receiver_clearance,
    battery_door_snap_height + 0.5,
    battery_door_receiver_clearance,
    (0, snap_receiver_y, receiver_z),
)
rear_cover = rear_cover.cut(snap_receiver)

rear_lip = rounded_box(rear_lip_outer_width, rear_lip_outer_length, rear_lip_height, rear_lip_radius).translate((0, 0, rear_cover_thickness))
rear_lip_inner = rounded_cutter(
    rear_lip_outer_width - 2.0 * rear_lip_wall,
    rear_lip_outer_length - 2.0 * rear_lip_wall,
    rear_lip_height + 0.4,
    max(0.8, rear_lip_radius - rear_lip_wall),
    (0, 0, rear_cover_thickness - 0.2),
)
rear_cover = rear_cover.union(rear_lip.cut(rear_lip_inner))

# Battery retaining rails move with the removable door instead of floating on
# the rear-cover opening.
battery_retainer = None
for x in (
    battery_pocket_x - battery_pocket_width / 2.0,
    battery_pocket_x + battery_pocket_width / 2.0,
):
    rail = (
        cq.Workplane("XY")
        .box(battery_rail_thickness, battery_rail_outer_length, battery_rail_height, centered=True)
        .translate((x, battery_pocket_y, battery_door_panel_thickness + battery_door_plug_height + battery_rail_height / 2.0 - 0.15))
    )
    battery_retainer = rail if battery_retainer is None else battery_retainer.union(rail)

for y in (
    battery_pocket_y - battery_pocket_length / 2.0,
    battery_pocket_y + battery_pocket_length / 2.0,
):
    rail = (
        cq.Workplane("XY")
        .box(battery_rail_outer_width, battery_rail_thickness, battery_rail_height, centered=True)
        .translate((battery_pocket_x, y, battery_door_panel_thickness + battery_door_plug_height + battery_rail_height / 2.0 - 0.15))
    )
    battery_retainer = rail if battery_retainer is None else battery_retainer.union(rail)

battery_retainer = battery_retainer.edges().fillet(battery_rail_fillet_radius)

# Wire channel toward BAT+/BAT- pads as shallow grooves in the cover interior.
wire_a = (
    cq.Workplane("XY")
    .box(abs(battery_pocket_x - bat_pad_x) + wire_channel_width, wire_channel_width, wire_channel_depth, centered=True)
    .translate(((battery_pocket_x + bat_pad_x) / 2.0, bat_pad_y, rear_cover_thickness + wire_channel_depth / 2.0))
)
wire_b = (
    cq.Workplane("XY")
    .box(wire_channel_width, abs(battery_pocket_y - bat_pad_y) + wire_channel_width, wire_channel_depth, centered=True)
    .translate((battery_pocket_x, (battery_pocket_y + bat_pad_y) / 2.0, rear_cover_thickness + wire_channel_depth / 2.0))
)
rear_cover = rear_cover.cut(wire_a).cut(wire_b)

# Through vents on the rear face. They stay clear of battery rails and wire
# channels.
for vent_width, vent_length, vent_x, vent_y in rear_vent_slots:
    vent = rounded_cutter(
        vent_width,
        vent_length,
        rear_vent_cut_height,
        min(vent_width, vent_length) / 2.0,
        (vent_x, vent_y, rear_vent_cut_z),
    )
    rear_cover = rear_cover.cut(vent)

# Separate removable battery door. It sits in the outside recess and uses a
# shallow inner plug plus small latch ribs to locate against the through opening.
battery_door = rounded_box(
    battery_door_panel_width,
    battery_door_panel_length,
    battery_door_panel_thickness,
    battery_door_radius,
)
battery_door_plug = rounded_box(
    battery_door_plug_width,
    battery_door_plug_length,
    battery_door_plug_height,
    max(0.8, battery_door_radius - 0.2),
).translate((0, 0, battery_door_panel_thickness))
battery_door = battery_door.union(battery_door_plug)

tab_y = battery_door_opening_length / 2.0 + battery_door_tab_overlap / 2.0 - battery_door_receiver_clearance
tab_z = battery_door_panel_thickness + battery_door_tab_height / 2.0 + 0.2
snap_z = battery_door_panel_thickness + battery_door_plug_height - battery_door_snap_height / 2.0
for tab_x in (-battery_door_tab_x_offset, battery_door_tab_x_offset):
    tab = (
        cq.Workplane("XY")
        .box(battery_door_tab_width, battery_door_tab_length, battery_door_tab_height, centered=True)
        .edges()
        .chamfer(battery_door_latch_chamfer)
        .translate((tab_x, tab_y, tab_z))
    )
    battery_door = battery_door.union(tab)

snap_y = -battery_door_opening_length / 2.0 - battery_door_snap_overlap / 2.0 + battery_door_receiver_clearance
snap = (
    cq.Workplane("XY")
    .box(battery_door_snap_width, battery_door_snap_length, battery_door_snap_height, centered=True)
    .edges()
    .chamfer(battery_door_latch_chamfer)
    .translate((0, snap_y, snap_z))
)
battery_door = battery_door.union(snap)

for slot_x in (-battery_door_flex_slot_x_offset, battery_door_flex_slot_x_offset):
    flex_slot = rounded_cutter(
        battery_door_flex_slot_width,
        battery_door_flex_slot_length,
        battery_door_panel_thickness + battery_door_plug_height + battery_door_snap_height + 0.8,
        battery_door_flex_slot_width / 2.0,
        (slot_x, -battery_door_plug_length / 2.0 + 8.0, -0.4),
    )
    battery_door = battery_door.cut(flex_slot)

finger_notch = rounded_cutter(
    battery_door_finger_notch_width,
    battery_door_finger_notch_length,
    battery_door_panel_thickness + 0.6,
    battery_door_finger_notch_length / 2.0,
    (0, battery_door_grip_y, -0.3),
)
battery_door = battery_door.cut(finger_notch)

for vent_width, vent_length, vent_x, vent_y in battery_door_vent_slots:
    vent = rounded_cutter(
        vent_width,
        vent_length,
        battery_door_vent_cut_height,
        min(vent_width, vent_length) / 2.0,
        (vent_x, vent_y, battery_door_vent_cut_z),
    )
    battery_door = battery_door.cut(vent)

# Keep the battery retaining frame continuous. The door's vent and flex cuts
# happen first so they cannot leave open gaps in the four-sided retainer.
battery_door = battery_door.union(battery_retainer)

enclosure_body = main_body.union(rear_cover, clean=False)
for opening_cut in side_opening_cutters + end_opening_cutters:
    enclosure_body = enclosure_body.cut(opening_cut, clean=False)
printable_assembly = enclosure_body.union(button_bar, clean=False).union(battery_door, clean=False)

# Validation-only bridges to make a single connected assembly for zero-to-cad.
validation_bridge_z = rear_cover_thickness + validation_bridge_height / 2.0
validation_bridge_y = -outer_length / 2.0 + 2.0
bridge_left = (
    cq.Workplane("XY")
    .box(validation_bridge_width, validation_bridge_length, validation_bridge_height, centered=True)
    .translate((-screen_opening_width / 2.0, validation_bridge_y, validation_bridge_z))
)
bridge_right = (
    cq.Workplane("XY")
    .box(validation_bridge_width, validation_bridge_length, validation_bridge_height, centered=True)
    .translate((screen_opening_width / 2.0, validation_bridge_y, validation_bridge_z))
)
button_validation_bridge = (
    cq.Workplane("XY")
    .box(2.0, 2.0, 1.0, centered=True)
    .translate((left_edge_x + 0.4, button_center_y, button_cut_z + button_carrier_z_offset))
)
battery_door_validation_bridge = (
    cq.Workplane("XY")
    .box(4.0, 5.0, 1.0, centered=True)
    .translate((0, -battery_door_recess_length / 2.0 + 0.1, 0.45))
)

result = (
    enclosure_body
    .union(bridge_left, clean=False)
    .union(bridge_right, clean=False)
    .union(button_bar, clean=False)
    .union(button_validation_bridge, clean=False)
    .union(battery_door, clean=False)
    .union(battery_door_validation_bridge, clean=False)
)
