#define PY_SSIZE_T_CLEAN

#include <DirectXTex.h>
#include <Python.h>

#include <span>
#include <stdexcept>

#include "dds.hpp"

using namespace DirectX;
using namespace Pso2Tools;

namespace {

PyObject* ConvertDdsToPng(PyObject* self, PyObject* args) {
  const char* ddsPath;
  const char* pngPath;

  if (!PyArg_ParseTuple(args, "ss", &ddsPath, &pngPath)) {
    return nullptr;
  }

  try {
    ScratchImage image;
    OpenDds(ddsPath, image);
    SavePng(pngPath, image);
  } catch (const std::runtime_error& ex) {
    PyErr_SetString(PyExc_ValueError, ex.what());
    return nullptr;
  }

  Py_RETURN_NONE;
}

PyMethodDef Methods[] = {
    {"dds_to_png", ConvertDdsToPng, METH_VARARGS, nullptr}, {},  // Sentinel
};

PyModuleDef Module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "import_dds",
    .m_size = -1,
    .m_methods = Methods,
};

}  // namespace

PyMODINIT_FUNC PyInit_import_dds() { return PyModule_Create(&Module); }