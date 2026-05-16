// Parametric desktop stand for Waveshare 4.2" and 7.5" e-paper modules.
// Open in OpenSCAD. Export front, back and kickstand as separate STL files.

screen = "4in2"; // "4in2" or "7in5"
part = "all"; // "all", "front", "back", "kickstand"

$fn = 36;

module dims() {
}

screen_w = screen == "7in5" ? 170.2 : 103.0;
screen_h = screen == "7in5" ? 111.2 : 78.5;
view_w = screen == "7in5" ? 163.2 : 84.8;
view_h = screen == "7in5" ? 97.92 : 63.6;

bezel = 8;
wall = 3;
case_depth = 16;
corner = 5;
frame_w = screen_w + bezel * 2;
frame_h = screen_h + bezel * 2;
window_w = view_w + 3;
window_h = view_h + 3;

module rounded_box(w, h, d, r) {
  hull() {
    translate([r, r, 0]) cylinder(h = d, r = r);
    translate([w - r, r, 0]) cylinder(h = d, r = r);
    translate([r, h - r, 0]) cylinder(h = d, r = r);
    translate([w - r, h - r, 0]) cylinder(h = d, r = r);
  }
}

module screw_hole(x, y, d = 3.0) {
  translate([x, y, -1]) cylinder(h = 40, d = d);
}

module front_frame() {
  difference() {
    rounded_box(frame_w, frame_h, wall, corner);
    translate([(frame_w - window_w) / 2, (frame_h - window_h) / 2, -1])
      rounded_box(window_w, window_h, wall + 2, 2);
    screw_hole(8, 8);
    screw_hole(frame_w - 8, 8);
    screw_hole(8, frame_h - 8);
    screw_hole(frame_w - 8, frame_h - 8);
  }
}

module back_shell() {
  difference() {
    rounded_box(frame_w, frame_h, case_depth, corner);
    translate([wall, wall, wall])
      rounded_box(frame_w - wall * 2, frame_h - wall * 2, case_depth, corner - 1);
    translate([frame_w - 28, frame_h / 2 - 6, case_depth - 4])
      cube([30, 12, 8]);
    screw_hole(8, 8);
    screw_hole(frame_w - 8, 8);
    screw_hole(8, frame_h - 8);
    screw_hole(frame_w - 8, frame_h - 8);
  }
  translate([12, 12, wall])
    cylinder(h = case_depth - wall, d = 7);
  translate([frame_w - 12, 12, wall])
    cylinder(h = case_depth - wall, d = 7);
  translate([12, frame_h - 12, wall])
    cylinder(h = case_depth - wall, d = 7);
  translate([frame_w - 12, frame_h - 12, wall])
    cylinder(h = case_depth - wall, d = 7);
}

module kickstand() {
  stand_w = min(70, frame_w * 0.45);
  stand_h = screen == "7in5" ? 115 : 82;
  difference() {
    linear_extrude(height = 8)
      polygon(points = [[0, 0], [stand_w, 0], [stand_w * 0.64, stand_h], [stand_w * 0.36, stand_h]]);
    translate([stand_w / 2, stand_h - 12, -1])
      cylinder(h = 10, d = 4);
  }
}

if (part == "front") {
  front_frame();
} else if (part == "back") {
  back_shell();
} else if (part == "kickstand") {
  kickstand();
} else {
  translate([0, 0, case_depth]) front_frame();
  back_shell();
  translate([frame_w + 18, 0, 0]) kickstand();
}
