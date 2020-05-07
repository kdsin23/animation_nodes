import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket

dupliModeItems = [
    ("VERTS", "Vertices", "Instance on vertices", "", 0),
    ("FACES", "Faces", "Instance on Faces", "", 1),
    ("COLLECTION", "Collection", "Instance a collection", "", 2),
    ("NONE", "None", "Clear Parent", "", 3)
]

class DupliInstancerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_DupliInstancer"
    bl_label = "Dupli Instancer"
    errorHandlingType = "EXCEPTION"
    bl_width_default = 160

    __annotations__ = {}

    __annotations__["useDisplay"] = BoolProperty(name = "Display Instancer", default = True, update = propertyChanged)
    __annotations__["useRender"] = BoolProperty(name = "Render Instancer", default = True, update = propertyChanged)

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "VERTS",
        items = dupliModeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Object", "Parent", "parent")
        if self.mode == "COLLECTION":
            self.newInput("Collection", "Collection", "collection", defaultDrawType = "PROPERTY_ONLY")
        elif self.mode == "VERTS":
            self.newInput("Object", "Child", "child")
            self.newInput("Boolean", "Align to Normal", "align")
        elif self.mode == "FACES":
            self.newInput("Object", "Child", "child")
            self.newInput("Boolean", "Scale by Face", "scaleByFace")
            self.newInput("Float", "Factor", "factor", value = 1.0)
        elif self.mode == "NONE":
            self.newInput("Object", "Child", "child")

        self.newOutput("Object", "Parent", "object")

    def draw(self, layout):
        layout.prop(self, "mode")
        layout.prop(self, "useDisplay")
        layout.prop(self, "useRender")

    def getExecutionFunctionName(self):
        if self.mode == "VERTS":
            return "execute_Verts"
        elif self.mode == "FACES":
            return "execute_Faces"
        elif self.mode == "COLLECTION":
            return "execute_Collection" 
        elif self.mode == "NONE":
            return "execute_None"                 

    def execute_Verts(self, parent, child, align):
        if parent == None or child == None or parent == child:
            return parent
        else:
            child.parent = parent
            parent.instance_type = "VERTS"
            parent.show_instancer_for_viewport = self.useDisplay
            parent.show_instancer_for_render = self.useRender
            parent.use_instance_vertices_rotation = align

    def execute_Faces(self, parent, child, scaleByFace, factor):
        if parent == None or child == None or parent == child:
            return parent
        else:
            child.parent = parent
            parent.instance_type = "FACES"
            parent.show_instancer_for_viewport = self.useDisplay
            parent.show_instancer_for_render = self.useRender
            parent.use_instance_faces_scale = scaleByFace
            parent.instance_faces_scale = factor          

    def execute_Collection(self, parent, collection):
        if parent == None or collection == None:
            return parent
        else:
            try:
                parent.instance_type = "COLLECTION"
                parent.show_instancer_for_viewport = self.useDisplay
                parent.show_instancer_for_render = self.useRender
                parent.instance_collection = collection
                return parent    
            except TypeError:
                self.raiseErrorMessage("Parent should be an Empty")
                return parent  

    def execute_None(self, parent, child):
        if parent == None or child == None or parent == child:
            return parent
        else:
            child.parent = None                              
