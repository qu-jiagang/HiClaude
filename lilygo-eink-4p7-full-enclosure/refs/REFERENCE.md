# LilyGo Screen-4.7-S3 Full Enclosure V15 Notes

## Assembly Change

- The screen and PCB are assumed to be bonded first with thin 3M double-sided
  tape.
- Because the board is almost the same footprint as the screen, the bonded
  stack can be positioned as a single rigid module.
- The enclosure no longer uses screen snap latches or screen support pads.
- PCB mounting screws from the rear/bottom define the final stack position.
- The former rear cover is now fused into the main enclosure body rather than
  exported as a separate printable cover.

## Flush Screen Intent

- `main_body.step` is now the fused enclosure body with a flush top opening.
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

- The -X long side matches `/home/midea/Downloads/h716_032n_frm.stl`: one
  button-left SD slot at y -9.75..4.75 and three button windows at
  y 8.05..13.15, 16.55..21.65, and 26.05..31.15. The upper narrow slots at
  y about -20 and y about 40 are intentionally not generated.
- The +Y short side matches the source STL wide opening at x -15.30..-0.70.
- The previous small end notch is no longer generated.

## Split

- `main_body.step`: fused flush side shell and rear cover with bottom-access PCB
  screw mounts.
- `buttons.step`: separate three-button insert.
- `battery_door.step`: separate sliding battery door.
