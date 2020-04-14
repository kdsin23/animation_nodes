import bpy
import numpy as np
from bpy.props import *
from mathutils import Matrix
from ... data_structures import DoubleList, Matrix4x4List, Vector3DList, VirtualMatrix4x4List, VirtualVector3DList 
from..bluefox_nodes.c_utils import matrix_lerp, vector_lerp
from ... events import executionCodeChanged, propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from..matrix.c_utils import extractMatrixTranslations

inheritancemodeItems = [
    ("VECTORS", "Vectors", "Vector list in", "", 0),
    ("MATRICES", "Matrices", "Matrix list in", "", 1)
]

class Inheritanceffector(bpy.types.Node, AnimationNode):
    bl_idname = "an_Inheritanceffector"
    bl_label = "Inheritance effector"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    usev1List: VectorizedSocket.newProperty()
    usev2List: VectorizedSocket.newProperty()
    usem1List: VectorizedSocket.newProperty()
    usem2List: VectorizedSocket.newProperty()

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "VECTORS",
        items = inheritancemodeItems, update = AnimationNode.refresh)

    def create(self):
        if self.mode == "VECTORS":
            self.newInput(VectorizedSocket("Vector", "usev1List",
            ("Vector A", "va"), ("Vectors A", "v1")))
            self.newInput(VectorizedSocket("Vector", "usev2List",
            ("Vector B", "vb"), ("Vectors B", "v2")))
            self.newOutput(VectorizedSocket("Vector", ["usev1List", "usev2List"],
            ("Vector out", "vec_out"), ("Vectors out", "vecs_out")))
            self.newOutput(VectorizedSocket("Float", ["usev1List", "usev2List"],
            ("Value", "value"), ("Values", "values")))
        elif self.mode == "MATRICES":
            self.newInput(VectorizedSocket("Matrix", "usem1List",
            ("Matrix A", "ma"), ("Matrices A", "m1")))
            self.newInput(VectorizedSocket("Matrix", "usem2List",
            ("Matrix B", "mb"), ("Matrices B", "m2")))
            self.newOutput(VectorizedSocket("Matrix", ["usem1List", "usem2List"],
            ("Matrix out", "mat_out"), ("Matrices out", "mats_out")))
            self.newOutput(VectorizedSocket("Float", ["usem1List", "usem2List"],
            ("Value", "value"), ("Values", "values")))
    
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "step gap", "step")
    
    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "VECTORS" and self.usev1List and self.usev2List:
            return "Vector_lerp_2list"
        elif self.mode == "VECTORS" and self.usev1List and self.usev2List==0:
            return "Vector_lerp_listA" 
        elif self.mode == "VECTORS" and self.usev1List==0 and self.usev2List:
            return "Vector_lerp_listB"
        elif self.mode == "VECTORS" and self.usev1List==0 and self.usev2List==0:
            return "Vector_lerp_single"             
        elif self.mode == "MATRICES" and self.usem1List and self.usem2List:
            return "Matrix_lerp_2list"
        elif self.mode == "MATRICES" and self.usem1List and self.usem2List==0:
            return "Matrix_lerp_listA" 
        elif self.mode == "MATRICES" and self.usem1List==0 and self.usem2List:
            return "Matrix_lerp_listB"
        elif self.mode == "MATRICES" and self.usem1List==0 and self.usem2List==0:
            return "Matrix_lerp_single"          

    def Matrix_lerp_2list(self, m1, m2, falloff, step ):
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
            return matrix_lerp(m1,_m2,influences), influences
        elif len(m2)>len(m1):  
            _m1 = VirtualMatrix4x4List.create(m1, Matrix.Identity(4)).materialize(lenmax)
            if step==0:
                influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(_m1)))
            else:
                influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(_m1)), step ))
            return matrix_lerp(_m1,m2,influences), influences
        else:
            return matrix_lerp(m1,m2,influences), influences

    def Matrix_lerp_listA( self, m1, mb, falloff, step ):
        if len(m1)==0 :
            return Matrix4x4List(), DoubleList()
        lenmax = len(m1)     
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        m2 = Matrix4x4List.fromValue(mb ,length = lenmax)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step ))
        return matrix_lerp(m1, m2, influences), influences 

    def Matrix_lerp_listB( self, ma, m2, falloff, step ):
        if len(m2)==0 :
            return Matrix4x4List(), DoubleList()
        lenmax = len(m2)     
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        m1 = Matrix4x4List.fromValue(ma ,length = lenmax)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step ))
        return matrix_lerp(m1, m2, influences), influences 

    def Matrix_lerp_single(self, ma, mb, falloff, step):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        m1=Matrix4x4List.fromValue(ma ,length = 1)
        influences = DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(extractMatrixTranslations(m1)), step ))
        out_vector = ma.lerp(mb, influences[0])
        return out_vector, influences[0]                       

    def Vector_lerp_2list( self, v1, v2, falloff, step ):
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
            return vector_lerp(v1, _v2, influences), influences
        elif len(v2)>len(v1):
            _v1 = VirtualVector3DList.create(v1,(0,0,0)).materialize(lenmax)
            if step==0:
                influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(_v1))
            else:
                influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(_v1), step ))
            return vector_lerp(_v1, v2, influences), influences
        else:
            return vector_lerp(v1, v2, influences), influences 

    def Vector_lerp_listA( self, v1, vb, falloff, step ):
        if len(v1)==0 :
            return Vector3DList(), DoubleList()
        lenmax = len(v1)     
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        v2 = Vector3DList.fromValue(vb ,length = lenmax)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))
        return vector_lerp(v1, v2, influences), influences

    def Vector_lerp_listB( self, va, v2, falloff, step ):
        if len(v2)==0 :
            return Vector3DList(), DoubleList()
        lenmax = len(v2)     
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        v1 = Vector3DList.fromValue(va ,length = lenmax)
        if step==0:
            influences =  DoubleList.fromValues(falloffEvaluator.evaluateList(v1))
        else:
            influences =  DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))
        return vector_lerp(v1, v2, influences), influences 

    def Vector_lerp_single(self, va, vb, falloff, step):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        v1=Vector3DList.fromValue(va ,length = 1)
        influences = DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(v1), step ))
        out_vector = va.lerp(vb, influences[0])
        return out_vector, influences[0]                           

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, nums, step ):
        num=np.asarray(nums)
        step_result = np.round( num / step ) * step if step != 0 else num
        return step_result.tolist() 

    

                