# Vital reverb reference

`reference.lib` freezes the C++-parity version of the port. It preserves the
source's 128-sample controls, float approximations, interpolation clock and
intermediate rounding. Its `materialize = _ <: attach` helper requests a shared
intermediate without duplicating the expression during box evaluation.

The public `re.vital_rev` keeps the network and filter design while accepting
parameter signals directly. It uses ordinary mathematical functions, a continuous
chorus oscillator, and predelay motion with a 4.2 Hz Butterworth response in time.
Its demo supplies raw sliders. Diffuser durations scale in seconds instead of
following the source's power-of-two buffer sizes. This deliberately changes the
tuning above 44.1 kHz; the reference retains the original scaling. The NumPy/SciPy
feedback matrix derivation is retained in the public function's documentation.

## Optional native comparison

Requires NumPy, Faust 2.87 or newer, a C++ compiler, and a local Git checkout of
https://github.com/mtytel/vital containing commit
`636ca0ef517a4db087a6a08a6a8a5e704e21f836`. The runner extracts that commit into
`tests/build/vital` without changing the checkout or downloading anything.

From the repository root:

```sh
FAUST=/path/to/faust python3 tests/vital_reverb/compare.py /path/to/vital \
    --require-exact --output tests/build/vital/comparison.json
```

`--quick` runs eight cases at 48 kHz. The full run covers 432 cold/settled cases,
30 control-change cases and six eight-second tails at 44.1/48/88.2/96/176.4/192 kHz.
The JSON records both reference equality and the public implementation's waveform,
level, octave-band levels and peaks. It also checks that a public mix change acts
on the next sample, even within a 128-sample interval.

Bit equality is verified on arm64 with `-O2 -ffp-contract=off`. Other architectures
or math libraries can differ in the upstream SIMD reductions; omit
`--require-exact` to inspect those differences. Production characterization is
reported separately: bit equality is a property of the frozen reference, not a
requirement on the public implementation.

The native source/framework are unmodified. `JuceHeader.h` supplies non-DSP
macros and standard includes only. `native.cpp` zero-fills correctly aligned
storage before construction to define the upstream uninitialized delay-velocity
field. Both implementations receive identical physical float controls. Native
renders use full 128-sample blocks, including zero padding at the end, since a
short final native block changes its control ramps. No output alignment, gain
fit, EQ or resampling is performed.
