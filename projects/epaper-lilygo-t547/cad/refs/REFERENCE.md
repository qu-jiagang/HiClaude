# LilyGo Screen-4.7-S3 Full Enclosure V15 Notes

## Assembly Change

- The screen and PCB are assumed to be bonded first with thin 3M double-sided
  tape.
- Because the board is almost the same footprint as the screen, the bonded
  stack can be positioned as a single rigid module.
- The enclosure no longer uses screen snap latches or screen support pads.
- The four internal PCB screw bosses have been removed; the bonded stack is
  retained by the flush front fit and adhesive.
- The former rear cover is now fused into the main enclosure body rather than
  exported as a separate printable cover.

## Flush Screen Intent

- `main_body.step` is now the fused enclosure body with a flush top opening.
- The screen face is intended to sit level with the top edge of the shell.
- No printed lip crosses over the screen face.
- Exact flushness depends on the real bonded stack height; the current model
  assumes about 8.2 mm from PCB to screen face, including about 0.2 mm tape.

## PCB Boss Removal

- The four rear-cover PCB bosses are no longer generated.
- The matching bottom screw clearance holes and screw head pockets are also
  removed from `main_body.step`.

## Printability Tuning

- Current body envelope is about 122.3 x 68.3 x 16.5 mm.
- The side wall was increased to about 1.58 mm for a more reliable FDM print.
- The rear cover is now 2.1 mm thick, and the removable battery door panel is
  1.0 mm thick.
- The battery door tabs/snap and the side-button heat-stake posts were slightly
  enlarged so the small service parts are less fragile.
- The battery door lower snap is now a lower-profile, easier-engaging latch,
  with larger receiver clearance and longer flex relief slots.
- The battery retainer is sized for an 82 x 51 x 4 mm battery and uses taller
  1.8 mm rails on the removable battery door.

## Openings

- The -X long side matches `/home/midea/Downloads/h716_032n_frm.stl`: one
  button-left SD slot at y -9.75..4.75 and three button windows at
  y 8.05..13.15, 16.55..21.65, and 26.05..31.15. The upper narrow slots at
  y about -20 and y about 40 are intentionally not generated.
- The +Y short side matches the source STL wide opening at x -15.30..-0.70.
- The previous small end notch is no longer generated.

## Split

- `main_body.step`: fused flush side shell and rear cover, with the former PCB
  screw bosses removed.
- `buttons.step`: separate three-button insert.
- `battery_door.step`: separate sliding battery door.
