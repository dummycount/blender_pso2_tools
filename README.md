# Blender Add-on for PSO2

## Installation

1. Install the [.NET Framework 4.7.2 Runtime](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net472).
1. Download from the [releases page](https://github.com/dummycount/blender_pso2_tools/releases).
1. In Blender, open **Edit > Preferences > Add-ons > Install** and select the downloaded ZIP file.
1. Enable the checkbox next to **Import-Export: PSO2 format**.
1. Click the arrow next to **Import-Export: PSO2 format** to expand the add-on preferences.
1. Set the path to the PSO2 data folder if it is not set automatically.

## Usage

### Import

**File > Import > PSO2 Model (.aqp)** imports from the `.aqp` model format. If an `.aqn` skeleton file of the same name exists, it is also read. Any `.dds` textures in the same folder will also be imported.

**File > Import > PSO2 ICE Archive** works the same as importing an `.aqp` file, except it imports directly from an ICE archive so you don't need to extract it first. It also supports importing textures from an archive that doesn't contain a model.

On the right side of the file selector, you can change the custom outfit colors, skin color, and which body type's skin texture will be imported. To skip importing skin textures, set the body type to "None". Skin textures are read from your PSO2 data folder.

### Export

**File > Export > PSO2 Model (.aqp)** exports to the `.aqp` model format. An `.aqn` skeleton file of the same name is also exported (this overwrites an existing file if the **Update Skeleton** setting is enabled).

### Materials

When importing a model, PSO2 Tools creates materials which approximate those used in game. They are not accurate but should be sufficient for seeing how a model will look with textures.

The materials currently support the following features:

- Diffuse texture
- Alpha for `blendalpha` and `hollow` materials
- Normal map
- Custom basewear/outerwear and skin colors
- Innerwear/body paint on skin materials

They do not support:

- Basewear/outerwear regions that use innerwear colors
- Cast materials
- Various special textures (`_o`, etc.)
- Most special shaders (fur, etc.)

To automatically assign textures such as innerwear, eyes, eyebrows, and eyelashes, import those ICE archives before importing the model that uses them.

To adjust outfit and skin colors after import, select an object with the material to edit, open Blender's shader editor, and click the icon at the top-right of the "Colors" node.

## Development

Requirements:

- [Python 3.10](https://www.python.org/downloads/) or newer.
- [Visual Studio](https://visualstudio.microsoft.com/vs/community/) with the C# and C++ workflows installed.
- [Autodesk FBX SDK](https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-3)
- [PowerShell](https://github.com/PowerShell/PowerShell/releases)

To install and build dependencies, run the following commands in a terminal:
```sh
git submodule update --init --recursive
./build
```

If building the dependencies fails, try running the build script a couple more times.

To symlink the development version of the add-on into Blender's add-ons directory, run:
```sh
./link
```

You can reload the add-on without restarting Blender by pressing `F3` and running the "Reload Scripts" command.

## Credits

FBX conversion is based on [Aqua Model Tool](https://github.com/Shadowth117/PSO2-Aqua-Library).