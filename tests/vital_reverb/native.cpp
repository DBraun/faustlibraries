#include "memory.h"
#include "reverb.h"
#include <cstdlib>
#include <new>
using namespace vital;
struct Handle {
  Reverb *reverb;
  std::unique_ptr<Output> controls[Reverb::kNumInputs];
  Handle(int sr) {
    void *storage =
        ::operator new(sizeof(Reverb), std::align_val_t(alignof(Reverb)));
    std::memset(storage, 0, sizeof(Reverb));
    reverb = new (storage) Reverb();
    reverb->setSampleRate(sr);
    for (int i = 0; i < Reverb::kNumInputs; i++) {
      controls[i] = std::make_unique<Output>(1);
      reverb->plug(controls[i].get(), i);
    }
  }
  ~Handle() {
    reverb->~Reverb();
    ::operator delete(reverb, std::align_val_t(alignof(Reverb)));
  }
};
extern "C" {
void *create(int sr) { return new Handle(sr); }
void destroy(void *p) { delete static_cast<Handle *>(p); }
void controls(void *p, const float *v) {
  auto *h = static_cast<Handle *>(p);
  for (int i = 1; i < Reverb::kNumInputs; i++)
    h->controls[i]->buffer[0] = v[i - 1];
}
void process(void *p, const float *l, const float *r, float *ol, float *orr,
             int n, int block) {
  auto *h = static_cast<Handle *>(p);
  poly_float audio[kMaxBufferSize];
  for (int start = 0; start < n; start += block) {
    int count = std::min(block, n - start);
    for (int i = 0; i < count; i++)
      audio[i] = poly_float(l[start + i], r[start + i], 0.f, 0.f);
    h->reverb->processWithInput(audio, count);
    for (int i = 0; i < count; i++) {
      auto y = h->reverb->output()->buffer[i];
      ol[start + i] = y[0];
      orr[start + i] = y[1];
    }
  }
}
}
