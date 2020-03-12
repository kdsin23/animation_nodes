import bpy
from math import *
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import DoubleList
from ... data_structures import Vector3DList

modeItems = [
    ("POINTS", "Points", "Vector points", "", 0),
    ("NUMBERS", "Numbers", "Numbers", "", 1)
]


class fibonaccii(bpy.types.Node, AnimationNode):
    bl_idname = "an_fibonacci"
    bl_label = "fibonacci"

    mode = EnumProperty(name = "Mode", default = "POINTS",
        items = modeItems, update = AnimationNode.refresh)
    
    
    def create(self):
        if self.mode == "NUMBERS":
            self.newInput("Float", "First", "x1")
            self.newInput("Float", "Second", "x2")
            self.newInput("Integer", "count", "count", minValue = 0)
            self.newInput("Float", "Max Value", "maxValue")
        
            self.newOutput("Float List", "result", "res")
        elif self.mode == "POINTS":
            self.newInput("Integer", "count", "count", value = 200, minValue = 1)
            self.newInput("Float", "Scale", "scale", value = 0.5)
        
            self.newOutput("Vector List", "Points", "Points_out")

    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "POINTS":
            return "execute_fibonacci_points"
        elif self.mode == "NUMBERS":
            return "execute_fibonacci_numbers"                
        

    def execute_fibonacci_points(self, count, scale):
        
        points = Vector3DList()
        golden_angle = pi*(3-sqrt(5))
        for i in range(count):
            theta = i*golden_angle
            r= sqrt(i)/ sqrt(count)
            points.append((r*cos(theta)*scale, r*sin(theta)*scale, 0))
        return points



    def execute_fibonacci_numbers(self, x1, x2, count, maxValue):
        if x1 is None or x2 is None:
            return
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

        return DoubleList.fromValues(result)    