import os
import numpy
from stl import mesh
import trimesh

# Create a dummy STL file (a simple cube)
def create_dummy_stl(filename):
    data = numpy.zeros(12, dtype=mesh.Mesh.dtype)
    cube = mesh.Mesh(data, remove_empty_areas=False)
    # 12 triangles for a cube (simplified for test)
    cube.save(filename)
    return filename

test_file = "test_cube.stl"
create_dummy_stl(test_file)

print(f"Created {test_file}")

# Test numpy-stl
try:
    print("Testing numpy-stl...")
    your_mesh = mesh.Mesh.from_file(test_file)
    volume, _, _ = your_mesh.get_mass_properties()
    print(f"numpy-stl Volume: {volume}")
except Exception as e:
    print(f"numpy-stl Failed: {e}")

# Test trimesh
try:
    print("Testing trimesh...")
    mesh_obj = trimesh.load(test_file)
    print(f"Trimesh loaded: {mesh_obj}")
    if hasattr(mesh_obj, 'volume'):
        print(f"Trimesh Volume: {mesh_obj.volume}")
    else:
        print("Trimesh volume not available directly")
except Exception as e:
    print(f"trimesh Failed: {e}")

# Cleanup
if os.path.exists(test_file):
    os.remove(test_file)
