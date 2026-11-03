#pragma once
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>
#define JUCE_LEAK_DETECTOR(T)
#define JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(T)                        \
  T(const T &) = delete;                                                       \
  T &operator=(const T &) = delete;
