// Universal desktop stand for Waveshare ESP32-S3-ePaper-3.97.
// This is a first-print stand, not a full enclosure.
// It avoids relying on exact screw hole positions: the board sits in a front lip
// and leans against a rear rail. Measure the real board before designing a full case.

part = "all"; // "all", "base", "rear_rail"

$fn = 48;

stand_width = 142;
stand_depth = 72;
base_thickness = 5;
front_lip_height = 10;
front_lip_depth = 8;
rear_rail_height = 52;
rear_rail_thickness = 8;
lean_angle = 72;
cable_slot_width = 18;
battery_clearance_width = 72;
battery_clearance_depth = 34;

module rounded_box(w, d, h, r) {
  hull() {
    translate([r, r, 0]) cylinder(h = h, r = r);
    translate([w - r, r, 0]) cylinder(h = h, r = r);
    translate([r, d - r, 0]) cylinder(h = h, r = r);
    translate([w - r, d - r, 0]) cylinder(h = h, r = r);
  }
}

module base() {
  difference() {
    union() {
      rounded_box(stand_width, stand_depth, base_thickness, 4);
      translate([0, 0, base_thickness])
        rounded_box(stand_width, front_lip_depth, front_lip_height, 3);
      translate([0, stand_depth - rear_rail_thickness, base_thickness])
        rounded_box(stand_width, rear_rail_thickness, rear_rail_height, 3);
    }

    // Type-C cable exit at the center rear.
    translate([(stand_width - cable_slot_width) / 2, stand_depth - rear_rail_thickness - 1, base_thickness + 8])
      cube([cable_slot_width, rear_rail_thickness + 2, 22]);

    // Lighten the base and leave room for a thin LiPo pouch.
    translate([(stand_width - battery_clearance_width) / 2, 18, -1])
      rounded_box(battery_clearance_width, battery_clearance_depth, base_thickness + 2, 4);
  }
}

module rear_rail() {
  rotate([lean_angle - 90, 0, 0])
    rounded_box(stand_width, rear_rail_thickness, rear_rail_height, 3);
}

if (part == "base") {
  base();
} else if (part == "rear_rail") {
  rear_rail();
} else {
  base();
}
