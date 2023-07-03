#include "dds.hpp"

#include <DirectXTex.h>
#include <stringapiset.h>

#include <format>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

using namespace DirectX;

namespace Pso2Tools {

namespace {
std::wstring ToWstring(const std::string& str) {
  if (str.empty()) {
    return {};
  }

  const auto size = MultiByteToWideChar(CP_UTF8, 0, str.data(), std::ssize(str), nullptr, 0);
  std::wstring wstr(size, 0);
  MultiByteToWideChar(CP_UTF8, 0, str.data(), std::ssize(str), wstr.data(), size);

  return wstr;
}

void Check(HRESULT hr, const std::string& context) {
  if (FAILED(hr)) {
    throw std::runtime_error{std::format("{} ({:#08x})", context.c_str(), static_cast<unsigned int>(hr))};
  }
}

}  // namespace

void Initialize() {
  auto hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
  Check(hr, "Failed to initialize COM");
}

void OpenDds(const std::string& path, ScratchImage& image) {
  const auto wpath = ToWstring(path);

  ScratchImage input;
  auto hr = LoadFromDDSFile(wpath.c_str(), DDS_FLAGS_NONE, nullptr, input);
  Check(hr, "Failed to open file");

  ScratchImage decompressed;
  if (DirectX::IsCompressed(input.GetMetadata().format)) {
    hr = Decompress(input.GetImages(), input.GetImageCount(), input.GetMetadata(), DXGI_FORMAT_UNKNOWN, decompressed);
    Check(hr, "Failed to decompress file");

    image = std::move(decompressed);
  } else {
    image = std::move(input);
  }
}

void SavePng(const std::string& path, const ScratchImage& image) {
  const auto wpath = ToWstring(path);

  auto hr = SaveToWICFile(image.GetImages(), image.GetImageCount(), WIC_FLAGS_FORCE_SRGB, GetWICCodec(WIC_CODEC_PNG),
                          wpath.c_str());
  Check(hr, "Failed to save image");
}

}  // namespace Pso2Tools