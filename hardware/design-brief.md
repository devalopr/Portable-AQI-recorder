# AQI recorder design brief

> **Status (V3):** this is the original product brief, written for Rev A. The current main board is [rev-b/main](rev-b/main/README.md), which supersedes the Rev A sizes and decisions below. The battery board sections now belong to the separate [18650-USB-C-UPS](https://github.com/devalopr/18650-USB-C-UPS) repo. Rev A files and the early research it mentions are in git history (commit `34dd5cf`).

The implementation and current decisions are documented in the Rev A README (git history; the current board is described in [rev-b/main](rev-b/main/README.md)). Main PCB size is 44 × 80 mm, following the user's request to stay close to 80 mm. The TFT uses a rear top-contact connector; its flex contacts face away from the board. The battery board uses a standard 65 mm cell with PCB protection and a 10-way JST GH internal link.

The final KiCad files are engineering review prototypes. See the validation report and release items in the README before fabrication. Earlier circuit proposals under references/early-research are superseded.
