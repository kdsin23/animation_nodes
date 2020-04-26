import bpy
import numpy as np
from bpy.props import *
from ... base_types import AnimationNode, VectorizedSocket
from ... events import executionCodeChanged, propertyChanged
from ... data_structures import Color, ColorList, VirtualColorList, VirtualDoubleList, DoubleList

colormodeItems = [
    ("MIX", "Mix", "Mix", "", 0),
    ("ADD", "Add", "Add", "", 1),
    ("LIGHTEN", "Lighten", "Lighten", "", 2),
    ("SCREEN", "Screen", "Screen", "", 3),
    ("OVERLAY", "Overlay", "Overlay", "", 4),
    ("DARKEN", "Darken", "Darken", "", 5),
    ("MULTIPLY", "Multiply", "Multiply", "", 6),
    ("SUBTRACT", "Subtract", "subtract", "", 7)
]

class Colormix2(bpy.types.Node, AnimationNode):
    bl_idname = "an_Colormix2"
    bl_label = "Color Mix 2"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}
    
    __annotations__["mode"] = EnumProperty(name = "Type", default = "MIX",
        items = colormodeItems, update = AnimationNode.refresh)

    clamp = BoolProperty(name = "Clamp", default = True, update = propertyChanged)    

    usecolorAList: VectorizedSocket.newProperty()
    usecolorBList: VectorizedSocket.newProperty()
    usefactorList: VectorizedSocket.newProperty()    

    def create(self):
        self.newInput(VectorizedSocket("Color", "usecolorAList",
            ("Color A", "colorA"), ("Colors A", "colorsA")))
        self.newInput(VectorizedSocket("Color", "usecolorBList",
            ("Color B", "colorB"), ("Colors B", "colorsB")))
        self.newInput(VectorizedSocket("Float", "usefactorList",
            ("Factor", "factor"), ("Factors", "factors")))        
        self.newInput("Float", "Alpha", "alpha", value = 1.0, hide = True)     

        self.newOutput(VectorizedSocket("Color", ["usecolorAList", "usecolorBList", "usefactorList"],
            ("Color", "color"), ("Colors", "colors")))   

    def draw(self, layout):
        layout.prop(self, "clamp")
        layout.prop(self, "mode")
                   
    def execute(self, colorsA, colorsB, factors, alpha):
        if not self.usecolorAList: colorsA = ColorList.fromValues([colorsA])
        if not self.usecolorBList: colorsB = ColorList.fromValues([colorsB])
        if not self.usefactorList: factors = DoubleList.fromValue(factors)

        if len(colorsA) == 0 or len(colorsB) == 0 or len(factors) == 0:
            self.raiseErrorMessage("Reconnect Output Socket")
            return ColorList()

        if len(colorsA) == len(colorsB) == len(factors):
            colA = np.array(colorsA)
            colB = np.array(colorsB)
            factor = np.array(factors)
        else:
            maxLength = max(max(len(colorsA), len(colorsB)), len(factors))
            colA = np.array(VirtualColorList.create(colorsA, colorsA[-1]).materialize(maxLength))
            colB = np.array(VirtualColorList.create(colorsB, colorsB[-1]).materialize(maxLength))
            factor = np.array(VirtualDoubleList.create(factors, factors[-1]).materialize(maxLength))

        mode = self.mode

        if mode == "ADD":
            result = colA + colB
        elif mode == "SUBTRACT":
            result = colA - colB
        elif mode == "MULTIPLY":
            result = colA * colB
        elif mode == "SCREEN":
            result = 1 - (1 - colA) * (1 - colB)   
        elif mode == "LIGHTEN":
            result = np.maximum(colA, colB)
        elif mode == "DARKEN":
            result = np.minimum(colA, colB)    
        elif mode == "OVERLAY":                 #Overlay function needs work
            if np.any([colA < 0.5]):
                result = 2 * colA * colB
            else:
                result = 1 - 2 * (1 - colA) * (1 - colB)
        elif mode == "MIX":
            result = colB

        out = self.color_mix(colA, result, factor)
        out[:,-1] = alpha

        if self.clamp:
            out = np.clip(out, 0.00, 1.00)
   
        if self.usecolorAList == 0 and self.usecolorBList == 0 and self.usefactorList == 0:
            return ColorList.fromValues(out)[0]
        else:
            return ColorList.fromValues(out)           
         
    def color_mix(self, colorsA, colorsB, factor):
        shaped_factor = np.repeat(factor, 4).reshape(-1, 4)
        if self.clamp:
            shaped_factor = np.clip(shaped_factor, 0.00, 1.00) 
        return (1 - shaped_factor) * colorsA + shaped_factor * colorsB
    
   