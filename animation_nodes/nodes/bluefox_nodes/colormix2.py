import bpy
import numpy as np
from bpy.props import *
from ... events import executionCodeChanged, propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Color, ColorList, VirtualColorList, VirtualDoubleList

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

    usecolor1List: VectorizedSocket.newProperty()
    usecolor2List: VectorizedSocket.newProperty()
    usefactorList: VectorizedSocket.newProperty()    

    def create(self):
        self.newInput(VectorizedSocket("Color", "usecolor1List",
            ("Color A", "colorA"), ("Colors A", "colorsA")))
        self.newInput(VectorizedSocket("Color", "usecolor2List",
            ("Color B", "colorB"), ("Colors B", "colorsB")))
        self.newInput(VectorizedSocket("Float", "usefactorList",
            ("Factor", "factor"), ("Factors", "factors")))        
        self.newInput("Float", "Alpha", "alpha", value = 1.0, hide = True)     

        self.newOutput(VectorizedSocket("Color", ["usecolor1List", "usecolor2List", "usefactorList"],
            ("Color", "color"), ("Colors", "colors")))   

    def draw(self, layout):
        layout.prop(self, "clamp")
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.usecolor1List and self.usecolor2List and self.usefactorList :
            return "execute_allList"
        elif self.usecolor1List and self.usecolor2List == 0 and self.usefactorList == 0 :
            return "execute_onlyColAList"
        elif self.usecolor1List == 0 and self.usecolor2List and self.usefactorList == 0 :
            return "execute_onlyColBList"
        elif self.usecolor1List == 0 and self.usecolor2List ==0 and self.usefactorList :
            return "execute_onlyFactorList"
        elif self.usecolor1List and self.usecolor2List ==0 and self.usefactorList :
            return "execute_ColA_Factor_isList"
        elif self.usecolor1List == 0 and self.usecolor2List and self.usefactorList :
            return "execute_ColB_Factor_isList"
        elif self.usecolor1List and self.usecolor2List and self.usefactorList == 0 :
            return "execute_ColA_ColB_isList"
        else:
            return "execute_allSingle"                        

    def execute_allList(self, colorsA, colorsB, factors, alpha):
        if len(colorsA) == 0 or len(colorsB) == 0 or len(factors) == 0:
            self.raiseErrorMessage("Reconnect Output Socket")
            return ColorList()

        if len(colorsA) == len(colorsB) == len(factors):
            colA = np.array(colorsA)
            colB = np.array(colorsB)
            shaped_factor = np.repeat(factors, 4).reshape(-1, 4)
        else:
            maxLength = max(max(len(colorsA), len(colorsB)), len(factors))
            colA = np.array(VirtualColorList.create(colorsA, colorsA[-1]).materialize(maxLength))
            colB = np.array(VirtualColorList.create(colorsB, colorsB[-1]).materialize(maxLength))
            factor = np.array(VirtualDoubleList.create(factors, factors[-1]).materialize(maxLength))
            shaped_factor = np.repeat(factor, 4).reshape(-1, 4)   
        mode = self.mode
        if self.clamp:
            shaped_factor = np.clip(shaped_factor, 0.00, 1.00)

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

        out = self.color_mix(colA, result, shaped_factor)
        out[:,-1] = alpha
        if self.clamp:
            out = np.clip(out, 0.00, 1.00)       
        return out.tolist()           
         
    def color_mix(self, colorsA, colorsB, factor):
        return (1 - factor) * colorsA + factor * colorsB

    def execute_onlyColAList(self, colorsA, colorB, factor, alpha):
        colorsB = ColorList.fromValues([colorB])
        return self.execute_allList(colorsA, colorsB, [factor], alpha)

    def execute_onlyColBList(self, colorA, colorsB, factor, alpha):
        colorsA = ColorList.fromValues([colorA])
        return self.execute_allList(colorsA, colorsB, [factor], alpha)

    def execute_onlyFactorList(self, colorA, colorB, factors, alpha):
        colorsA = ColorList.fromValues([colorA])
        colorsB = ColorList.fromValues([colorB])
        return self.execute_allList(colorsA, colorsB, factors, alpha)

    def execute_ColA_Factor_isList(self, colorsA, colorB, factors, alpha):
        colorsB = ColorList.fromValues([colorB])
        return self.execute_allList(colorsA, colorsB, factors, alpha) 

    def execute_ColB_Factor_isList(self, colorA, colorsB, factors, alpha):
        colorsA = ColorList.fromValues([colorA])
        return self.execute_allList(colorsA, colorsB, factors, alpha)

    def execute_ColA_ColB_isList(self, colorsA, colorsB, factor, alpha):
        return self.execute_allList(colorsA, colorsB, [factor], alpha)

    def execute_allSingle(self, colorA, colorB, factor, alpha):
        colorsA = ColorList.fromValues([colorA])
        colorsB = ColorList.fromValues([colorB])
        result = self.execute_allList(colorsA, colorsB, [factor], alpha)
        return result[0] 

   