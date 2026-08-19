//----------------------------------------------------------------------------
// pinktrombone_tests.dsp
// Deterministic tests for the Pink Trombone port
// (pinktrombone.lib).
//----------------------------------------------------------------------------

pt = library("pinktrombone.lib");
os = library("oscillators.lib");
ba = library("basics.lib");
si = library("signals.lib");
no = library("noises.lib");

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

glottis_test = pt.glottis(140, 0.6, (ba.time < 24000), 0);

tractDiameters2_test = pt.tractDiameters2(20, 3.0, 36.3, 0.5, 1, 20.6, 0.8, 1);

tract_test = (os.lf_imptrain(140), 0.3) : pt.tract(12.9, 2.43, 30, 3, 0, 0);

tractN_test = pt.tractN(no.noise, 12.9, 2.43, 30.4, 0.55, 1, 0, os.lf_imptrain(140), 0.3);

tractN2_test = pt.tractN2(no.noise, 12.9, 2.43, 36.3, 0.5, 1, 20.6, 0.8, 1, 0, os.lf_imptrain(140), 0.3);

pt_moveTowards_test = pt.moveTowards(10, 5, (ba.time < 12000));

pt_latch_test = pt.latch(os.lf_imptrain(10), os.lf_sawpos(3));

pt_simplexNoise_test = pt.simplexNoise(4.07);

pt_whiteNoise_test = pt.whiteNoise;

pt_bandpassUnity_test = no.noise : pt.bandpassUnity(500, 0.5);

pt_aspirationNoise_test = pt.aspirationNoise;

pt_fricativeNoise_test = pt.fricativeNoise;

pt_restDiameter_test = par(i, 44, pt.restDiameter(12.9, 2.43, i));

pt_constrictedDiameter_test = par(i, 44, pt.constrictedDiameter(30.4, 0.55, 1, i, 1.5));

pt_slowReturn_test = par(i, 44, pt.slowReturn(i));

pt_noseDiameterInit_test = par(i, 28, pt.noseDiameterInit(i));

pt_noseArea_test = par(i, 28, pt.noseArea(i));

pt_noseReflection_test = par(i, 27, pt.noseReflection(i+1));

pt_cif_test = pt.cif(1, 2, 3), pt.cif(0, 2, 3);

pt_n_test = pt.n;

pt_bladeStart_test = pt.bladeStart;

pt_tipStart_test = pt.tipStart;

pt_lipStart_test = pt.lipStart;

pt_noseLength_test = pt.noseLength;

pt_noseStart_test = pt.noseStart;

pt_glottalReflection_test = pt.glottalReflection;

pt_lipReflection_test = pt.lipReflection;

pt_movementSpeed_test = pt.movementSpeed;

pt_tractDamping_test = pt.tractDamping;

pt_noseDamping_test = pt.noseDamping;

pt_noseReflectionA0_test = pt.noseReflectionA0;

pt_blockTime_test = pt.blockTime;

pt_tongueIndexMin_test = pt.tongueIndexMin;

pt_tongueIndexMax_test = pt.tongueIndexMax;

pt_tongueDiameterMin_test = pt.tongueDiameterMin;

pt_tongueDiameterMax_test = pt.tongueDiameterMax;

pt_noiseSeed_test = pt.noiseSeed;

pt_NSTATE_test = pt.NSTATE;

pt_NREFL_test = pt.NREFL;

// Release a full closure to exercise the transient path.
tract_release_test = (os.lf_imptrain(140), 0.3) : pt.tract(12.9, 2.43, 30, 0, ba.time < 12000, 0);

// Exercise audio-rate shape changes and delayed voice onset across period wraps.
lfWaveform_modulated_test = pt.lfWaveform(0.5 + 1.1*(1 + os.osc(2)), os.lf_sawpos(200));
glottis_modulated_test = pt.glottis(150 + 50*os.osc(0.8), 0.5 + 0.45*os.osc(4), (ba.time % 48000) > 12000, 1);
