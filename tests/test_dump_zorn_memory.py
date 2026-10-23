import importlib.util
import struct
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "dump-zorn-memory.py"
SPEC = importlib.util.spec_from_file_location("dump_zorn_memory", MODULE)
FDT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FDT)

def prop(name, value, strings):
    off = strings.setdefault(name, len(b"".join(strings.values())))
    return struct.pack(">III", 3, len(value), off) + value + bytes((-len(value)) % 4)

def make_dtb():
    names = [b"#address-cells\0", b"#size-cells\0", b"device_type\0", b"reg\0", b"no-map\0"]
    strings = b"".join(names)
    offsets = {n[:-1].decode(): strings.index(n) for n in names}
    def p(name, value):
        return struct.pack(">III", 3, len(value), offsets[name]) + value + bytes((-len(value)) % 4)
    def begin(name):
        raw = name.encode() + bytes([0])
        return struct.pack(">I", 1) + raw + bytes((-len(raw)) % 4)
    def endnode(): return struct.pack(">I", 2)
    def cells(*v): return struct.pack(">" + "I" * len(v), *v)
    st = bytearray()
    st += begin("") + p("#address-cells", cells(2)) + p("#size-cells", cells(2))
    st += begin("memory@80000000") + p("device_type", b"memory\0")
    st += p("reg", cells(0, 0x80000000, 0, 0x40000000)) + endnode()
    st += begin("reserved-memory") + p("#address-cells", cells(2)) + p("#size-cells", cells(2))
    st += begin("secure@90000000") + p("reg", cells(0, 0x90000000, 0, 0x01000000))
    st += struct.pack(">III", 3, 0, offsets["no-map"]) + endnode() + endnode() + endnode()
    st += struct.pack(">I", 9)
    off_struct = 56
    off_strings = off_struct + len(st)
    total = off_strings + len(strings)
    header = struct.pack(">10I", 0xD00DFEED, total, off_struct, off_strings, 40, 17, 16, 0, len(strings), len(st))
    return header + bytes(16) + bytes(st) + strings

class FdtMemoryTests(unittest.TestCase):
    def test_reads_memory_and_no_map_reserved_region(self):
        root = FDT.parse_dtb(make_dtb())
        nodes = list(FDT.descendants(root))
        memory = next(n for n in nodes if n["name"].startswith("memory@"))
        secure = next(n for n in nodes if n["name"].startswith("secure@"))
        self.assertEqual(FDT.reg_ranges(memory), [{"base":"0x80000000","size":"0x40000000","base_int":0x80000000,"size_int":0x40000000}])
        self.assertIn("no-map", secure["props"])

    def test_rejects_non_dtb(self):
        with self.assertRaises(ValueError): FDT.parse_dtb(b"not a dtb")

if __name__ == "__main__": unittest.main()
