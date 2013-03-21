# bl_info dictionary is needed to qualify as a Blender add-on
bl_info = {
    "name": "Alchemist: Nodes",
    "description": "Add nodes from Alchemist simulation.",
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

# Dictionary of steps: every step is a couple (frame_number, step_dictionary) in the dict
steplist = {}

# Draw a single node (represented by a cone)
def createMeshFromPrimitive(name, origin):
    bpy.ops.mesh.primitive_cone_add(
        vertices=32, 
        radius=0.3, 
        depth=5, 
        cap_end=True, 
        view_align=False, 
        enter_editmode=False, 
        location=origin, 
        rotation=(0, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.show_name = True
    me = ob.data
    me.name = name+'Mesh'
    mat = bpy.data.materials.new(name+'Mat')
    mat.diffuse_color = (random.random(),random.random(),random.random())
    ob.active_material = mat
    return ob

# Tell if a string may represent a float
def is_float(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

# Read nodes from file and put in a dict structure
# The single step is represented by a dictionary itself, which couples are (node_name, (x, y))
def readNodesFromFile(filename):
    steps = {}
    step = 1
    with open(filename, 'r') as csvfile:
        for row in csvfile.readlines():
            nodes = {}
            time, sep, rest = row.partition(';') # Read the time
            realstep, sep, nodelist = rest.partition(';') # Read the step number
            bpy.ops.anim.change_frame(frame=int(step))
            for node in nodelist.split(';'):
                nodename,sep,rest = node.partition(',') # Read the node name
                x,sep,rest = rest.partition(',') # Read the x value
                y,sep,type = rest.partition(',') # Read the y value, everything else is 'type'
                if (type == "person"): # Only if the node qualifies as a person
                    nodes[nodename] = (float(x),float(y)) # Insert the node in the dictionary
            steps[step] = nodes
            step = step+1
    return steps

# Hide an object which has not to be seen in the frame
def make_hidden(object):
    object.hide = True
    object.hide_render = True # Not seen in the rendering, too

# Make an object visible again
def make_visible(object):
    object.hide = False
    object.hide_render = False

# Move the objects (called by the frame handler)
def set_objects_location(node_dict,frame):
    # Hide alle the existing objects
    for key2 in bpy.context.scene.objects.keys():
        if (key2.startswith("node_")):
            ob = bpy.context.scene.objects.get(key2)
            make_hidden(ob)
    for key, (x,y) in node_dict[frame].items():
        ob = bpy.context.scene.objects.get("node_"+key)
        # Create the new objects for this frame, if any
        if (ob == None):
            ob = createMeshFromPrimitive("node_"+key, (float(x),float(y),0))
        # Make visible and move only the objects which are to be seen in this frame
        else:
            ob.location = (x, y, 2.5)
        make_visible(ob)

# Every frame change, this function is called.
def my_handler(scene):
    global steplist
    frame = scene.frame_current
    set_objects_location(steplist,frame)

# Draw all the nodes in a file
def importNodes(node_file):
    bpy.context.scene.frame_current=1
    global steplist
    steplist = readNodesFromFile(node_file)
    for key, (x,y) in steplist[1].items() :
        createMeshFromPrimitive("node_"+key, (float(x),float(y),0))
    bpy.app.handlers.frame_change_pre.append(my_handler)
    bpy.context.scene.frame_current=1


# USER INTERFACE

from bpy_extras.io_utils import ImportHelper

class ImportNod(bpy.types.Operator, ImportHelper):
    """Import from Alchemist Node file (.nod)"""
    bl_idname = "import_scene.nodes"
    bl_description = 'Import from Alchemist Nodes file (.nod)'
    bl_label = "Import nod"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'UNDO'}
    filename_ext = ".nod"
    filter_glob = StringProperty(default="*.nod", options={'HIDDEN'})
    filepath = StringProperty(subtype='FILE_PATH')
    def draw(self, context):
        layout = self.layout
    def execute(self, context):
        try:
            importNodes(self.filepath)
        except NodError:
            print("Error when loading Nod file:\n" + theMessage)
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# INITIALIZE AND REGISTER

def menu_func(self, context):
    self.layout.operator(ImportNod.bl_idname, text="Alchemist Nodes (.nod)...")

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

class NodError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)