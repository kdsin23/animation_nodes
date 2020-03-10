import bpy
import numpy as np
from math import *
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import DoubleList
from ... events import executionCodeChanged
from ... sockets.info import toListDataType

from . c_utils import (
    range_LongList_StartStep,
    range_DoubleList_StartStep,
    range_DoubleList_StartStop
)

modeItems = [
    ("ANIMATE", "Animate", "Animate on frame", "", 0),
    ("MANUAL", "Manual", "Manual offset", "", 1)
]

class Sinewave(bpy.types.Node, AnimationNode):
    bl_idname = "an_sinewave"
    bl_label = "Sine wave"

    mode = EnumProperty(name = "Mode", default = "ANIMATE",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Integer", "n", "n", value = 10)
        if self.mode == "ANIMATE":
            self.newInput("Float", "speed", "speed", value = 0.5)
        elif self.mode == "MANUAL":
            self.newInput("Float", "offset", "offset", value = 0)    
        self.newInput("Float", "frequency", "freq", value = 5.0)
        self.newInput("Float", "Amplitude", "amp", value = 1.0)
        self.newInput("Float", "Snap", "step", value = 0.0, minValue = 0)

        self.newOutput("Float List", "strengths", "strengths")
    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "ANIMATE":
            return "execute_Animate"
        elif self.mode == "MANUAL":
            return "execute_Manual"    

    def execute_Animate(self, n, speed, freq, amp, step):

        if n is None :
            return
        if n <= 0: return DoubleList()
        T=bpy.context.scene.frame_current
        offset = T*speed
        out = self.sinewave_fun(n, offset, freq, amp, step)
        return out

    def execute_Manual(self, n, offset, freq, amp, step):

        out = self.sinewave_fun(n, offset, freq, amp, step)
        return out   

    def sinewave_fun(self, n, offset, freq, amp, step):

        if n is None :
            return
        if n <= 0: return DoubleList()
        x=range_DoubleList_StartStep(n, 0, (1 - 0) / n)
        z=[]
        for i in x:
            a=amp*(sin((i*freq)+offset))
            out=round(a / step) * step if step != 0 else a
            z.append(out)

        return DoubleList.fromValues(z)

#unused function
    def saw_fun(self, n, offset, freq, amp, step):

        if n is None :
            return
        if n <= 0: return DoubleList()
        x=range_DoubleList_StartStep(n, 0, (1 - 0) / n)
        z=[]
        for i in x:
            a = amp - amp * (((i / freq + offset) * 2) % 2)
            out=round(a / step) * step if step != 0 else a
            z.append(out)

        return DoubleList.fromValues(z)

        
        