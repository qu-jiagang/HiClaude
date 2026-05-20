# LilyGo Screen-4.7-S3 Full Enclosure V15 Notes

## Assembly Change

- The screen and PCB are assumed to be bonded first with thin 3M double-sided
  tape.
- Because the board is almost the same footprint as the screen, the bonded
  stack can be positioned as a single rigid module.
- The enclosure no longer uses screen snap latches or screen support pads.
- PCB mounting screws from the rear/bottom define the final stack position.

## Flush Screen Intent

- `main_body.step` is now a clean side shell with a flush top opening.
- The screen face is intended to sit level with the top edge of the shell.
- No printed lip crosses over the screen face.
- Exact flushness depends on the real bonded stack height; the current model
  assumes about 8.2 mm from PCB mounting plane to screen face, including about
  0.2 mm tape.

## Rear Screw Mounts

- Rear-cover PCB bosses now have through holes for bottom screw access.
- Screw clearance: 2.4 mm.
- Screw head pocket: 4.6 mm diameter x 1.0 mm deep.
- Boss diameter: 5.8 mm.

## Openings

- Long GPIO relief slot remains removed.
- Buttons remain as three separate small side windows.
- USB-C, SD, and JST windows remain constrained to their local connector zones.

## Split

- `main_body.step`: flush side shell.
- `rear_cover.step`: removable back cover with battery support and bottom-access
  PCB screw mounts.
