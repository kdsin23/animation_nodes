import bpy
import numpy as np
from bpy.props import *
from ... data_structures import *
from..bluefox_nodes.c_utils import *
from ... base_types import AnimationNode
from ... events import propertyChanged
from..matrix.c_utils import extractMatrixTranslations

modeItems = [
    ("VECTORS", "Vectors", "Vector list in", "", 0),
    ("MATRICES", "Matrices", "Matrix list in", "", 1)
]

class Inheritanceffector(bpy.types.Node, AnimationNode):
    bl_idname = "an_Inheritanceffector"
    bl_label = "Inheritance effector"
    errorHandlingType = "EXCEPTION"

    mode = EnumProperty(name = "Mode", default = "VECTORS",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        if self.mode == "VECTORS":
            self.newInput("Vector List", "Vectors A", "v1")
            self.newInput("Vector List", "Vectors B", "v2")
            self.newOutput("Vector List", "Vector list", "outMatrices2")
            self.newOutput("Float List", "Values", "val_v")
        elif self.mode == "MATRICES":
            self.newInput("Matrix List", "Matrices A", "m1")
            self.newInput("Matrix List", "Matrices B", "m2")
            self.newOutput("Matrix List", "Matrices", "outMatrices3")
            self.newOutput("Float List", "Values", "val_m")
    
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "step gap", "step")
    
    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "VECTORS":
            return "Vector_lerp"
        elif self.mode == "MATRICES":
            return "Matrix_lerp"         

    def Matrix_lerp(self, m1, m2, falloff, step ):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step ))    

        try:
            return matrixlerp(m1, m2, influences), influences
        except IndexError:
            return m1, influences

    def Vector_lerp( self, v1, v2, falloff, step ):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))

        try:
            return vectorlerp(v1, v2, influences), influences
        except IndexError:
            return v1, influences           

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, nums, step ):
        num=np.asarray(nums)
        step_result = np.round( num / step ) * step if step != 0 else num
        return step_result.tolist() 
   

                