# Pink Trombone port — reference, validation and notes

Support material for `pinktrombone.lib` (root, prefix `pt`), the Faust port of Neil
Thapen's **Pink Trombone** v1.1 (2017, MIT) <https://dood.al/pinktrombone/>.

## Files

- `port-notes.md` — how each part of the JS maps to Faust, every deliberate
  deviation, validation results, Faust lessons. **Read this before changing the DSP.**
- `simplex-noise-fit.md` — the 1-D simplex drift noise (`no.simplex1_lf` in
  `noises.lib`, exact) and the history of the earlier statistical substitute.
- `ptref.py` — line-by-line Python port of the JS `Tract`/`Glottis` used as the
  reference. `fh.py` — DawDreamer render helper. `validate.py` — compares the Faust
  code with the reference: `python3.11 tests/pinktrombone/validate.py`
  (needs dawdreamer, numpy, scipy).
- `../pinktrombone_tests.dsp` — deterministic `_test` specs for `make reference/check`;
  `dm.pink_trombone_demo` in `demos.lib` (`../demos_tests.dsp`).
- Not committed (gitignored): the original page — fetch with
  `curl -sL https://dood.al/pinktrombone/ -o tests/pinktrombone/pinktrombone-1.1-original.html`
  (the whole synth is inline JS: `Glottis`, `Tract`, `TractUI.setRestDiameter`,
  `TractUI.handleTouches`, `AudioSystem.doScriptProcessor`) — and `listening/`
  demo renders (default "ah", vowel glide with wobble, tenseness sweep, fricative,
  plosive, nasal, voice gate, 20 s wobble).

## Status (2026-08-18)

- Tract (44-section Kelly–Lochbaum + 28-section nose, 2 ticks/sample, transients,
  turbulence, velum) matches the JS reference to ~1e-6 relative in steady state
  (float32); differences only in the first ~0.25 s (the JS interpolates its
  reflection coefficients from zero in block 0) and during diameter movement
  (block-rate vs sample-rate slew).
- Glottis (LF pulse via Rd, per-period parameter latching, aspiration, intensity
  ramp, frequency smoothing, vibrato/wobble, tenseness drift) matches the reference
  waveform to <1.5e-3 abs and RMS / high-band statistics to <1 %; the drift noise
  is real simplex noise, exact up to the seed (`pt.noiseSeed`).
- CPU: ~12 % of one core at 44.1 kHz (DawDreamer, float32). Compiles and renders
  its block diagram in the Faust Web IDE (box-graph kept small; see port-notes.md).
- Not yet listened to by a human.

## Controls (`pt.ui` / `dm.pink_trombone_demo`)

| group | control | original |
|---|---|---|
| voicebox | pitch (0..20 semitones above F2 87.31 Hz), tenseness, always voice, pitch wobble | keyboard x, keyboard y, the two buttons |
| tract | tongue index (12..29), tongue diameter (2.05..3.5), nasal | tongue control disc, touching above the nose |
| constriction | index (2..44), diameter (0..3, 3 = none, ≤0.3 = closure), active | any other touch on the tract |
