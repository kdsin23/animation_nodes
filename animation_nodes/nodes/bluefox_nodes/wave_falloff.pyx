import bpy
cimport cython
from bpy.props import *
from ... utils.clamp cimport clampLong
from ... math cimport abs as absNumber
from libc.math cimport M_PI, asin, atan
from ... base_types import AnimationNode
from ... data_structures cimport BaseFalloff
from ... math cimport Vector3, setVector3, distanceVec3, sin, tan

WaveTypeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

class WaveFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_wavefalloff"
    bl_label = "Wave falloff"

    __annotations__ = {}
    __annotations__["waveType"] = EnumProperty(name = "Wave Type", default = "SINE",
        items = WaveTypeItems, update = AnimationNode.refresh)
    __annotations__["enableRipple"] = BoolProperty(name = "Enable Ripple", update = AnimationNode.refresh)        

    def create(self):
        if self.enableRipple:
            self.newInput("Vector", "Origin", "origin")
        else:    
            self.newInput("Integer", "Index", "index", value = 0)
            self.newInput("Integer", "Amount", "amount", value = 10, minValue = 0)
        self.newInput("Float", "Frequency", "frequency", value = 1)
        self.newInput("Float", "Offset", "offset", value = 0)
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Boolean", "Clamp", "clamp", value = False)

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "enableRipple", text = "", icon = "PROP_ON")
        row2 = row.row(align = True)
        row2.prop(self, "waveType", text = "")

    def getExecutionFunctionName(self):
        if self.enableRipple: 
            return "executeRipple"
        else:
            return "executeBasic"    

    def executeBasic(self, index, amount, frequency, offset, amplitude, clamp):
        return WaveFalloff((0,0,0), index, index + amount, frequency, offset, amplitude, self.waveType, self.enableRipple, clamp)

    def executeRipple(self, origin, frequency, offset, amplitude, clamp):
        return WaveFalloff(origin, 0, 0, frequency, offset, amplitude, self.waveType, self.enableRipple, clamp)

cdef class WaveFalloff(BaseFalloff):
    cdef:
        long index, amount
        float indexDiff
        float frequency, offset, amplitude
        str waveType
        bint enableRipple, clamp
        Vector3 origin

    def __cinit__(self, origin, index, amount, frequency, offset, amplitude, waveType, enableRipple, clamp):
        self.index = clampLong(index)
        self.amount = clampLong(amount)
        self.indexDiff = <float>(self.amount - self.index)
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.clamp = clamp
        self.enableRipple = enableRipple
        self.waveType = waveType
        self.clamped = True
        setVector3(&self.origin, origin)
        self.dataType = "NONE"
        if self.enableRipple:
            self.dataType = "LOCATION"

    @cython.cdivision(True)
    cdef float evaluate(self, void *object, Py_ssize_t index):
        cdef float influence, offset, frequency, temp, result, inf
        cdef Py_ssize_t i

        if index <= self.index:
            influence = 0
        if index >= self.amount: 
            influence = 1
        else:
            influence = <float>(index - self.index) / self.indexDiff
        if self.enableRipple:
           influence = distanceVec3(<Vector3*>object, &self.origin)/10

        if self.clamp:
            return max(min(wave(self, influence), 1), 0)
        else:    
            return wave(self, influence)

@cython.cdivision(True)
cdef inline float wave(WaveFalloff self, float i):
    cdef float temp, offset, frequency
    cdef float result = 0

    offset = self.offset * -1
    frequency = self.frequency

    if self.waveType == "SINE":
        result = sin(2 * M_PI * i * frequency + offset)
    elif self.waveType == "SQUARE":
        temp = sin(2 * M_PI * i * frequency + offset)
        if temp < 0:
            result = -1 
        else:
            result = 1   
    elif self.waveType == "TRIANGULAR":
        temp = asin(sin((2 * M_PI * i * frequency) + offset)) # ranges b/w -pi/2 and pi/2
        result = (temp / M_PI + 0.5) * 2 - 1 # make range -1 to 1
    elif self.waveType == "SAW":
        result = 2 / M_PI * atan(1 / tan(i * frequency * M_PI + offset))
        
    return result * self.amplitude
