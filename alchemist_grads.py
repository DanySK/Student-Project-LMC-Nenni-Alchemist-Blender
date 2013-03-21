# bl_info dictionary is needed to qualify as a Blender add-on
bl_info = {
    "name": "Alchemist: Gradients",
    "description": "Add gradients from Alchemist simulation.",
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
RED_FACTOR = 4 # Reduction factor (too high gradients tend to go out of the rendering window)

# Dictionary of gradients: every step is a couple (frame_number, step_dictionary) in the dict
gradlist = {}

# Draw a single sphere
def createSphereMeshFromPrimitive(name, origin):
    bpy.ops.mesh.primitive_uv_sphere_add(
        location = origin,
        size = 0.1
        )
    ob = bpy.context.object
    ob.name = name
    ob.show_name = True
    me = ob.data
    me.name = name+'SphereMesh'
    mat = bpy.data.materials.new(name+'Mat')
    mat.diffuse_color = (random.random(),random.random(),random.random())
    ob.active_material = mat
    return ob

# Read gradients from file and put in a dict structure
# The single step is represented by a dictionary itself, which couples are (node_name, (x, y, z)), where 'z' is the gradient value
def readGradsFromFile(filename):
    grads = {}
    step = 1
    with open(filename, 'r') as csvfile:
        for row in csvfile.readlines():
            gradnodes = {}
            time, sep, rest = row.partition(';') # Reads the time
            realstep, sep, nodelist = rest.partition(';') # Reads the step number
            bpy.ops.anim.change_frame(frame=int(step))
            for node in nodelist.split(';'):
                if(node != '\n'):
                    name,x,y,z = node.split(',')
                    gradnodes[name] = (float(x),float(y),float(z)/RED_FACTOR) # Inserts the node in the dictionary
            grads[step] = gradnodes
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

# Move the objects (called by the frame handler)
def set_objects_location(grad_dict,frame):
    # Hide alle the existing objects
    for key2 in bpy.context.scene.objects.keys():
        if (key2.startswith("grad_")):
            ob = bpy.context.scene.objects.get(key2)
            make_hidden(ob)
    for key,(x,y,z) in grad_dict[frame].items():
        ob = bpy.context.scene.objects.get("grad_"+key)
        # Create the new objects for this frame, if any
        if (ob == None):
            ob = createSphereMeshFromPrimitive("grad_"+key, (float(x),float(y),float(z)/RED_FACTOR))
        # Make visible and move only the objects which are to be seen in this frame
        else:
            ob.location = (x, y, z/RED_FACTOR)
        make_visible(ob)

# Every frame change, this function is called.
def my_handler(scene):
    global gradlist
    frame = scene.frame_current
    set_objects_location(gradlist,frame)

# Draw all the gradients in a file
def importGrads(grad_file):
    bpy.context.scene.frame_current=1
    global gradlist
    gradlist = readGradsFromFile(grad_file)
    for key,(x,y,z) in gradlist[1].items() :
        createSphereMeshFromPrimitive("grad_"+key, (float(x),float(y),float(z)/RED_FACTOR))
    bpy.app.handlers.frame_change_pre.append(my_handler)
    bpy.context.scene.frame_current=1


# USER INTERFACE

from bpy_extras.io_utils import ImportHelper

class ImportGra(bpy.types.Operator, ImportHelper):
    """Import from Alchemist Grad file (.gra)"""
    bl_idname = "import_scene.grads"
    bl_description = 'Import from Alchemist Gradients file (.gra)'
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
    self.layout.operator(ImportGra.bl_idname, text="Alchemist Gradients (.gra)...")

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
