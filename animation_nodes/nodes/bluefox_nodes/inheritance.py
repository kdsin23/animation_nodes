import bpy
from math import *
from bpy.props import *
from mathutils import Matrix
from ... base_types import AnimationNode
from ... events import propertyChanged
from ... events import executionCodeChanged
from ... data_structures import *
from ..matrix.c_utils import extractMatrixTranslations

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

    swap = BoolProperty(name = "Swap", default = False, update = propertyChanged)

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
        layout.prop(self, "swap")


    def getExecutionFunctionName(self):
        if self.mode == "VECTORS":
            return "Vector_lerp"
        elif self.mode == "MATRICES":
            return "Matrix_lerp"         

    def Matrix_lerp(self, m1, m2, falloff, step ):

        if self.swap:
            x1 = m2
            x2 = m1
        else:
            x1 = m1
            x2 = m2   

        if x1 is None or x2 is None or falloff is None :
            return Matrix4x4List(), DoubleList()

        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influences = falloffEvaluator.evaluateList(extractMatrixTranslations(x1))

        out_matrixlist = Matrix4x4List()
        values = []

        for i, item in enumerate( x1 ):
                step_result = self.snap_number( influences[i], step )
                values . append(step_result)
                out_matrixlist . append( item . lerp( x2[i], step_result ))       
        return out_matrixlist, DoubleList . fromValues( values )
        
    def Vector_lerp( self, v1, v2, falloff, step ):

        if self.swap:
            x1 = v2
            x2 = v1
        else:
            x1 = v1
            x2 = v2   

        if x1 is None or x2 is None or falloff is None :
            return Vector3DList(), DoubleList()

        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influences = falloffEvaluator.evaluateList(x1)

        out_vectorlist = Vector3DList()
        values = []

        for i, item in enumerate( x1 ):
                step_result = self.snap_number( influences[i], step )
                values . append( step_result )
                out_vectorlist . append( item . lerp( x2[i], step_result ) )       
        return out_vectorlist, DoubleList . fromValues( values )        

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, num, step ):
        step_result = round( num / step ) * step if step != 0 else num
        return step_result
                
        

             