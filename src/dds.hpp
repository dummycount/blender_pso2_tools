#pragma once

#include <DirectXTex.h>

#include <span>
#include <string>

namespace Pso2Tools {

void Initialize();

void OpenDds(const std::string& path, DirectX::ScratchImage& image);

void SavePng(const std::string& path, const DirectX::ScratchImage& image);

}