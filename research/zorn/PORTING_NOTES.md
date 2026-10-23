# Redmi K80 (zorn) porting notes

Status: research / bring-up planning. This is **not** a bootable device configuration.

## Target

- Device: Redmi K80
- Android codename: `zorn`
- SoC: Qualcomm SM8650 (`pineapple`)
- Current vendor baseline: HyperOS `OS4.0.0.13.XOKCN`, vendor Android 14 / SDK 34
- System build properties identify the generic system source as `missi`; this is expected and is not treated as a device mismatch.
- Kernel: `6.1.157-android14-11`, clang 17 build
- Bootloader: unlocked; current slot `_a`; A/B update enabled
- Host available: Ubuntu 26.04; no local macOS/Xcode host

## Porting guide audit

The repository's porting guide defines two device-specific repositories plus the shared UniXNU build framework:

1. `UniXNU-zorn`: `board.toml`, `configs/zorn_defconfig`, ADT generator, device scripts, device drivers/kits and package.
2. `uefi-zorn`: Mu-Silicium device platform, DSC/FDF, firmware configuration and preflight checks.
3. The shared `UniXNU` tree supplies the build driver, DarwinBoot, NativePrelink, generic drivers and shared XNU patches.

The documented bring-up order is UEFI -> UniXNU menu -> payload -> DarwinBoot -> XNU entry -> platform expert -> storage/root -> userland. A successful kernel compile or UEFI menu is not evidence that the next stage works.

The `sheng` reference is a method/example only. Its board file targets Xiaomi Pad 6S Pro / SM8550 and pins a specific iPadOS IPSW, KernelCache hash, prelink metadata, memory map, device drivers and UEFI platform. Do not copy those device-specific values to zorn.

## Confirmed read-only device observations

- `ro.product.device=zorn`; model `24117RK2CC`
- `ro.board.platform=pineapple`, `ro.soc.model=SM8650`, `ro.soc.manufacturer=QTI`
- System fingerprint: `Xiaomi/missi/missi:17/CP2A.260605.016/17OS4.0.260920.223526195.QCPECN.S:user/release-keys`
- Vendor fingerprint: `Redmi/zorn/zorn:14/UKQ1.240624.001/OS4.0.0.13.XOKCN:user/release-keys`
- Kernel command line includes `rootwait ro init=/init`; this is the stock Android kernel and does not establish an XNU boot path.
- Current slot is `_a`; A/B update is enabled.
- Readable block-name listing includes `boot_a/b`, `vendor_boot_a/b`, `init_boot_a/b`, `dtbo_a/b`, `vbmeta_a/b`, `uefi_a/b`, `super` and `userdata`. Presence of `uefi_a/b` alone does not prove they are safe or appropriate targets for a custom image.
- Direct reads of `/proc/device-tree/compatible` and `/sys/firmware/devicetree/base/{model,compatible}` were denied by Android permissions. Do not assume the nodes are absent.

## Important constraints

1. Do not copy `UniXNU-sheng`'s `board.toml`, defconfig, kernelcache hashes, prelink addresses, DTB fixups, UEFI config, or boot arguments as if they applied to zorn.
2. The generic UniXNU repository is a build framework, not a Redmi K80 port. A real port needs the dedicated device repository and a compatible Mu-Silicium UEFI platform.
3. The current `macos.yml` workflow uploads text logs only; it does not publish kernel/payload/boot-image artifacts. A successful CI run alone therefore cannot deliver a boot image.
4. The XNU kernel build step requires macOS/Xcode. Ubuntu can be used for source review and parts of the firmware/build preparation, but it is not a supported host for the kernel step.
5. Do not flash or erase partitions during early bring-up. Prefer a documented reversible RAM-boot test if the K80 bootloader supports it; verify device support and recovery procedure first.

## Same-SoC reference port

The UniXNU device index lists two community ports on SM8650, neither is a Redmi K80 port:

- OPPO Find X7 Ultra (`PHY120`): UEFI/menu works; kernel builds in CI, but payload discovery and prelink/device boot remain pending. This is useful as a UEFI/platform reference, not as a source of zorn constants.
- OnePlus Ace 5 (`giulia` / PKG110): its public project reports XNU entry and later userland/Setup progress on a different SM8650 board, with a Darwin 22 / iOS 16 target. Its `board.toml`, ADT generator, UFS and display details are board-specific. Use the architecture and staged diagnostic approach as a reference only; do not transplant memory maps, kernel arguments, UFS addresses, DT values or image pins.

This cross-reference means there is an SM8650 precedent worth studying before designing zorn from scratch. The remaining work is to compare its generic-vs-board-specific implementation and the official zorn device tree, then determine which UEFI components can be reused safely.

## Bring-up sequence

### Phase 0 — source and boot-chain research
- Match the public Xiaomi zorn kernel/device-tree source branch to the installed vendor build; do not infer an exact source match from the kernel's `android14` label alone.
- Identify the boot image header, AVB/vbmeta chain, ABL behavior, DTB/DTBO arrangement, UEFI partition role and a reversible test path.
- Extract or obtain stock boot-chain images and DT/DTBO from the exact installed build where technically and legally available.
- Identify a compatible Apple IPSW/kernelcache strategy for the UniXNU framework and document the ABI/prelink assumptions before writing a board configuration.

### Phase 1 — UEFI feasibility
- Establish a reproducible Mu-Silicium build for SM8650/zorn.
- Validate the boot image header, firmware base/size, GOP/framebuffer, storage visibility and serial/USB diagnostics.
- Keep the stock boot path untouched; use only a documented, reversible test method.

### Phase 2 — XNU kernel bring-up
- Add the zorn device repository and defconfig once the board values and source inputs are known.
- Confirm the XNU target configuration, compatible IPSW/kernelcache, prelink metadata, interrupt controller, timer, SMP, memory map and ADT handoff.
- First milestone is diagnostic kernel execution/panic output, not a graphical iOS boot.

### Phase 3 — storage and display
- Add device-specific UFS/storage and display support, then touch/input and power management.
- Treat GPU acceleration, Wi-Fi, Bluetooth, audio, sensors and cellular as separate later milestones.

### Phase 4 — iOS userspace
- Only after the kernel can reliably mount the expected APFS volumes and start essential services should the project attempt the iOS UI/SpringBoard path. A kernel boot does not imply a usable iOS system.

## First local diagnostics

Initial read-only ADB diagnostics are complete. Do not repeat them unless a new question requires it. Partition names are observations only; no partition writes have been performed.

## Current blocker

No verified zorn-specific UniXNU device repository/UEFI platform has been identified yet. Next work is source/boot-chain analysis and UEFI feasibility, not another round of generic property collection or a guessed `zorn_defconfig`.


## Official zorn device-tree source audit

Reviewed the Xiaomi public `kernel_devicetree` branch `bsp-zorn-v-oss` at tree commit `e6826f9350752ebceebee4d1d4ed20e0edf4d3a4`. Relevant files:

- `qcom/zorn-sm8650-overlay.dts` (blob `8b315d748f8696bd838b592409e13cc12bd27bb5`)
- `qcom/zorn-sm8650.dtsi` (blob `b5f14d2128432307d53959eaec75f44e69729adf`)
- `qcom/zorn-pinctrl.dtsi` (blob `53882a30fdc6594a0bb343232caccbcf6c59a78a`)
- `qcom/xiaomi-sm8650-common.dtsi` (blob `a45877e80823204521dfd16a3783f8db703c402c`)
- shared SoC source `qcom/pineapple.dtsi` (blob `2b94b3acd02a71ea9e7f5454de659b5720771fe1`)

The public zorn overlay declares:
- model: `Qualcomm Technologies, Inc. Zorn based on SM8650`
- compatible list: `qcom,pineapple-mtp`, `qcom,pineapple`, `qcom,pineapplep-mtp`, `qcom,pineapplep`, `qcom,mtp`
- `qcom,msm-id = <557 0x10000>, <557 0x20000>, <577 0x10000>, <577 0x20000>`
- `qcom,board-id = <8 0>`
- `xiaomi,miboard-id = <0xd 0>`

The zorn DTSI includes `zorn-pinctrl.dtsi` and `xiaomi-sm8650-common.dtsi`; the latter includes `pineapple-mtp.dtsi`. The zorn DTSI comments describe it as attribution/public platform attribution, so it must not be mistaken for a complete runtime DTB. These compatible strings and board IDs are **from the public source**, not a direct handset readback (ADB denied access to the live device-tree nodes).

The shared Pineapple DTSI shows an eight-core CPU topology and the UFS alias `ufshc1 = &ufshc_mem`, but these are Linux DT descriptions, not values to copy directly into an Apple Device Tree. ADT structure, memory ownership and interrupt/timer properties still need to be derived for the actual XNU handoff.

## First implementation scaffold

Added a non-buildable staging area at `porting/zorn/` on this branch:

- `README.md`: scope, evidence rules and promotion gates.
- `board.toml.template`: required UniXNU board schema with build-blocking `example = true`; no guessed IPSW, KernelCache pin, slide, DRAM window or UEFI FD base.
- `configs/zorn_defconfig.template`: conservative first-entry feature selection; no UFS, display, GPU or other unqualified hardware I/O enabled.

These are intentionally templates, not a working port or a valid boot image. The framework's own contribution guide says board-specific files belong in a dedicated `UniXNU-zorn` repository and firmware platform code in `uefi-zorn`; this staging directory is for review before splitting those repositories.

## Next source-level task

Inspect the exact zorn stock boot image / vendor_boot / DTB chain and identify whether a device-specific Mu-Silicium platform can be derived from the existing Qualcomm platform package. Then pin a supported Apple IPSW/kernelcache and validate the prelink inputs. No partition writes or flash commands are part of this phase.


## Boot-chain research note

Added [`porting/zorn/BOOT_CHAIN_RESEARCH.md`](porting/zorn/BOOT_CHAIN_RESEARCH.md), comparing public zorn Android build configurations and separating their packaging hints from the still-unknown exact stock image chain. The note records boot-header-v4 / separate init_boot-vendor_boot-dtbo conventions seen in community build configs, but explicitly does not treat these as proof of the active HyperOS image layout or permission to write any partition.
