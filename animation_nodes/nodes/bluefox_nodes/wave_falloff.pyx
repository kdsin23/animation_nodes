import bpy
cimport cython
from bpy.props import *
from ... math cimport sin
from ... base_types import AnimationNode
from ... data_structures cimport BaseFalloff

modeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

class WaveFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_wavefalloff"
    bl_label = "Wave falloff"

    __annotations__ = {}
    __annotations__["mode"] = EnumProperty(name = "Type ", default = "SINE",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Float", "Amplitude", "amplitude", value = 1.0)
        self.newInput("Float", "Frequency", "frequency", value = 5.0)
        self.newInput("Float", "Offset", "offset")
        self.newInput("Boolean", "Clamp", "clamp", value = False)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "mode", text = "")    

    def execute(self, amplitude, frequency, offset, clamp):
        return WaveFalloff(frequency, amplitude, offset, clamp, self.mode)

cdef class WaveFalloff(BaseFalloff):
    cdef:
        bint clamp
        str mode
        float frequency, amplitude, offset

    def __cinit__(self, float frequency, float amplitude, float offset, bint clamp, str mode):
        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.mode = mode
        self.clamp = clamp
        self.dataType = "LOCATION"
        
    cdef float evaluate(self, void *value, Py_ssize_t index):
        return sinwav(self, index)    

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                            Py_ssize_t amount, float *target):                  
        for i in range(amount):
            if self.clamp:
                target[i] = max(min(wave(self, i/amount), 1), 0)
            else:
                target[i] = wave(self, i/amount)

@cython.cdivision(True)
cdef inline float wave(WaveFalloff self, float i):
    cdef float result, temp
    if self.mode == "SINE":
        result = sin(i * self.frequency + self.offset)
    elif self.mode == "SQUARE":
        temp = sin(i * self.frequency + self.offset)
        if temp < 0:
            result = 1 
        else:
            result = -1 
    elif self.mode == "TRIANGULAR":
        temp = (i * self.frequency + self.offset / 10) * 2
        result = 2 * (((i * self.frequency + self.offset / 10) * 2) % 1) - 1
        if not temp % 2 > 1:
            result *= -1
    elif self.mode == "SAW":
        result = ((i * self.frequency + self.offset / 10) * 2) % 2
    return result * self.amplitude
