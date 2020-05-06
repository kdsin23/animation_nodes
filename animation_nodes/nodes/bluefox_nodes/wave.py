import bpy
import numpy as np
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import FloatList, DoubleList
from ... events import executionCodeChanged
from..falloff.custom_falloff import CustomFalloff

#inspired by sverchok oscillator node

modeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

class Wavefalloff(bpy.types.Node, AnimationNode):
    bl_idname = "an_wavefalloff"
    bl_label = "Wave falloff"

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Type ", default = "SINE",
        items = modeItems, update = AnimationNode.refresh)

    __annotations__["check_animated"] = BoolProperty(name = "Animated", default = False, update = AnimationNode.refresh)  

    def create(self):
        self.newInput("Integer", "n", "n", value = 10, minValue = 1)
        if self.check_animated == True:
            self.newInput("Float", "speed", "speed", value = 0.2)
        elif self.check_animated == False:
            self.newInput("Float", "offset", "offset", value = 0)      
        self.newInput("Float", "frequency", "freq", value = 4.0)
        self.newInput("Float", "Amplitude", "amp", value = 1.0, minValue = 0.00001)
        self.newInput("Float", "Angle", "angle", value = 360.0)    
        self.newInput("Float", "Step gap", "step", value = 0.0, minValue = 0)
        self.newInput("Float", "Fallback", "fallback", hide = True)

        self.newOutput("Falloff", "Falloff", "outFalloff")
        self.newOutput("Float List", "strengths", "strengths")

    def draw(self, layout):
        layout.prop(self, "mode")
        layout.prop(self, "check_animated")

    def getExecutionFunctionName(self):
        if self.check_animated == True:
            return "execute_Animate"
        elif self.check_animated == False:
            return "execute_Manual"    

    def execute_Animate(self, n, speed, freq, amp, angle, step, fallback):
        offset = speed * bpy.context.scene.frame_current
        if self.mode == "SINE":
            out = self.sinewave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "SQUARE":
            out = self.squarewave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "TRIANGULAR":
            out = self.triangularwave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "SAW":
            out = self.sawwave_fun(n, offset, freq, amp, angle, step, fallback)
        values = FloatList.fromNumpyArray(out.astype('float32'))                 
        return CustomFalloff(values, fallback), values

    def execute_Manual(self, n, offset, freq, amp, angle, step, fallback):
        if self.mode == "SINE":
            out = self.sinewave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "SQUARE":
            out = self.squarewave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "TRIANGULAR":
            out = self.triangularwave_fun(n, offset, freq, amp, angle, step, fallback)
        elif self.mode == "SAW":
            out = self.sawwave_fun(n, offset, freq, amp, angle, step, fallback)   
        values = FloatList.fromNumpyArray(out.astype('float32'))                 
        return CustomFalloff(values, fallback), values  

    def sinewave_fun(self, n, offset, freq, amp, angle, step, fallback):
        z=np.linspace(0.00, 1.00, num=n, endpoint=False)
        k=amp * np.sin((z*freq/100 + offset/100) * angle)
        out=self.maprange_fun((self.snap_number(k, step)), -(amp), amp, 0, amp)
        return out

    def squarewave_fun(self, n, offset, freq, amp, angle, step, fallback):
        z=np.linspace(0.00, 1.00, num=n, endpoint=False)
        act_phase = np.ones(n)
        mask = np.sin((z*freq/100 + offset/100) *angle) < 0
        act_phase[mask] = -1
        res = amp * act_phase
        out=self.maprange_fun((self.snap_number(res, step)), -(amp), amp, 0, amp)
        return out  

    def triangularwave_fun(self, n, offset, freq, amp, angle, step, fallback):
        z=np.linspace(0.00, 1.00, num=n, endpoint=False)
        mask = ((z*freq/360*angle + offset) * 2) % 2 > 1
        res = 2 * amp * (((z*freq + offset)*2) % 1) - amp
        res[mask] *= -1
        out=self.maprange_fun((self.snap_number(res, step)), -(amp), amp, 0, amp)
        return out 

    def sawwave_fun(self, n, offset, freq, amp, angle, step, fallback):
        z=np.linspace(0.00, 1.00, num=n, endpoint=False)
        res = amp - amp * (((z * freq/360*angle + offset) * 2) % 2)
        out=self.maprange_fun((self.snap_number(res, step)), -(amp), amp, 0, amp)
        return out           

    def snap_number( self, num, step ):
        step_result = np.round( num / step ) * step if step != 0 else num
        return step_result 

    def maprange_fun(self, value, leftMin, leftMax, rightMin, rightMax):
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin
        valueScaled = (value - leftMin) / (leftSpan)
        return rightMin + (valueScaled * rightSpan)       
