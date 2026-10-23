#!/usr/bin/env python3
"""Read-only FDT inspector: list /memory and /reserved-memory reg ranges."""
import json, struct, sys
from pathlib import Path
MAGIC=0xD00DFEED

def parse(path):
    b=Path(path).read_bytes()
    if len(b)<40: raise ValueError("short FDT header")
    h=struct.unpack_from(">10I",b)
    magic,total,os,ot,_,ver,last,_,ss,sz=h
    if magic!=MAGIC or total>len(b) or ver<17 or last>ver: raise ValueError("invalid/unsupported DTB")
    strings=b[ot:ot+ss]; end=os+sz; p=os; stack=[]; root=None
    while p+4<=end:
        tok=struct.unpack_from(">I",b,p)[0]; p+=4
        if tok==1:
            e=b.index(bytes([0]),p,end); name=b[p:e].decode("ascii","replace"); p=(e+4)&~3
            n={"name":name,"props":{},"children":[],"parent":stack[-1] if stack else None}
            if stack: stack[-1]["children"].append(n)
            elif root is None: root=n
            else: raise ValueError("multiple roots")
            stack.append(n)
        elif tok==2:
            if not stack: raise ValueError("unbalanced node")
            stack.pop()
        elif tok==3:
            length,no=struct.unpack_from(">II",b,p); p+=8
            e=strings.index(bytes([0]),no); key=strings[no:e].decode("ascii")
            stack[-1]["props"][key]=b[p:p+length]; p=(p+length+3)&~3
        elif tok==4: pass
        elif tok==9: break
        else: raise ValueError("unknown FDT token")
    if root is None or stack: raise ValueError("incomplete FDT")
    return root

def cells(raw):
    if len(raw)%4: raise ValueError("bad cell length")
    v=0
    for i in range(0,len(raw),4): v=(v<<32)|struct.unpack_from(">I",raw,i)[0]
    return v

def propnum(n,k,d):
    x=n["props"].get(k)
    return d if x is None else struct.unpack(">I",x)[0]

def ranges(n):
    par=n["parent"]; ac=propnum(par,"#address-cells",2); sc=propnum(par,"#size-cells",1)
    raw=n["props"].get("reg",b""); stride=(ac+sc)*4
    if not raw or not stride or len(raw)%stride: raise ValueError("bad reg at "+n["name"])
    out=[]
    for p in range(0,len(raw),stride):
        base=cells(raw[p:p+ac*4]); size=cells(raw[p+ac*4:p+stride]) if sc else 0
        out.append({"base":hex(base),"size":hex(size)})
    return out

def walk(n):
    for c in n["children"]:
        yield c; yield from walk(c)

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: dump-zorn-memory.py runtime.dtb")
    root=parse(sys.argv[1]); ram=[]; reserved=[]
    for n in walk(root):
        typ=n["props"].get("device_type",b"").split(bytes([0]),1)[0]
        path=n["name"]
        if typ==b"memory" or path=="memory" or path.startswith("memory@"):
            ram += [{"node":path,**r} for r in ranges(n)]
        if n["parent"] and n["parent"]["name"]=="reserved-memory" and "reg" in n["props"]:
            reserved += [{"node":path,"no_map":"no-map" in n["props"],**r} for r in ranges(n)]
    print(json.dumps({"warning":"Linux FDT evidence only; not an Apple DT or usable-RAM map","memory":ram,"reserved_memory":reserved},indent=2))
    if not ram: raise SystemExit("no memory ranges found")
if __name__=="__main__":
    try: main()
    except (OSError,ValueError,struct.error) as e: raise SystemExit("FDT error: "+str(e))
