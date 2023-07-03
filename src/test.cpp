#include <DirectXTex.h>

#include <iostream>

#include "dds.hpp"

using namespace DirectX;
using namespace Pso2Tools;

int main(int argc, char* argv[]) {
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << " input.dds output.png\n";
    return 0;
  }

  Initialize();

  ScratchImage image;
  OpenDds(argv[1], image);
  SavePng(argv[2], image);

  return 0;
}