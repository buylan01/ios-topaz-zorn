# SM8650 reference audit for Redmi K80 (zorn)

Status: source-level audit only. No K80 image has been built or booted by this change. No device partitions have been written.

## Result in one sentence

There is already meaningful public iOS/XNU work on the same SM8650 SoC, especially the OnePlus Ace 5 (giulia), but no public evidence found in the reviewed sources of an existing Redmi K80/zorn iOS port. The giulia work is the closest functional reference; it is not a drop-in board port.

## Reference projects and verified state

### OnePlus Ace 5 / giulia — closest reference

- Project: https://github.com/tycykp/UniXNU-OnePlus-Ace5
- UniXNU device index: https://github.com/UniXNU/UniXNU/blob/main/docs/devices/giulia.md
- SoC: Qualcomm SM8650, same SoC family as Redmi K80.
- Public README dated 2026-10-23 reports UEFI handoff, XNU startup on CPU0 in a single-core configuration, native UFS reads, USB CDC debug serial, HFSX root mount, and iOS Hello/Setup with full display and aligned touch.
- The same README marks GPU as preparation-only (no GPU execution/Metal), Wi-Fi as not yet firmware-ready in the latest device run, audio as experimental with no device playback, and cellular/DRM as unverified.
- The UniXNU device index summarizes this project as reaching Hello and Setup with display/touch; GPU and Wi-Fi remain pending.

Useful artifacts to inspect as design references:
- `.github/workflows/ios16-boot.yml`, `.github/workflows/ios16-uefi.yml`, `.github/workflows/ios16-xnu.yml`: split CI workflows are evidence of how the project separates UEFI, kernel and boot packaging.
- `board.toml`, `configs/giulia_defconfig`: board-specific inputs. Do not copy their values into zorn.
- `docs/DEVELOPMENT_STATUS.md`, `docs/DISPLAY_POWER.md`, `docs/USB_TERMINAL.md`, `docs/WIFI_FIRMWARE_READY.md`: staged validation and known limitations.
- `sources.json` and the target workflows pin source revisions; zorn should similarly record exact revisions and hashes.

### OnePlus Ace 5 / giulia — independent project

- Project listed by UniXNU: https://github.com/jasper2863/UniXNU-giulia
- The current URL returned 404 through the GitHub API during this audit, so its current public availability and details could not be independently verified. The UniXNU device index records the project as reaching a GUI progress bar, with installation service blocked. Treat that status as the index's statement, not as a freshly verified repository state.

### OPPO Find X7 Ultra / PHY120

- Device index: https://github.com/UniXNU/UniXNU/blob/main/docs/devices/phy120.md
- Same SM8650 SoC, different board.
- The index reports UEFI firmware/menu working and XNU building in CI, while payload discovery, prelink and device boot remain pending.
- This is useful for UEFI and build-framework comparison, but is behind giulia in verified XNU/userland milestones.

### Redmi K80 / zorn-related public repositories

Reviewed project index and known public Android/device-tree references. The search did not identify a public iOS/XNU port specifically for Redmi K80/zorn. This is not proof that no private, unindexed, or newly created project exists.

## What can transfer conceptually

| Area | What giulia proves is feasible on an SM8650 device | What zorn must still prove independently |
|---|---|---|
| Build system | An iOS 16 / Darwin 22 workflow can build and package for an SM8650 target. | Matching source pins, target config, XNU build and artifact integrity in this fork. |
| UEFI handoff | A community UEFI → XNU handoff is possible on a different SM8650 board. | Exact K80 ABL/UEFI chain, supported boot method, image format and reversible recovery path. |
| CPU and XNU entry | XNU can start on CPU0 in a single-core setup on giulia. | K80 EL/security state, CPU ID registers, boot MPIDR, timer, PSCI behavior, memory map and ADT. |
| Storage | Native UFS access and HFSX root mounting are possible on giulia. | K80 UFS controller mapping, PHY/clock/reset/power sequence, queue/interrupt behavior and safe test image. |
| Logging | USB CDC serial provides useful logs on giulia. | A working K80 debug channel before relying on panic output. UART candidate addresses are not confirmed merely by DT presence. |
| Display/input | Setup UI and aligned touch are reported on giulia. | K80 panel, DSI/MDP, display clocks, framebuffer ownership, touch controller and coordinate transform. |
| Wi-Fi/GPU/audio | These remain incomplete even on the reference, so they should not be early milestones. | Treat each as an independent later project after stable kernel, UFS and userspace. |

## K80 facts available before any port code

From the existing read-only research record:
- Device model: `24117RK2CC`; codename `zorn`; SoC `SM8650` / platform `pineapple`.
- Runtime Linux FDT model: `Qualcomm Technologies, Inc. Zorn based on SM8650`.
- Runtime FDT compatible list includes `qcom,pineapple-mtp`, `qcom,pineapple`, `qcom,pineapplep-mtp`, `qcom,pineapplep`, `qcom,mtp`.
- CPU cluster report: 2× Cortex-A520, 5× Cortex-A720, 1× Cortex-X4.
- GICv3 distributor base is DT-described at `0x17100000`; ITS at `0x17140000`. These are Linux DT observations, not yet validated as usable XNU mappings. The detailed research record reports redistributors starting at `0x17180000`.
- A candidate UART range `0x89c000` exists in the runtime DT, but Linux uses `console=ttynull`; physical accessibility and suitability remain unverified.
- Stock Android boot images are header v4, with separate boot/vendor_boot/init_boot/dtbo/vbmeta artifacts. The stock boot kernel is Linux, not XNU.
- The presence of `uefi_a/b` partitions does not establish that they are safe or appropriate to overwrite.

The Linux FDT is evidence for discovery only. Do not convert it mechanically into an Apple Device Tree, and do not treat any board-specific giulia values as zorn values.

## Immediate implementation plan

1. Keep the upstream `topaz` branch unchanged. Work on `migration/zorn-sm8650-bringup`.
2. Keep the ios-topaz iOS 16 / XNU `xnu-8796` path as the baseline, and add K80-specific work as isolated, numbered deltas. Do not transplant the UniXNU board framework or its prelink assumptions wholesale.
3. First establish a host-side build and artifact-validation path in GitHub Actions. Ubuntu 26.04 is the user's available host; no local macOS/Xcode is available.
4. Add a zorn research-only hardware manifest before any runtime code: exact source/hash provenance, CPU topology, reserved-memory map, GIC/timer, UFS candidate, console candidates and confidence level for each field.
5. Implement only non-destructive diagnostics first: a reproducible build, static validation of generated ADT/payload, then a minimal boot/logging path once image ABI and recovery have been documented.
6. Do not install an iOS root filesystem into `userdata` or write `boot`, `vendor_boot`, `dtbo`, `vbmeta`, or `uefi` partitions during this stage. A future RAM-boot test still requires explicit confirmation of the exact command/image and a verified return-to-stock plan.

## Acceptance gates

- [ ] Build job produces named artifacts and records source revisions and SHA-256 hashes.
- [ ] Static checks reject missing/placeholder board values and malformed ADT/payload.
- [ ] The runtime memory map accounts for all reserved/no-map regions before enabling an allocator.
- [ ] A logging path is demonstrated independently of the Linux `ttynull` console setting.
- [ ] CPU0 XNU entry and panic/log capture are reproducible before SMP is enabled.
- [ ] UFS read tests are read-only before any root-volume write is considered.
- [ ] Display/touch and then userland are separate milestones, not assumed from a kernel build.

## Sources

- https://github.com/tycykp/UniXNU-OnePlus-Ace5
- https://github.com/UniXNU/UniXNU/blob/main/docs/devices/giulia.md
- https://github.com/UniXNU/UniXNU/blob/main/docs/devices/phy120.md
- https://github.com/jasper2863/UniXNU-giulia (current API fetch returned 404 in this audit)
- Original K80 research previously staged at https://github.com/buylan01/UniXNU-xiaomi-zorn/tree/port/zorn-bringup-notes/porting/zorn

