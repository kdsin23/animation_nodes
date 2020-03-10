import bpy
from math import *
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import DoubleList
from ... data_structures import Vector3DList



class fibinocci(bpy.types.Node, AnimationNode):
    bl_idname = "an_fibinocci"
    bl_label = "fibinocci"
    
    
    def create(self):
        self.newInput("Float", "First", "x1")
        self.newInput("Float", "Second", "x2")
        self.newInput("Integer", "count", "count")
        self.newInput("Float", "MaxValue", "maxValue")
        
        self.newOutput("Float List", "result", "res")
        
    
    def execute(self, x1, x2, count, maxValue):
        if x1 is None or x2 is None:
            return
        result = self.fibonacci(x1, x2, count, maxValue)    
        return DoubleList.fromValues(result) 


    def fibonacci(self, x1, x2, count, maxValue):

        result = [x1,x2]
        for i in range(count-2):
            r = x1 + x2
            result.append(r)
            x1 = x2
            x2 = r

        if maxValue:
            actualMax = max(map(abs, result))
            if actualMax == 0.0:
                return result
            result = [x*maxValue/actualMax for x in result]

        return result    