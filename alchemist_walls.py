# bl_info dictionary is needed to qualify as a Blender add-on
bl_info = {
    "name": "Alchemist: Walls",
    "description": "Add walls from Alchemist simulation.",
    "author": "Luca Nenni",
    "version": (1, 0, 1),
    "blender": (2, 62, 0),
    "location": "File > Import",
    "warning": "", # used for warning icon and text in addons panel
    "category": "Import-Export"}


import bpy, random
from os.path import expanduser
from bpy.props import StringProperty

user_home = expanduser("~")
theMessage = ""

# List of walls
walls = []

# Draw a single wall
def drawWall(pt1, pt2, name, material) :
    height = 3
    vertsData=[(0,0,0),(pt2[0]-pt1[0],0,0),(pt2[0]-pt1[0],pt2[1]-pt1[1],0),(0,pt2[1]-pt1[1],0),(0,0,height),(pt2[0]-pt1[0],0,height),(pt2[0]-pt1[0],pt2[1]-pt1[1],height),(0,pt2[1]-pt1[1],height)] # Vertices are relative to the first one
    nbVerts=len(vertsData)
    edgesData=[(0,1),(1,2),(2,3),(3,7),(4,7),(5,6),(6,7),(0,3),(4,5),(1,5),(2,6),(0,4),(1,4)] # All the edges are listed here
    nbEdges=len(edgesData)
    facesData=[(0,1,2,3),(4,7,6,5),(1,5,6,2),(2,6,7,3),(4,0,3,7),(0,1,5,4)] #Same for all the faces (vertices must be in correct order!)
    nbFaces=len(facesData)
    scn = bpy.data.scenes[0]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertsData,edgesData,facesData)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name,mesh)
    obj.data = mesh
    obj.location = (pt1[0],pt1[1],0)
    obj.active_material = material
    scn.objects.link(obj)
    return obj

# Read walls from file and put in a list structure
# Format: x1,y1,x2,y2;x1_1,y1_1,x2_1,y2_1;...
def readWalls(filename):
    global walls
    with open(filename, 'r') as file:
        for row in file.readlines():
            for coords in row.split(';'):
                if (coords != ""):
                    (val1, val2, val3, val4) = coords.split(',')
                    walls.append((((float)(val1), (float)(val2)), ((float)(val3), (float)(val4))))
    return walls

# Draw all the walls contained in a file
def drawWalls(filename):
    global walls
    walls = readWalls(filename)
    # Material definition
    mat = bpy.data.materials.new('WallMaterial')
    mat.diffuse_color = (1,0.965,0.560)
    mat.alpha = 0.1
    mat.transparency_method = 'Z_TRANSPARENCY'
    # Draw the walls
    i = 0
    for wall in walls:
        wallname = 'wall'+str(i)
        wl = drawWall(wall[0],wall[1],wallname,mat)
        i = i+1


# USER INTERFACE

from bpy_extras.io_utils import ImportHelper

class ImportWal(bpy.types.Operator, ImportHelper):
    """Import from Alchemist Wall file (.wal)"""
    bl_idname = "import_scene.walls"
    bl_description = 'Import from Alchemist Wall file (.wal)'
    bl_label = "Import wal"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}
    filename_ext = ".wal"
    filter_glob = StringProperty(default="*.wal", options={'HIDDEN'})
    filepath = StringProperty(subtype='FILE_PATH')
    def draw(self, context):
        layout = self.layout
    def execute(self, context):
        try:
            drawWalls(self.filepath)
        except WalError:
            print("Error when loading Wal file:\n" + theMessage)
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# INITIALIZE AND REGISTER

def menu_func(self, context):
    self.layout.operator(ImportWal.bl_idname, text="Alchemist Walls (.wal)...")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    try:
        bpy.utils.unregister_module(__name__)
    except:
        pass
    try:
        bpy.types.INFO_MT_file_import.remove(menu_func)
    except:
        pass

if __name__ == "__main__":
    unregister()
    register()

# ERROR HANDLER

class WalError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)