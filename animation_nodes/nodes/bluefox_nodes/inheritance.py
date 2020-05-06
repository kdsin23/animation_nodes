import bpy
import numpy as np
from bpy.props import *
from mathutils import Matrix
from..matrix.c_utils import extractMatrixTranslations
from ... base_types import AnimationNode, VectorizedSocket
from ... events import executionCodeChanged, propertyChanged
from .. spline . spline_evaluation_base import SplineEvaluationBase
from..bluefox_nodes.c_utils import matrix_lerp, vector_lerp, inheritanceCurve
from ... data_structures import DoubleList, Matrix4x4List, Vector3DList, VirtualMatrix4x4List, VirtualVector3DList, FloatList

inheritancemodeItems = [
    ("VECTORS", "Vectors", "Vector list in", "", 0),
    ("MATRICES", "Matrices", "Matrix list in", "", 1)
]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along curve path", "", 1)
]

class Inheritanceffector(bpy.types.Node, AnimationNode, SplineEvaluationBase):
    bl_idname = "an_Inheritanceffector"
    bl_label = "Inheritance effector"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    useV1List: VectorizedSocket.newProperty()
    useV2List: VectorizedSocket.newProperty()
    useM1List: VectorizedSocket.newProperty()
    useM2List: VectorizedSocket.newProperty()

    __annotations__["mode"] = EnumProperty(name = "Type", default = "VECTORS",
        items = inheritancemodeItems, update = AnimationNode.refresh)

    __annotations__["selectMode"] = EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)    

    def create(self):
        if self.mode == "VECTORS":
            self.newInput(VectorizedSocket("Vector", "useV1List",
            ("Vector A", "va"), ("Vectors A", "v1")))
            self.newInput(VectorizedSocket("Vector", "useV2List",
            ("Vector B", "vb"), ("Vectors B", "v2")))
            self.newOutput(VectorizedSocket("Vector", ["useV1List", "useV2List"],
            ("Vector out", "vec_out"), ("Vectors out", "vecs_out")))
            self.newOutput(VectorizedSocket("Float", ["useV1List", "useV2List"],
            ("Value", "value"), ("Values", "values")))
            if self.selectMode == "SPLINE":
                self.newInput("Spline", "Path", "path", defaultDrawType = "PROPERTY_ONLY")
                self.newInput("Float", "Min", "varMin", value = 0, hide = True)
                self.newInput("Float", "Max", "varMax", value = 1, hide = True)
                self.newInput("Float", "Randomness", "randomness", value = 0.5)
                self.newInput("Float", "Smoothness", "smoothness", value = 0.33, hide = True)
                
        elif self.mode == "MATRICES":
            self.newInput(VectorizedSocket("Matrix", "useM1List",
            ("Matrix A", "ma"), ("Matrices A", "m1")))
            self.newInput(VectorizedSocket("Matrix", "useM2List",
            ("Matrix B", "mb"), ("Matrices B", "m2")))
            self.newOutput(VectorizedSocket("Matrix", ["useM1List", "useM2List"],
            ("Matrix out", "mat_out"), ("Matrices out", "mats_out")))
            self.newOutput(VectorizedSocket("Float", ["useM1List", "useM2List"],
            ("Value", "value"), ("Values", "values")))

        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "step gap", "step", hide = True)
    
    def draw(self, layout):
        layout.prop(self, "mode", text = "")
        if self.mode == "VECTORS":
            layout.prop(self, "selectMode")

    def getExecutionFunctionName(self):
        if self.mode == "VECTORS":
            if self.selectMode == "LINEAR":
                return "VectorLerpFunction"
            else:
                return "vectorCurveInheritance"        
        else:
            return "MatrixLerpFunction"          
    
    def MatrixLerpFunction(self, m1, m2, falloff, step ):
        if not self.useM1List: m1 = Matrix4x4List.fromValues([m1])
        if not self.useM2List: m2 = Matrix4x4List.fromValues([m2])

        if len(m1)==0 or len(m2)==0:
            return Matrix4x4List(), DoubleList()

        lenmax = max(len(m1),len(m2))     
        falloffEvaluator = self.getFalloffEvaluator(falloff)

        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step ))
        if len(m1)>len(m2):
            _m2 = VirtualMatrix4x4List.create(m2, Matrix.Identity(4)).materialize(lenmax)
            result = matrix_lerp(m1,_m2,influences)
        elif len(m2)>len(m1):  
            _m1 = VirtualMatrix4x4List.create(m1, Matrix.Identity(4)).materialize(lenmax)
            if step==0:
                influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(_m1)))
            else:
                influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(_m1)), step ))
            result = matrix_lerp(_m1,m2,influences)
        else:
            result = matrix_lerp(m1,m2,influences)

        if  self.useM1List == 0 and self.useM2List ==0:
            return result[0], influences[0] 
        else:
            return result, influences       

    def VectorLerpFunction( self, v1, v2, falloff, step ):
        if not self.useV1List: v1 = Vector3DList.fromValues([v1])
        if not self.useV2List: v2 = Vector3DList.fromValues([v2])

        if len(v1)==0 or len(v2)==0:
            return Vector3DList(), DoubleList()
        lenmax = max(len(v1),len(v2))      
        falloffEvaluator = self.getFalloffEvaluator(falloff)

        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))
        if len(v1)>len(v2):
            _v2 = VirtualVector3DList.create(v2,(0,0,0)).materialize(lenmax)
            result = vector_lerp(v1, _v2, influences)
        elif len(v2)>len(v1):
            _v1 = VirtualVector3DList.create(v1,(0,0,0)).materialize(lenmax)
            if step==0:
                influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(_v1))
            else:
                influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(_v1), step ))
            result = vector_lerp(_v1, v2, influences)
        else:
            result = vector_lerp(v1, v2, influences)

        if self.useV1List == 0 and self.useV2List == 0:
            return result[0], influences[0]
        else:
            return result, influences 

    def vectorCurveInheritance(self, v1, v2, path, varMin, varMax, randomness, smoothness, falloff, step):
        if not self.useV1List: v1 = Vector3DList.fromValues([v1])
        if not self.useV2List: v2 = Vector3DList.fromValues([v2])

        if len(v1)==0 or len(v2)==0:
            return Vector3DList(), DoubleList()
        lenmax = max(len(v1),len(v2))
        resolution = self.resolution
        pathPoints = path.points      
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))
        if len(v1)>len(v2):
            _v2 = VirtualVector3DList.create(v2,(0,0,0)).materialize(lenmax)
            result = inheritanceCurve(v1, _v2, pathPoints, varMin, varMax, randomness, smoothness, influences, resolution)
        elif len(v2)>len(v1):
            _v1 = VirtualVector3DList.create(v1,(0,0,0)).materialize(lenmax)
            if step==0:
                influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(_v1))
            else:
                influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(_v1), step ))
            result = inheritanceCurve(_v1, v2, pathPoints, varMin, varMax, randomness, smoothness, influences, resolution)
        else:
            result = inheritanceCurve(v1, v2, pathPoints, varMin, varMax, randomness, smoothness, influences, resolution)

        if self.useV1List == 0 and self.useV2List == 0:
            return result[0], influences[0]
        else:
            return result, influences           

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, nums, step ):
        num=np.asarray(nums)
        step_result = np.round( num / step ) * step if step != 0 else num
        return FloatList.fromNumpyArray(step_result.astype('float32')) 
      