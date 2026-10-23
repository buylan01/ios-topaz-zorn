import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "dump-zorn-memory.py"
SPEC = importlib.util.spec_from_file_location("dump_zorn_memory", MODULE)
FDT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FDT)

def make_dtb():
    names = [b"#address-cells\0", b"#size-cells\0", b"device_type\0", b"reg\0", b"no-map\0"]
    strings = b"".join(names)
    offsets = {n[:-1].decode(): strings.index(n) for n in names}
    def prop(name, value):
        return struct.pack(">III", 3, len(value), offsets[name]) + value + bytes((-len(value)) % 4)
    def begin(name):
        raw = name.encode() + bytes([0])
        return struct.pack(">I", 1) + raw + bytes((-len(raw)) % 4)
    def endnode(): return struct.pack(">I", 2)
    def cells(*v): return struct.pack(">" + "I" * len(v), *v)
    st = bytearray()
    st += begin("") + prop("#address-cells", cells(2)) + prop("#size-cells", cells(2))
    st += begin("memory@80000000") + prop("device_type", b"memory\0")
    st += prop("reg", cells(0, 0x80000000, 0, 0x40000000)) + endnode()
    st += begin("reserved-memory") + prop("#address-cells", cells(2)) + prop("#size-cells", cells(2))
    st += begin("secure@90000000") + prop("reg", cells(0, 0x90000000, 0, 0x01000000))
    st += struct.pack(">III", 3, 0, offsets["no-map"]) + endnode() + endnode() + endnode()
    st += struct.pack(">I", 9)
    off_struct = 56
    off_strings = off_struct + len(st)
    total = off_strings + len(strings)
    header = struct.pack(">10I", 0xD00DFEED, total, off_struct, off_strings, 40, 17, 16, 0, len(strings), len(st))
    return header + bytes(16) + bytes(st) + strings

class FdtMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile()
        self.tmp.write(make_dtb()); self.tmp.flush()
        self.addCleanup(self.tmp.close)

    def test_reads_memory_and_no_map_reserved_region(self):
        root = FDT.parse(self.tmp.name)
        nodes = list(FDT.walk(root))
        memory = next(n for n in nodes if n["name"].startswith("memory@"))
        secure = next(n for n in nodes if n["name"].startswith("secure@"))
        self.assertEqual(FDT.ranges(memory), [{"base":"0x80000000","size":"0x40000000"}])
        self.assertIn("no-map", secure["props"])

    def test_rejects_non_dtb(self):
        with self.assertRaises(ValueError): FDT.parse("/definitely/not/a/dtb")

if __name__ == "__main__": unittest.main()
