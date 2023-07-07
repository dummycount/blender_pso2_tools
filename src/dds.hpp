#pragma once

#include <DirectXTex.h>

#include <filesystem>
#include <span>

namespace Pso2Tools {

void Initialize();

void OpenDds(const std::filesystem::path& path, DirectX::ScratchImage& image);

void SavePng(const std::filesystem::path& path, const DirectX::ScratchImage& image);

}