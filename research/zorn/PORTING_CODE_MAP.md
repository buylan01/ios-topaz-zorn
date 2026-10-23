# Code migration map: topaz to zorn

This is an implementation checklist. The topaz source remains the reference baseline; no topaz hardware constant is valid for zorn without independent evidence.

## Files that must be split into common code and board data

- `shim/shim.c`: board-specific restart registers, GIC addresses, interrupt IDs, CPU count, MPIDR construction and reset path are interwoven with architectural setup. First isolate reset and interrupt-controller operations behind a board interface. For zorn, start with CPU0 architectural register capture only; do not enable secondary cores based on Linux CPU indices.
- `shim/mmu.c` / `shim/mmu.h`: topaz maps a fixed low physical range and a fixed framebuffer. Replace this with a range table generated from a normalized zorn memory map. Keep the allocator disabled until RAM banks and all reserved/no-map ranges are represented without overlap.
- `shim/ufs.c` / `shim/ufs.h`: the host controller base and power-on assumptions are topaz-specific. Do not compile this probe into a zorn boot path until the zorn controller resources and link state are sourced. First tests must remain read-only.
- `shim/console.c` / `shim/console.h`: the console directly writes to topaz's splash framebuffer. Split logging from the display backend. Zorn's candidate UART is not verified; do not write to it merely because it appears in a DT.
- `shim/loader.c`: the current code assumes topaz ABL's boot-image-v4 ramdisk behavior and the SWEETXNU appended-payload layout. Confirm the Redmi K80 bootloader handoff and payload ABI before reusing this path.
- `tools/mkadt.py`: RAM banks, GIC, storage, framebuffer, timer frequency, panel dimensions and product identity are topaz-specific. Refactor the serializer to accept a board manifest, and make zorn generation fail when required values are unknown.
- `.github/workflows/xnu.yml`: CI pins macOS/Xcode-era tooling and a topaz CPU target. Keep this as the upstream baseline; add a separate zorn validation/build job instead of silently changing the existing target.
- `tools/mkiosroot.sh`: this path erases Android userdata. Do not run it on the K80 during bring-up.

## First code milestones

1. Add a small host-side FDT inspection tool to emit all RAM and reserved-memory ranges, including address/size cell widths and no-map flags. Test it against the saved runtime DTB before using its output.
2. Add a zorn-only diagnostic entry that reports architectural CPU state and boot arguments without changing board registers. A verified logging transport is a prerequisite.
3. Capture CPU0 MPIDR, current exception level, supported translation granules, architectural timer frequency, GIC system-register interface state and PSCI version.
4. Normalize the complete memory map and validate that image, page tables and handoff structures occupy ordinary RAM and avoid all reserved ranges.
5. Validate GICv3 redistributor affinity and timer interrupt delivery before entering XNU.
6. Implement a zorn ADT generator from explicit measured inputs, with unit tests and rejection of missing required fields.
7. Only after repeatable CPU0 entry and panic capture, investigate UFS reads. Keep storage writes disabled.

## Values explicitly not to copy

Do not copy topaz's SM6225 CPU topology, MPIDR scheme, GIC and UFS bases, timer frequency, framebuffer location, panel geometry, restart registers or memory layout. Do not copy the OnePlus Ace 5 board values either. A shared SM8650 SoC does not make board wiring, firmware, memory carveouts, UFS PHY setup or display resources identical.

## Current gates

The research manifest intentionally leaves UFS base, timer frequency, boot MPIDR, translation-granule support, normalized memory regions and panel data unset. This is correct: unknown hardware data must block the relevant feature instead of being filled with guesses.
