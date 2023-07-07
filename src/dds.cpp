#include "dds.hpp"

#include <DirectXTex.h>
#include <stringapiset.h>

#include <filesystem>
#include <format>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

using namespace DirectX;

namespace Pso2Tools {

namespace {
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

void OpenDds(const std::filesystem::path& path, ScratchImage& image) {
  ScratchImage input;
  auto hr = LoadFromDDSFile(path.generic_wstring().c_str(), DDS_FLAGS_NONE, nullptr, input);
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

void SavePng(const std::filesystem::path& path, const ScratchImage& image) {
  const auto itemCount = image.GetMetadata().arraySize;

  // TODO: support importing animated textures by saving to tex00.png, tex01.png, ...
  // and reporting the paths of all saved files.
  auto hr = SaveToWICFile(*image.GetImage(0, 0, 0), WIC_FLAGS_FORCE_SRGB, GetWICCodec(WIC_CODEC_PNG),
                          path.generic_wstring().c_str());
  Check(hr, "Failed to save image");
}

}  // namespace Pso2Tools