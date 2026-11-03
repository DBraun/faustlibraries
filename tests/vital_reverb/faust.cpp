#include "faust/dsp/dsp.h"
#include "faust/gui/MapUI.h"
#include "faust/gui/meta.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <vector>
// clang-format off
<<includeIntrinsic>>
<<includeclass>>
// clang-format on
struct Handle {
  mydsp dsp;
  MapUI ui;
  Handle(int sr) {
    dsp.init(sr);
    dsp.buildUserInterface(&ui);
  }
};
extern "C" {
void *make(int sr) { return new Handle(sr); }
void destroy(void *p) { delete static_cast<Handle *>(p); }
int inputs(void *p) { return static_cast<Handle *>(p)->dsp.getNumInputs(); }
int outputs(void *p) { return static_cast<Handle *>(p)->dsp.getNumOutputs(); }
int set(void *p, const char *key, float value) {
  auto q = static_cast<Handle *>(p)->ui.getParamZone(key);
  if (!q)
    return 0;
  *q = value;
  return 1;
}
void process(void *p, int n, int block, const float *x, float *y) {
  auto h = static_cast<Handle *>(p);
  int ni = h->dsp.getNumInputs(), no = h->dsp.getNumOutputs();
  std::vector<std::vector<FAUSTFLOAT>> in(ni, std::vector<FAUSTFLOAT>(block)),
      out(no, std::vector<FAUSTFLOAT>(block));
  std::vector<FAUSTFLOAT *> pi(ni), po(no);
  for (int c = 0; c < ni; c++)
    pi[c] = in[c].data();
  for (int c = 0; c < no; c++)
    po[c] = out[c].data();
  for (int pos = 0; pos < n; pos += block) {
    int nb = std::min(block, n - pos);
    for (int c = 0; c < ni; c++)
      for (int k = 0; k < nb; k++)
        in[c][k] = x[c * n + pos + k];
    h->dsp.compute(nb, pi.data(), po.data());
    for (int c = 0; c < no; c++)
      for (int k = 0; k < nb; k++)
        y[c * n + pos + k] = out[c][k];
  }
}
}
