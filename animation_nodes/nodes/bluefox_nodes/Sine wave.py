import bpy
from math import *
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import *
from ... events import executionCodeChanged
from ... sockets.info import toListDataType
from..falloff.custom_falloff import CustomFalloff
from ..number.c_utils import *

modeItems = [
    ("ANIMATE", "Animated", "Animate on frame", "", 0),
    ("MANUAL", "Manual", "Manual offset", "", 1)
]

class Sinewave(bpy.types.Node, AnimationNode):
    bl_idname = "an_sinewave"
    bl_label = "Sine wave falloff"

    mode = EnumProperty(name = "Mode", default = "ANIMATE",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        
        self.newInput("Integer", "n", "n", value = 10, minValue = 1)
        if self.mode == "ANIMATE":
            self.newInput("Float", "speed", "speed", value = 0.5)
        elif self.mode == "MANUAL":
            self.newInput("Float", "offset", "offset", value = 0)
               
        self.newInput("Float", "frequency", "freq", value = 5.0)
        self.newInput("Float", "Amplitude", "amp", value = 1.0)
        self.newInput("Float", "Step gap", "step", value = 0.0, minValue = 0)
        self.newInput("Float", "Fallback", "fallback", hide = True)

        self.newOutput("Falloff", "Falloff", "outFalloff")
        self.newOutput("Float List", "strengths", "strengths")

    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "ANIMATE":
            return "execute_Animate"
        elif self.mode == "MANUAL":
            return "execute_Manual"    

    def execute_Animate(self, n, speed, freq, amp, step, fallback):

        if n is None :
            return
        if n <= 0: return DoubleList()
        T=bpy.context.scene.frame_current
        offset = T*speed
        out = self.sinewave_fun(n, offset, freq, amp, step, fallback)
        return CustomFalloff(FloatList.fromValues(out), fallback), DoubleList.fromValues(out)

    def execute_Manual(self, n, offset, freq, amp, step, fallback):

        out = self.sinewave_fun(n, offset, freq, amp, step, fallback)
        return CustomFalloff(FloatList.fromValues(out), fallback), DoubleList.fromValues(out)   

    def sinewave_fun(self, n, offset, freq, amp, step, fallback):

        if n is None :
            return
        if n <= 0: return DoubleList()
        x=range_DoubleList_StartStep(n, 0, (1 - 0) / n)
        z=[]
        for i in x:
            a=amp*(sin((i*freq)+offset))
            out=self.snap_number(a, step)
            z.append(out)

        return z

    def snap_number( self, num, step ):
        step_result = round( num / step ) * step if step != 0 else num
        return step_result    

#unused function
    """
    def saw_fun(self, n, offset, freq, amp, step, fallback):

        if n is None :
            return
        if n <= 0: return DoubleList()
        x=range_DoubleList_StartStep(n, 0, (1 - 0) / n)
        z=[]
        for i in x:
            a = amp - amp * (((i / (freq/10) + (offset/10)) * 2) % 2)
            out=round(a / step) * step if step != 0 else a
            z.append(out)

        return z
    """    

        
        