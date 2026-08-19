//----------------------------------------------------------------------------
// pinktrombone_tests.dsp
// Deterministic tests for the Pink Trombone port
// (pinktrombone.lib).
//----------------------------------------------------------------------------

pt = library("pinktrombone.lib");
os = library("oscillators.lib");
ba = library("basics.lib");
si = library("signals.lib");

// LF glottal pulse at a few Rd values, driven by a phasor
lfWaveform_test = par(i, 3, pt.lfWaveform(0.5 + i, os.lf_sawpos(100)));

// Rest tract shape and the derived reflection coefficients
tractDiameters_test = pt.tractDiameters(12.9, 2.43, 30, 3, 0);
tractDiameters_constricted_test = pt.tractDiameters(20, 3.0, 30.4, 0.55, 1);
tractReflections_test = pt.tractDiameters(12.9, 2.43, 30, 3, 0), 0.01 : pt.tractReflections;

// One waveguide tick from a known state
tractTick_test = state, exc : pt.tractTick
with {
    state = par(k, pt.NSTATE, (k == 16) + (k == 64) + 0.7*(k == 91) + 0.2*(k == 125));
    exc = 1, par(k, pt.n, (k == 5)*0.25), par(i, pt.n - 1, 0.01*(i+1)), 0.1, 0.2, 0.3;
};

// Tract driven by a 140 Hz pulse train (deterministic, no turbulence)
pulses = (os.lf_imptrain(140)), 0.3;
tract_vowel_test = pulses : pt.tract(12.9, 2.43, 30, 3, 0, 0);
tract_nasal_test = pulses : pt.tract(27, 2.2, 30, 3, 0, 1);
tract_closure_test = pulses : pt.tract(12.9, 2.43, 40, 0, 1, 0);
tract2_test = pulses : pt.tract2(12.9, 2.43, 36.3, 0.5, 1, 20.6, 0.8, 1, 0);

// Full instrument (uses internal noise generators: deterministic no.noises streams)
pinkTrombone_test = pt.pinkTrombone(140, 0.6, 1, 0, 12.9, 2.43, 30, 3, 0, 0);
pinkTrombone2_test = pt.pinkTrombone2(140, 0.6, 1, 0, 12.9, 2.43, 40, 0.2, 1, 20, 1.0, 1, 1);
ui_test = pt.ui;
