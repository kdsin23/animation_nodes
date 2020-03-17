import bpy
from..bluefox_nodes.c_utils import *
from bpy.props import *
from ... data_structures import *
from ... base_types import AnimationNode
from ... events import executionCodeChanged
from..falloff.custom_falloff import CustomFalloff


modeItems = [
    ("RED", "red", "red1", "", 0),
    ("GREEN", "green", "green1", "", 1),
    ("BLUE", "blue", "blue1", "", 2),
    ("ALPHA", "alpha", "alpha1", "", 3),
    ("GREY", "grey", "grey1", "", 4)
]

class Texturefalloff(bpy.types.Node, AnimationNode):
    bl_idname = "an_Texturefalloff"
    bl_label = "Texture falloff"

    mode = EnumProperty(name = "Use", default = "GREY",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Texture", "Texture", "texture", defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Vector List", "vecin", "locations")
        self.newInput("Float", "strength", "strength", value=1)
        self.newInput("Float", "Fallback", "fallback", hide = True)

        self.newOutput("Falloff", "Falloff", "outFalloff") 
        self.newOutput("Color List", "colors", "colors")

    def draw(self, layout):
        layout.prop(self, "mode")       

    def execute(self, texture, locations, strength, fallback):
        c, r, g, b, a = getTextureColors_moded(texture, locations, strength)
        if self.mode == "GREY":
            return CustomFalloff(FloatList.fromValues(getTexturegreys(texture, locations, strength)), fallback),c
        else:
            if self.mode == "RED":
                return CustomFalloff(FloatList.fromValues(r), fallback),c
            elif self.mode == "GREEN":
                return CustomFalloff(FloatList.fromValues(g), fallback),c
            elif self.mode == "BLUE":
                return CustomFalloff(FloatList.fromValues(b), fallback),c
            elif self.mode == "ALPHA":
                return CustomFalloff(FloatList.fromValues(a), fallback),c

        






