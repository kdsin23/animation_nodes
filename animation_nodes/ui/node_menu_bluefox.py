import bpy
from bpy.props import *
from .. utils.operators import makeOperator
from .. sockets.info import getBaseDataTypes
from .. tree_info import getSubprogramNetworks
from .. utils.nodes import getAnimationNodeTrees

mainBaseDataTypes = ("Object", "Integer", "Float", "Vector", "Text")
numericalDataTypes = ("Matrix", "Vector", "Float", "Color", "Euler", "Quaternion")

def drawMenu(self, context):
    if context.space_data.tree_type != "an_AnimationNodeTree": return

    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"

    if drawNodeTreeChooser(layout, context):
        return
    layout.separator()
    layout.menu("AN_MT_bluefox_menu", text = "Bluefox Nodes", icon = "MESH_MONKEY")
    layout.separator()
 
def drawNodeTreeChooser(layout, context):
    if len(getAnimationNodeTrees()) == 0:
        col = layout.column()
        col.scale_y = 1.6
        col.operator("an.create_node_tree", text = "New Node Tree", icon = "PLUS")
        return True
    return False

@makeOperator("an.create_node_tree", "Create Node Tree")
def createNodeTree():
    tree = bpy.data.node_groups.new("AN Tree", "an_AnimationNodeTree")
    bpy.context.space_data.node_tree = tree

class BluefoxMenu(bpy.types.Menu):
    bl_idname = "AN_MT_bluefox_menu"
    bl_label = "Bluefox Menu"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        layout.menu("AN_MT_Effectors_menu", text = "Effectors")
        layout.separator()
        layout.menu("AN_MT_newfalloffs_menu", text = "New Falloffs")
        layout.separator()
        insertNode(layout, "an_Spherical_spiral", "Spherical spiral")
        insertNode(layout, "an_fibonacci", "Fibonacci")
        insertNode(layout, "an_lorenz", "Lorenz Attractor")
        layout.separator()
        layout.menu("AN_MT_AlphaNodes_menu", text = "AlphaNodes", icon = "ERROR")
        layout.separator()
        

class EffectorMenu(bpy.types.Menu):
    bl_idname = "AN_MT_Effectors_menu"
    bl_label = "Effectors Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_Inheritanceffector", "Inheritance effector")

class NewfalloffsMenu(bpy.types.Menu):
    bl_idname = "AN_MT_newfalloffs_menu"
    bl_label = "New falloffs Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_wavefalloff", "Wave falloff")

class AlphaNodesMenu(bpy.types.Menu):
    bl_idname = "AN_MT_AlphaNodes_menu"
    bl_label = "AlphaNodes Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_splinetracer", "Spline Tracer")
        insertNode(layout, "an_MemoryNode", "Memory Node")
        insertNode(layout, "an_Memoryfalloff", "Memory Falloff")
        insertNode(layout, "an_Colormix2", "Color mix-2")
        insertNode(layout, "an_Texturefalloff", "Texture falloff")
        insertNode(layout, "an_Formulafalloff", "Formula falloff")
        insertNode(layout, "an_MixFalloffsNodePlus", "Mix Falloffs-2")


def insertNode(layout, type, text, settings = {}, icon = "NONE"):
    operator = layout.operator("node.add_node", text = text, icon = icon)
    operator.type = type
    operator.use_transform = True
    for name, value in settings.items():
        item = operator.settings.add()
        item.name = name
        item.value = value
    return operator

def register():
    bpy.types.NODE_MT_add.append(drawMenu)

def unregister():
    bpy.types.NODE_MT_add.remove(drawMenu)
