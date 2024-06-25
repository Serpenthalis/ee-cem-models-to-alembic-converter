import os
import bpy
import logging
from pathlib import Path

# Set logging level
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# Config
blender_path = str(Path("C:/path/to/blender.exe"))
cemtool_path = str(Path("C:/path/to/CEMtool-Blender_WiP25_edit.zip"))
cemtool_name = "io_scene_cem"
input_directory_path = str(Path("C:/path/to/cem-models"))
output_directory_path = str(Path("C:/path/to/put/alembic-models"))

try_apply_material = True
texture_directory_path = str(Path("C:/path/to/textures"))
texture_file_extension = "tga"
material_name_suffix = "_Mat_Inst"


def main():
    # Tell bpy where Blender is
    bpy.app.binary_path = blender_path

    # Empty file instead of default scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Install CEMtool
    bpy.ops.preferences.addon_install(filepath=cemtool_path)

    # Enable CEMtool
    bpy.ops.preferences.addon_enable(module=cemtool_name)
    bpy.ops.wm.save_userpref()

    # Get list of all input files
    input_files = [file for file in os.listdir(input_directory_path) if
                   os.path.isfile(Path(f"{input_directory_path}/{file}"))]

    # Conversion
    for file in input_files:
        clear_scene()
        convert(file)


def convert(file):
    # Append input path to file name
    file_path = str(Path(f"{input_directory_path}/{file}"))

    # Import CEM files
    try:
        bpy.ops.import_scene.cem(filepath=file_path)
    except (TypeError, Exception) as e:
        logging.warning(f"{file}: {e}")
        return

    # Try applying the texture
    if try_apply_material:
        texture_matches = [filename for filename in os.listdir(texture_directory_path) if
                           file.split(".")[:-1][0] in filename and filename.endswith(f".{texture_file_extension}")]

        meshes = get_meshes()

        for idx, mesh in enumerate(meshes):
            mesh.data.materials.pop()
            if "player" in mesh.name:
                material = bpy.data.materials.new(name=f"player_color")  # Blender automatically adds _001 if duplicate
                logging.warning(f"Unable to find corresponding texture file for {file}")
            elif len(texture_matches) != 1:
                material = bpy.data.materials.new(name=f"{idx}_{mesh.data.name}")
                logging.warning(f"Unable to find corresponding texture file for {file}")
            else:
                texture_path = str(Path(f"{texture_directory_path}/{texture_matches[0]}"))
                material = create_material_with_texture(texture_path)
                logging.info(f"Successfully assigned texture {texture_matches[0]}")
            assign_material_to_mesh(mesh.name, material)
            mesh.data.materials.append(material)

    # Export ABCs file
    output_file_path = str(Path(f"{output_directory_path}/{file.split('.')[:-1][0]}.abc"))

    bpy.ops.wm.alembic_export('EXEC_DEFAULT', filepath=output_file_path, face_sets=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def get_meshes():
    meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            meshes.append(obj)
    return meshes


def create_material_with_texture(image_path):
    os_path_separator = str(Path("/"))

    # Create a new material
    material = bpy.data.materials.new(name=f"{image_path.split(os_path_separator)[-1].split('.')[:-1][0]}{material_name_suffix}")

    return material


def assign_material_to_mesh(mesh_names, material):
    # Find the mesh object
    for mesh_name in mesh_names:
        obj = bpy.data.objects.get(mesh_name)
        if obj:
            # Make sure the object has mesh data
            if obj.type == 'MESH':
                if obj.data.materials:
                    # If the object already has materials, replace the first one
                    obj.data.materials[0] = material
                else:
                    # If the object has no materials, append the new material
                    obj.data.materials.append(material)
                print(f"Material {material.name} assigned to mesh '{mesh_name}'.")
            else:
                print(f"Object '{mesh_name}' is not a mesh.")


if __name__ == '__main__':
    main()
