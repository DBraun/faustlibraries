#!/usr/bin/env python3
"""Optional Vital C++ conformance and public-implementation characterization.

Requires NumPy, Faust, a C++ compiler and a local Vital Git checkout. No downloads
or edits to the checkout are made. Native source is extracted from the pinned
commit into the ignored build directory. This is not part of the normal CI run.
"""
import argparse
import ctypes as ct
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVISION = "636ca0ef517a4db087a6a08a6a8a5e704e21f836"
QUANTUM = 128
RATES = (44100, 48000, 88200, 96000, 176400, 192000)
PTR = ct.POINTER(ct.c_float)
FLAGS = ["-std=c++17", "-O2", "-ffp-contract=off"]
PARAMS = ",".join(f'hslider("p{i}",0.5,0,1,0.001)' for i in range(12))
# Identical normalized-to-physical float controls, not derived from rendered audio.
MAPPING = """mapping(a,b,c,d,e,f,g,h,i,j,k,l) =
 min(100,max(0.1,exp(12*j-6))),16+119*a,16+119*b,16+119*c,-24+24*e,
 16+119*d,-24+24*f,g*g,min(16,exp(11*h-8)),1,k,materialize(i*0.3),l
 with { materialize = _ <: attach; };
"""


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, cwd=ROOT, **kwargs)


def padded(x):
    return np.pad(x, ((0, 0), (0, (-x.shape[1]) % QUANTUM)))


def compile_native(args):
    directory = args.build / REVISION
    source = directory / "src"
    if not source.exists():
        directory.mkdir(parents=True, exist_ok=True)
        archive = run(["git", "-C", args.vital_source, "archive", REVISION, "src"],
                      capture_output=True).stdout
        run(["tar", "-xf", "-", "-C", directory], input=archive)
    identity = (HERE / "native.cpp").read_bytes() + (HERE / "JuceHeader.h").read_bytes()
    identity += args.toolchain.encode()
    output = directory / ("native-" + hashlib.sha256(identity).hexdigest()[:12] + args.suffix)
    if not output.exists() or output.stat().st_mtime < (HERE / "native.cpp").stat().st_mtime:
        includes = [HERE, source] + sorted(p for p in source.rglob("*") if p.is_dir())
        units = [source / "synthesis/effects/reverb.cpp"]
        units += [source / "synthesis/framework" / (p + ".cpp")
                  for p in ("processor", "processor_router", "feedback", "utils", "value")]
        run([args.cxx, *FLAGS, *args.shared, *("-I" + str(p) for p in includes),
             *units, HERE / "native.cpp", "-o", output])
    return output


def compile_faust(args, name, definitions, expression):
    code = 'import("stdfaust.lib");\n' + definitions + "\nprocess = " + expression + ";\n"
    dependencies = b"".join(p.read_bytes() for p in sorted(ROOT.glob("*.lib")))
    identity = (code + args.toolchain).encode() + dependencies
    identity += (HERE / "reference.lib").read_bytes() + (HERE / "faust.cpp").read_bytes()
    folder = args.build / (name + "-" + hashlib.sha256(identity).hexdigest()[:12])
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / ("processor" + args.suffix)
    if not output.exists():
        dsp, cpp = folder / "processor.dsp", folder / "processor.cpp"
        dsp.write_text(code)
        run([args.faust, "-single", "-I", ROOT, "-a", HERE / "faust.cpp", dsp, "-o", cpp])
        run([args.cxx, *FLAGS, *args.shared, "-I" + str(args.faust_include), cpp, "-o", output])
    return output


class Faust:
    def __init__(self, path):
        self.d = ct.CDLL(str(path))
        self.d.make.argtypes = [ct.c_int]
        self.d.make.restype = ct.c_void_p
        self.d.destroy.argtypes = [ct.c_void_p]
        self.d.set.argtypes = [ct.c_void_p, ct.c_char_p, ct.c_float]
        self.d.process.argtypes = [ct.c_void_p, ct.c_int, ct.c_int, PTR, PTR]
        self.d.outputs.argtypes = [ct.c_void_p]
        self.h = None

    def reset(self, rate, controls):
        self.close()
        self.h = self.d.make(rate)
        self.set(controls)

    def set(self, controls):
        for i, value in enumerate(controls):
            if not self.d.set(self.h, f"p{i}".encode(), value):
                raise RuntimeError(f"missing control p{i}")

    def render(self, x):
        x = np.ascontiguousarray(x, dtype="f4")
        y = np.zeros((self.d.outputs(self.h), x.shape[1]), dtype="f4")
        self.d.process(self.h, x.shape[1], QUANTUM, x.ctypes.data_as(PTR), y.ctypes.data_as(PTR))
        return y

    def close(self):
        if self.h:
            self.d.destroy(self.h)
            self.h = None


class Native:
    def __init__(self, path):
        self.d = ct.CDLL(str(path))
        self.d.create.argtypes = [ct.c_int]
        self.d.create.restype = ct.c_void_p
        self.d.destroy.argtypes = [ct.c_void_p]
        self.d.controls.argtypes = [ct.c_void_p, PTR]
        self.d.process.argtypes = [ct.c_void_p, PTR, PTR, PTR, PTR, ct.c_int, ct.c_int]
        self.h = None

    def reset(self, rate, controls):
        self.close()
        self.h = self.d.create(rate)
        self.set(controls)

    def set(self, controls):
        controls = np.ascontiguousarray(controls, dtype="f4")
        self.d.controls(self.h, controls.ctypes.data_as(PTR))

    def render(self, x):
        x = np.ascontiguousarray(x, dtype="f4")
        assert x.shape[1] % QUANTUM == 0
        y = np.zeros_like(x)
        self.d.process(self.h, x[0].ctypes.data_as(PTR), x[1].ctypes.data_as(PTR),
                       y[0].ctypes.data_as(PTR), y[1].ctypes.data_as(PTR), x.shape[1], QUANTUM)
        return y

    def close(self):
        if self.h:
            self.d.destroy(self.h)
            self.h = None


def parameters():
    groups = []
    rng = np.random.default_rng(20261103)
    p = rng.uniform(0.08, 0.92, (8, 12))
    p[:, 1] = rng.uniform(0.7, 0.94, 8)
    p[:, 0] = rng.uniform(0.02, 0.28, 8)
    p[:, 10] = rng.uniform(0.05, 0.9, 8)
    p[:, 11] = rng.uniform(0.25, 1, 8)
    p[0, [6, 10]], p[1, [6, 10]], p[2, 8] = [0.95, 0.08], [0.9, 0.12], 0
    groups.append(p)
    rng = np.random.default_rng(20261104)
    p = rng.uniform(0.02, 0.98, (8, 12))
    p[:, 0], p[:, 1] = rng.uniform(0.01, 0.3, 8), rng.uniform(0.7, 0.98, 8)
    p[:, 9], p[:, 11] = rng.uniform(0.35, 0.85, 8), rng.uniform(0.3, 1, 8)
    p[0, 10], p[1, 10], p[2, 8] = 0.375, 0.875, 0
    groups.append(p)
    rng = np.random.default_rng(2026110344176)
    p = rng.uniform(0.01, 0.99, (20, 12))
    p[:, 0], p[:, 1] = rng.uniform(0.01, 0.3, 20), rng.uniform(0.7, 0.98, 20)
    p[:, 11] = rng.uniform(0.25, 1, 20)
    p[:7, 10] = [0, 0.125, 0.375, 0.5, 0.625, 0.875, 1]
    p[7, 6], p[8, 6], p[9, 8], p[10, 8], p[11, 9], p[12, 9] = 0, 1, 0, 1, 0, 1
    p[13, 4:6], p[14, 4:6] = [0, 1], [1, 0]
    groups.append(p)
    return np.concatenate(groups)


def characterize(y, reference, rate):
    power = lambda a: np.sum(a.astype("f8") ** 2)
    ratio = lambda a, b: float(10 * np.log10(max(a, 1e-40) / max(b, 1e-40)))
    n = y.shape[1]
    spectrum = np.abs(np.fft.rfft(y.astype("f8"), axis=1)) ** 2
    native_spectrum = np.abs(np.fft.rfft(reference.astype("f8"), axis=1)) ** 2
    frequency = np.fft.rfftfreq(n, 1 / rate)
    bands = []
    for center in (125, 250, 500, 1000, 2000, 4000):
        mask = (frequency >= center / np.sqrt(2)) & (frequency < center * np.sqrt(2))
        bands.append(ratio(spectrum[:, mask].sum(), native_spectrum[:, mask].sum()))
    return dict(level_db=ratio(power(y), power(reference)),
                waveform_error_db=ratio(power(y.astype("f8") - reference), power(reference)),
                band_level_db=bands, peak=float(np.max(np.abs(y))), finite=bool(np.isfinite(y).all()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vital_source", type=Path)
    parser.add_argument("--faust", default=os.environ.get("FAUST", "faust"))
    parser.add_argument("--cxx", default=os.environ.get("CXX", "c++"))
    parser.add_argument("--faust-include", type=Path)
    parser.add_argument("--build", type=Path, default=ROOT / "tests/build/vital")
    parser.add_argument("--quick", action="store_true", help="one rate, four cold/settled controls")
    parser.add_argument("--require-exact", action="store_true", help="fail on any reference float-bit difference")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    executable = shutil.which(args.faust)
    if executable is None:
        parser.error("Faust not found; set FAUST or use --faust")
    args.faust = str(Path(executable).resolve())
    args.toolchain = run([args.faust, "-v"], capture_output=True, text=True).stdout
    args.toolchain += run([args.cxx, "--version"], capture_output=True, text=True).stdout
    args.toolchain += platform.machine() + " ".join(FLAGS)
    if args.faust_include is None:
        candidates = [Path(args.faust).parents[2] / "architecture",
                      Path(run([args.faust, "-includedir"], capture_output=True, text=True).stdout.strip()),
                      Path("/usr/local/include"), Path("/opt/homebrew/include"), Path("/usr/include")]
        args.faust_include = next((p for p in candidates if (p / "faust/dsp/dsp.h").exists()), None)
    if args.faust_include is None:
        parser.error("cannot locate Faust C++ headers; use --faust-include")
    args.build = args.build.resolve()
    args.build.mkdir(parents=True, exist_ok=True)
    args.suffix = ".dylib" if platform.system() == "Darwin" else ".so"
    args.shared = ["-dynamiclib"] if platform.system() == "Darwin" else ["-shared", "-fPIC"]
    native = Native(compile_native(args))
    reference = Faust(compile_faust(args, "reference", 'vr=library("'+str(HERE/'reference.lib')+'");', 'vr.vital_rev('+PARAMS+')'))
    public = Faust(compile_faust(args, "public", "", 're.vital_rev('+PARAMS+')'))
    mapper = Faust(compile_faust(args, "mapping", MAPPING, 'mapping('+PARAMS+')'))
    rows = []

    def physical(p):
        mapper.reset(44100, p)
        return mapper.render(np.empty((0, 1), dtype="f4"))[:, 0]

    def reset(rate, p):
        native.reset(rate, physical(p))
        reference.reset(rate, p)
        public.reset(rate, p)

    def render(x):
        return native.render(x), reference.render(x), public.render(x)

    def record(rate, name, outputs):
        n, r, y = outputs
        equal = bool(np.array_equal(n.view("u4"), r.view("u4")))
        row = dict(rate=rate, case=name, reference_bit_equal=equal, frames=n.shape[1],
                   public=characterize(y, n, rate))
        rows.append(row)
        if not row["public"]["finite"]:
            raise AssertionError("non-finite public output: " + name)
        if args.require_exact and not equal:
            raise AssertionError("reference mismatch: " + name + " at " + str(rate))

    rates = (48000,) if args.quick else RATES
    for rate in rates:
        for case, p in enumerate(parameters()[:4] if args.quick else parameters()):
            for settled in (False, True):
                reset(rate, p)
                if settled:
                    render(np.zeros((2, QUANTUM * int(np.ceil(4 * rate / QUANTUM))), dtype="f4"))
                t = np.arange(int(0.7 * rate)) / rate
                x = (0.03*np.sin(2*np.pi*(200+23*case)*t)[None, :] +
                     0.02*np.random.default_rng(7000+case).normal(size=(2, len(t)))).astype("f4")
                x[:, int(0.25*rate):] = 0
                record(rate, f"controls-{case}-{'settled' if settled else 'cold'}", render(padded(x)))
        if args.quick:
            continue
        p = [0.15,0.85,0.45,0.75,0.8,0.7,0.3,0.6,0.03,0.5,0.45,0.8]
        changes = [("tone",{0:0.25,1:0.7,2:0.7,3:0.6,4:0.2,5:0.3}),
                   ("size",{9:0.8,10:0.75}), ("predelay",{8:0.35}),
                   ("chorus",{6:0.85,7:0.75}), ("mix",{11:0.25})]
        for name, values in changes:
            reset(rate, p)
            t = np.arange(QUANTUM * int(rate / QUANTUM)) / rate
            x = (0.04*np.random.default_rng(443).normal(size=(2,len(t))) +
                 0.03*np.sin(2*np.pi*330*t)[None,:]).astype("f4")
            x[:,int(0.8*rate):] = 0
            split = QUANTUM * int(0.4*rate/QUANTUM)
            first = render(x[:,:split])
            new = p.copy()
            for index, value in values.items():
                new[index] = value
            native.set(physical(new)); reference.set(new); public.set(new)
            last = render(x[:,split:])
            record(rate,name,tuple(np.concatenate([a,b],axis=1) for a,b in zip(first,last)))
        if rate in (44100,96000,192000):
            for name,p in [("flat-tail",[0.15,0.9,0.4,0.8,1,1,0,0.5,0,0.65,0.55,1]),
                           ("modulated-tail",[0.1,0.92,0.3,0.85,0.9,0.8,0.7,0.8,0.07,0.8,0.7,1])]:
                reset(rate,p)
                render(np.zeros((2,QUANTUM*int(np.ceil(2*rate/QUANTUM))),dtype="f4"))
                t = np.arange(8*rate)/rate
                x = np.stack([0.03*np.sin(2*np.pi*330*t),0.03*np.sin(2*np.pi*477*t)]).astype("f4")
                x[:,rate:] = 0
                record(rate,name,render(padded(x)))
    # A sub-128-sample mix change must affect the very next public sample.
    p = [0.5,0.5,0.5,0.7,0.4,0.6,0,0.2,0,0.5,0.5,0]
    public.reset(48000,p)
    for mix, count in [(0,17),(1,23),(0.35,19),(0.8,31)]:
        p[-1] = mix
        public.set(p)
        x = np.full((2,count),0.1,dtype="f4")
        y = public.render(x)
        np.testing.assert_allclose(y,x*np.sin(np.pi*(1-mix)/2),rtol=2e-6,atol=2e-8)
    for processor in (native,reference,public,mapper):
        processor.close()
    summary = dict(native_revision=REVISION,platform=platform.machine(),quantum=QUANTUM,
                   reference_sha256=hashlib.sha256((HERE/"reference.lib").read_bytes()).hexdigest(),
                   public_sha256=hashlib.sha256((ROOT/"reverbs.lib").read_bytes()).hexdigest(),
                   toolchain=args.toolchain,cases=len(rows),reference_bit_equal=sum(r["reference_bit_equal"] for r in rows),
                   public_direct_mix_response=True,rows=rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary,indent=2)+"\n")
    print(f"Reference: {summary['reference_bit_equal']}/{len(rows)} cases bit-identical. "
          "Public output finite; sub-block mix response passed.")


if __name__ == "__main__":
    main()
