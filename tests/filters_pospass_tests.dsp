//----------------------------------------------------------------------------
// filters_pospass_tests.dsp
// Tests for positive-pass (single-side-band) filters.
//----------------------------------------------------------------------------

fi = library("filters.lib");
os = library("oscillators.lib");

src = os.osc(440);

pospass_test = src : fi.pospass(3, 1000);
pospass6e_test = src : fi.pospass6e(1000);

hilbert_test = os.osc(440) : fi.hilbert(6, 100);

hilbert6e_test = os.osc(440) : fi.hilbert6e(100);
