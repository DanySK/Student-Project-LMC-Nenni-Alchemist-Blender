# bl_info dictionary is needed to qualify as a Blender add-on
bl_info = {
    "name": "Alchemist: Gradients - Surface",
    "description": "Add gradients from Alchemist simulation into a mesh surface.",
    "author": "Luca Nenni",
    "version": (1, 0, 0),
    "blender": (2, 62, 0),
    "location": "File > Import",
    "warning": "", # used for warning icon and text in addons panel
    "category": "Import-Export"}


import bpy, random
from os.path import expanduser
from bpy.props import StringProperty
# Requires Point Cloud Skinner by Hans.P.G.
# http://blenderartists.org/forum/showthread.php?241950-A-Script-to-Skin-a-Point-Cloud-(for-Blender-2-6x-or-Later)
# Change the following line if you rename the .py add-on
point_cloud = __import__("98 t25_PointCloudSkinner1_Umbrella")
from datetime import datetime # Useful for debugging

user_home = expanduser("~")
theMessage = ""
RED_FACTOR = 4 # Reduction factor (too high gradients tend to go out of the rendering window)

# Dictionary required by Point Cloud Skinner
point_cloud.gb["TargetObject"] = 'Grad'
point_cloud.gb["MaxAroundDist"] = 5
point_cloud.gb["MaxDistForAxis"] = 10
point_cloud.gb["MaxAroundCount"] = 10
point_cloud.gb["MinVertsAngle"] = 25
point_cloud.gb["MaxVertsAngle"] = 135
point_cloud.gb["GridSize"] = [3 * 5] * 3
point_cloud.gb["PrecisionLevel"] = 2
point_cloud.gb["TargetVertsMode"] = False
point_cloud.gb["IgnoreErrors"] = True

# Dictionary of gradients: every step is a couple (frame_number, step_dictionary) in the dict
gradlist = {}

# Read gradients from file and put in a dict structure
# The single step is represented by a dictionary itself, which couples are (node_name, (x, y, z)), where 'z' is the gradient value
def readGradsFromFile(filename):
    grads = {}
    step = 1
    with open(filename, 'r') as csvfile:
        for row in csvfile.readlines():
            gradnodes = []
            time, sep, rest = row.partition(';') # Reads the time
            realstep, sep, nodelist = rest.partition(';') # Reads the step number
            bpy.ops.anim.change_frame(frame=int(step))
            for node in nodelist.split(';'):
                if(node != '\n'):
                    name,x,y,z = node.split(',')
                    gradnodes.append((float(x),float(y),float(z)/RED_FACTOR)) # Inserts the node in the list
            grads[step]=gradnodes
            step = step+1
    return grads

# Hide an object which has not to be seen in the frame
def make_hidden(object):
    object.hide = True
    object.hide_render = True # Not seen in the rendering, too

# Make an object visible again
def make_visible(object):
    object.hide = False
    object.hide_render = False

# Every frame change, this function is called.
# The surfaces are drawn by the next function, so the frame handler only decides what to show for every frame.
def my_handler(scene):
    scene = bpy.context.scene
    frame = scene.frame_current
    for ob in bpy.data.objects.values():
        if ((ob.name == 'Grad_'+str(frame)) or (ob.type == 'CAMERA') or (ob.type == 'LAMP')):
            make_visible(ob)
        else:
            make_hidden(ob)

# Draw all the gradients surfaces
def importGrads(grad_file):
    firstTime = datetime.time(datetime.now())
    bpy.context.scene.frame_current=1
    scene = bpy.context.scene
    global gradlist
    gradlist = readGradsFromFile(grad_file)
    for key in gradlist:
        print('Grad_'+str(key)+' done, actual time: '+str(datetime.time(datetime.now())))
        mesh = bpy.data.meshes.new('Grad_'+str(key))
        mesh.from_pydata(gradlist[key],[],[])
        obj = bpy.data.objects.new('Grad_'+str(key),mesh)
        scene.objects.link(obj)
        point_cloud.gb["TargetObject"] = 'Grad_'+str(key)
        point_cloud.SkinVerts()
    bpy.app.handlers.frame_change_pre.append(my_handler)
    bpy.context.scene.frame_current=1
    print('First timestamp was: '+str(firstTime))

# USER INTERFACE

from bpy_extras.io_utils import ImportHelper

class ImportGraS(bpy.types.Operator, ImportHelper):
    """Import from Alchemist Grad file (.gra)"""
    bl_idname = "import_scene.gradsurf"
    bl_description = 'Import from Alchemist Gradients file (.gra) into surface'
    bl_label = "Import gra"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}
    filename_ext = ".gra"
    filter_glob = StringProperty(default="*.gra", options={'HIDDEN'})
    filepath = StringProperty(subtype='FILE_PATH')
    def draw(self, context):
        layout = self.layout
    def execute(self, context):
        try:
            importGrads(self.filepath)
        except GraError:
            print("Error when loading Gra file:\n" + theMessage)
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# INITIALIZE AND REGISTER

def menu_func(self, context):
    self.layout.operator(ImportGraS.bl_idname, text="Alchemist Gradients (.gra) into surface...")

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

class GraError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
