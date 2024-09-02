# Blender Add-on for PSO2

## Installation

1. Download `pso2_tools-****.zip` from the [latest release](https://github.com/dummycount/blender_pso2_tools/releases/latest).
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click the down arrow in the upper-right corner and select **Install from Disk...**.
4. Select the .zip file you downloaded.
5. Make sure **PSO2 Tools** is checked in the add-ons list.
6. Expand **PSO2 Tools** and make sure **Path to pso2_bin/data** is correct. If not, set it to point to your game's install directory.

## Usage

### Import

**Files > Import > PSO2 Model Search** opens a window to find an import items by name. Currently only character model items can be searched.

**Files > Import > PSO2 ICE Archive** imports models and textures from an ICE archive. If the file name matches a known item, settings such as color mapping are automatically read from that item.

**Files > Import > PSO2 AQP (.aqp)** imports from the `.aqp` model format. If an `aqn` skeleton file of the same name exists, it is also imported, as are any `.dds` textures in the same folder. If the file name matches a known item, settings such as color mapping are automatically read from that item.

For models that get their textures from other items, such as innerwear textures on basewear items, or eye/eyebrow/eyelash textures on faces, import the item with the textures first, then import the model, and it will automatically find the correct textures. If you import in the wrong order, you can go to Blender's **Shading** tab, select an object, then assign any missing textures in the shader editor area.

If an NGS model uses skin textures, they will automatically be imported. You can change which textures to use in the add-on preferences.

### Export

**Files > Export > PSO2 AQP (.aqp)** exports the model back to an `.aqp` file.

By default, this will only write a matching `.aqn` file if it does not already exist. Check **Overwrite .aqn** to overwrite any existing file.

### Preferences

Go to **Edit > Preferences > Add-ons > PSO2 Tools** to edit the extension's settings.

| Setting                 | Description                                                      |
| ----------------------- | ---------------------------------------------------------------- |
| Path to pso2_bin/data   | Path to `pso2_bin/data` inside the game's install directory      |
| Hide armature on import | Automatically hide the armature object when importing a model    |
| Debug logging           | If enabled, debugging messages are written to the system console |
| Default Muscularity     | Default value for **Muscularity** scene property                 |
| Default T1 Skin Texture | Skin texture to import for T1 models                             |
| Default T2 Skin Texture | Skin texture to import for T2 models                             |
| Import Colors           | Default values for the color scene properties                    |

### Scene Properties

In the **Properties** area, go to the **Scene** tab. Two panels will appear here once a model has been imported:

#### PSO2 Appearance

| Property       | Description                                             |
| -------------- | ------------------------------------------------------- |
| Hide Innerwear | Hides the innerwear layer on skin materials             |
| Muscularity    | Adjusts the mix between skin textures on skin materials |
| Colors         | The color channels used by PSO2 materials               |

#### PSO2 Ornaments

Clicking the buttons here will show or hide meshes that are associated with toggleable ornaments.

## Development

To build and develop the extension, first install the following requirements:

- [Blender 4.2](https://www.blender.org/download/releases/) or newer.
- [Python 3.11](https://www.python.org/downloads/) or newer.
- [Visual Studio](https://visualstudio.microsoft.com/vs/community/) with the C# and C++ workflows installed.
- [Autodesk FBX SDK](https://www.autodesk.com/content/dam/autodesk/www/adn/fbx/2020-1/fbx20201_fbxsdk_vs2017_win.exe) version 2020.1

First, clone the repo with submodules:

```pwsh
git clone --recurse https://github.com/dummycount/blender_pso2_tools.git
cd blender_pso2_tools
```

Then run the following commands to set up the development environment:

```pwsh
# Install Python modules needed for development
pip install requirements-dev.txt
# Set up Git hooks to format files
pre-commit install

# Download Python wheels for dependencies.
scripts/wheels.py
# Build binaries needed by the add-on.
scripts/build_bin.py
# Generate Python typings for the above binaries.
# (This will probably fail, but it will generate some useful typings first.)
scripts/build_typings.py
```

[scripts/wheels.py](scripts/wheels.py) defines the Python dependencies used by the add-on. This script needs to be run any time the dependencies are updated, and [pso2_tools/blender_manifest.toml](pso2_tools/blender_manifest.toml) needs to be updated to list all the wheel files.

[scripts/build_bin.py](scripts/build_bin.py) needs to be run any time the PSO2-Aqua-Library submodule is updated. The `PACKAGES` array at the top also needs to be kept in sync with any nuget packages used by Aqua Library.

[scripts/build_typings.py](scripts/build_typings.py) does not need to be run for the add-on to function, but it generates typings that can be helpful when editing in an IDE.

To build and install the add-on, run:

```pwsh
scripts/install.py --editable
```

This will install the add-on in Blender, then symlink it back to this repo. The extension will automatically reload itself when it detects a change to its own files. (This usually crashes Blender after a while, so save your work often.)

Run the script without `--editable` to install the add-on without a symlink.

To build the add-on without installing it, e.g. for a release, run:

```pwsh
scripts/build_package.py
```
