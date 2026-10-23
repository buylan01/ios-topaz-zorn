# zorn stock boot-chain research (read-only)

This note records what public Android device configuration tells us, and separates it from facts that still require the exact installed stock images. It is not a flash guide.

## Public device-tree / Android build evidence

Reviewed public device configuration files for Xiaomi `zorn`:

- Sakura-Devices `device_xiaomi_zorn/BoardConfig.mk` at commit `63cc02ced0ab7f1087ea4160f09796dae6066b38`: https://github.com/Sakura-Devices/device_xiaomi_zorn/blob/63cc02ced0ab7f1087ea4160f09796dae6066b38/BoardConfig.mk
- zorn-developement-sources `device_xiaomi_zorn/BoardConfig.mk` at commit `3e2738b19a8251e4c4ccdc3c0e54c6a35a59798e`: https://github.com/zorn-developement-sources/device_xiaomi_zorn/blob/3e2738b19a8251e4c4ccdc3c0e54c6a35a59798e/BoardConfig.mk
- AOSP device-tree dump `aosp-device-tree/BoardConfig.mk` at commit `a60e54dad830c23893593a2f7114569557760108`: https://github.com/Jiovanni-dump/redmi_zorn_dump/blob/a60e54dad830c23893593a2f7114569557760108/aosp-device-tree/BoardConfig.mk

These public configurations agree on the Android platform family and modern boot image conventions, but they are community ROM build configurations—not a forensic dump of the user's installed HyperOS build.

Useful signals in the ROM configs:

- Boot image header version 4 is configured.
- A/B slots and separate `init_boot`, `vendor_boot`, and `dtbo` partitions are used.
- `TARGET_USES_UEFI := true` appears in a community ROM configuration. This says that ROM's boot flow expects UEFI; it does **not** prove that the handset's `uefi_a/b` partition can be overwritten, that the public UEFI binary is compatible, or that fastboot RAM boot is supported.
- The Sakura config points at prebuilt DTB and DTBO assets and sets `BOARD_INCLUDE_DTB_IN_BOOTIMG := true`. The dump config also shows a DTB/DTBO arrangement. This is evidence that image packaging matters; it does not identify which DTB/DTBO is active on the currently installed build.
- The public ROM config contains partition sizes and AVB settings for building that ROM. Do not use those values to write partitions or infer the installed image's exact layout/signatures.

## What remains unknown

The following must be established from exact stock-build artifacts or a documented runtime handoff before constructing a test image:

1. Exact `boot`, `vendor_boot`, `init_boot`, `dtbo`, `vbmeta`, and any UEFI-related image versions for the installed OS build.
2. Boot image header fields, page size, kernel/ramdisk/DTB placement and vendor ramdisk table contents.
3. Which DTBO overlay is selected for this board/revision, and the final merged live device tree.
4. Whether the bootloader supports `fastboot boot` for a custom image on this model and what image formats it accepts.
5. How the existing `uefi_a/b` partitions are used by the actual boot chain, and whether the bootloader verifies or chains into them.
6. A verified return-to-stock/recovery procedure for any eventual RAM-boot experiment.

## Safe next acquisition steps (read-only)

On Ubuntu, first use the official full fastboot/Recovery package for the *exact* installed build if available, or a trusted local copy of the matching factory images. Keep the archive and record its checksum. Do not substitute an image from another HyperOS build or a custom ROM.

If the exact build's image files are available on the host, inspect copies offline with Android image tools (for example `unpack_bootimg.py` / `mkbootimg` from AOSP, `avbtool info_image`, and `dtc` for DTB/DTBO decoding). Save all extracted outputs in a new working directory and never overwrite the source files. Record image SHA-256 hashes and the full tool versions in the notes.

ADB partition names alone are not enough to safely dump raw partitions. Do not use `dd` against guessed block paths, and do not write to `boot_a/b`, `vendor_boot_a/b`, `dtbo_a/b`, `vbmeta_a/b`, or `uefi_a/b`. If no exact stock package is available, the next task is to identify a supported, read-only acquisition path; do not improvise with root-only paths or a flash operation.

## Implications for UniXNU

The Android kernel image and Android boot metadata cannot simply be reused as an XNU boot image. The future test image needs a compatible Mu-Silicium UEFI stage, a deliberately constructed Darwin payload, and a valid Apple Device Tree handoff. The Linux DTB is useful evidence for hardware discovery, but its properties are not automatically an Apple Device Tree.

The first hardware milestone should remain a reversible UEFI/XNU diagnostic entry with a captured serial/USB/panic log. Do not attempt root filesystem mounting or iOS UI until the entry and platform initialization are repeatable.


## Exact installed-device evidence: runtime Linux DTB and boot images

Collected from the user's K80 running HyperOS, using read-only ADB/root access. These observations describe the current Linux boot, not an XNU handoff.

### Image layout observed offline

Extracted stock slot-A images have these sizes and Android boot header facts:

- `boot_a.img`: 96 MiB; boot header v4; kernel 36,751,872 bytes; ramdisk size 0.
- `vendor_boot_a.img`: 96 MiB; header v4; vendor ramdisk 38,129,733 bytes; DTB container 2,361,704 bytes; bootconfig 205 bytes; one vendor ramdisk table entry (`vendor_ramdisk00`, type 1).
- `init_boot_a.img`: 8 MiB; header v4; ramdisk 3,075,693 bytes.
- `dtbo_a.img`: 24 MiB.
- `vbmeta_a.img` and `vbmeta_system_a.img`: 128 KiB each.

SHA-256 recorded by the user:
- `boot_a.img`: `1089ccf7b583c86c9ecc92746fc076da4d52cba57e564aa204060e7d16dd0ce1`
- `vendor_boot_a.img`: `4abef38fea3ef44c90c8280f04182390c6fbf721a1443f8024937206752f8b38`
- `init_boot_a.img`: `554a1be45f14c8f1b0a443febcf5167b8ddeeadf181babdb4daefff57a332023`
- `dtbo_a.img`: `99d9196ba8061fba63b9507c1b2f0f2d049ab84c91410ffc9d07d1c264c5825e`
- `vbmeta_a.img`: `427c7cc1609b1cacc52996a8fc6fa5fdf5abcc624a7ac023f42edd4f5f94acbe`
- `vbmeta_system_a.img`: `ba36617b54d2dc41c8c400c0c055cedb3e21ba05598d5913b14d3d6350c93679`

The kernel extracted from `boot_a` is an ARM64 Linux boot image, not XNU. The DTB container contains four SoC candidates (Pineapple/PineappleP, revisions 1 and 2); the container alone does not establish which candidate or overlay the bootloader selected.

### Runtime DTB: stronger evidence for active board identity

The user acquired `/sys/firmware/fdt` as `unpacked/runtime.dtb` and decompiled it to `unpacked/runtime.dts`. Its top-level identity is:

- Model: `Qualcomm Technologies, Inc. Zorn based on SM8650`.
- Compatible list: `qcom,pineapple-mtp`, `qcom,pineapple`, `qcom,pineapplep-mtp`, `qcom,pineapplep`, `qcom,mtp`.
- `qcom,msm-id` includes `0x22d`/revision `0x20000` and `0x10000`, plus PineappleP IDs.
- `qcom,board-id = <8 0>`, matching the public Xiaomi Zorn overlay's board ID.

This runtime tree is the best evidence gathered so far for the active Linux board configuration. It is still a Linux Device Tree, not an Apple Device Tree (ADT), and some values can be firmware-mutated before Linux receives it.

### CPU, PSCI, GIC and memory observations

- Eight CPU nodes are present at MPIDR-style IDs `0x0` through `0x700`; every node has `enable-method = "psci"`.
- The runtime tree defines `/soc/psci` as `arm,psci-1.0` with `method = "smc"`. CPU bring-up should therefore be designed around the PSCI SMC interface, after confirming the firmware state and required PSCI calls.
- The primary interrupt controller is `arm,gic-v3` at `0x17100000`; the listed redistributor region starts at `0x17180000` and spans `0x200000`. A GICv3 ITS is listed at `0x17140000`. These are DT-described addresses, not proof that XNU can access the blocks in the same state.
- The top-level memory node has multiple discontiguous `reg` ranges. The reserved-memory node includes explicit `no-map` areas for the hypervisor, SMEM, TrustZone, modem/DSP, firmware and other subsystems, plus reusable shared DMA pools. Do not treat every physical address range as XNU-available RAM; produce a normalized memory map and account for firmware reservations before any allocator is enabled.
- Linux reports about 11.37 GB as `MemTotal`; this is Linux-visible memory after its own exclusions and is not a reliable measurement of physical RAM capacity.

### Debugging implication

The running kernel command line contains `console=ttynull`, so ordinary Linux console output is suppressed/redirected. This does not prove that a hardware UART is unavailable. A later UEFI/XNU test needs an independently verified logging path (serial, USB, or another known-good channel); do not assume that a Linux console setting will configure the UEFI stage.

### Next read-only data to collect

1. Extract the complete `/memory` node and `/reserved-memory` ranges into a normalized address/size table, preserving 64-bit cell pairs and marking `no-map` versus reusable regions.
2. Inspect the complete `/chosen` node and the exact CPU-map hierarchy.
3. Identify UART/serial nodes, their status, register ranges, clocks, pinctrl and interrupt references. This only identifies candidates; it does not prove the UART pins are routed to an accessible connector.
4. Capture `/proc/iomem` and the exact `dtc` version used to decompile the runtime blob.
5. Keep all findings read-only. No partition writes or boot-chain assumptions are justified by this data alone.
