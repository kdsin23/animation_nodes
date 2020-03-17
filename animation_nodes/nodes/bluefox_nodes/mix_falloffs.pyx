import bpy
import numpy as np
from bpy.props import *
from ... base_types import AnimationNode
from .. falloff.constant_falloff import ConstantFalloff
from ... data_structures cimport CompoundFalloff, Falloff

mixTypeItems = [
    ("ADD", "Add", "", "NONE", 0),
    ("SUB", "Sub", "", "NONE", 4),
    ("MULTIPLY", "Multiply", "", "NONE", 1),
    ("OVERLAY", "Overlay", "", "NONE", 5),
    ("MAX", "Max", "", "NONE", 2),
    ("MIN", "Min", "", "NONE", 3)]

useFactorTypes = {"ADD"}

class MixFalloffsNodePlus(bpy.types.Node, AnimationNode):
    bl_idname = "an_MixFalloffsNodePlus"
    bl_label = "Mix Falloffs Plus"

    __annotations__ = {}

    __annotations__["mixType"] = EnumProperty(name = "Mix Type", items = mixTypeItems,
        default = "MAX", update = AnimationNode.refresh)

    __annotations__["mixFalloffList"] = BoolProperty(name = "Mix Falloff List", default = False,
        update = AnimationNode.refresh)

    def create(self):
        if self.mixFalloffList:
            self.newInput("Falloff List", "Falloffs", "falloffs")
        else:
            self.newInput("Falloff", "A", "a")
            self.newInput("Falloff", "B", "b")
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "mixType", text = "")
        row.prop(self, "mixFalloffList", text = "", icon = "LINENUMBERS_ON")

    def getExecutionFunctionName(self):
        if self.mixFalloffList:
            return "execute_List"
        else:
            return "execute_Two"

    def execute_List(self, falloffs):
        return MixFalloffs(falloffs, self.mixType, default = 1)

    def execute_Two(self, a, b):
        return MixFalloffs([a, b], self.mixType, default = 1)


class MixFalloffs:
    def __new__(cls, list falloffs not None, str method not None, double default = 1):
        if len(falloffs) == 0:
            return ConstantFalloff(default)
        elif len(falloffs) == 1:
            return falloffs[0]
        elif len(falloffs) == 2:
            if method == "ADD": return AddTwoFalloffs(*falloffs)
            elif method == "SUB": return SubTwoFalloffs(*falloffs)
            elif method == "MULTIPLY": return MultiplyTwoFalloffs(*falloffs)
            elif method == "OVERLAY": return OverlayTwoFalloffs(*falloffs)
            elif method == "MAX": return MaxTwoFalloffs(*falloffs)
            elif method == "MIN": return MinTwoFalloffs(*falloffs)
            raise Exception("invalid method")
        else:
            if method == "ADD": return AddFalloffs(falloffs)
            elif method == "SUB": return SubFalloffs(falloffs)
            elif method == "MULTIPLY": return MultiplyFalloffs(falloffs)
            elif method == "MAX": return MaxFalloffs(falloffs)
            elif method == "MIN": return MinFalloffs(falloffs)
            raise Exception("invalid method")


cdef class MixTwoFalloffsBase(CompoundFalloff):
    cdef:
        Falloff a, b

    def __cinit__(self, Falloff a, Falloff b):
        self.a = a
        self.b = b

    cdef list getDependencies(self):
        return [self.a, self.b]

cdef class AddTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] + dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] + b[i]

cdef class SubTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return np.clip((dependencyResults[0] - dependencyResults[1]), 0, 1)

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = np.clip((a[i] - b[i]),0,1)

cdef class OverlayTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[0] < 0.5:
            return np.clip((2*dependencyResults[0]*dependencyResults[1]),0,1)
        else:    
            return np.clip((1-2*(1-dependencyResults[0])*(1-dependencyResults[1])),0,1)

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if a[i]<0.5:
                target[i]=np.clip((2*a[i]*b[i]),0,1)
            else:    
                target[i] = np.clip((1-2*(1-a[0])*(1-b[1])),0,1)                        

cdef class MultiplyTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] * dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] * b[i]

cdef class MinTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return min(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = min(a[i], b[i])

cdef class MaxTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return max(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = max(a[i], b[i])


cdef class MixFalloffsBase(CompoundFalloff):
    cdef list falloffs
    cdef int amount

    def __init__(self, list falloffs not None):
        self.falloffs = falloffs
        self.amount = len(falloffs)
        if self.amount == 0:
            raise Exception("at least one falloff required")

    cdef list getDependencies(self):
        return self.falloffs

cdef class AddFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float sum = 0
        for i in range(self.amount):
            sum += dependencyResults[i]
        return sum

cdef class SubFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float sub = 0
        for i in range(self.amount):
            sub -= dependencyResults[i]
        return sub        

cdef class MultiplyFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float product = 1
        for i in range(self.amount):
            product *= dependencyResults[i]
        return product

cdef class MinFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float minValue = dependencyResults[0]
        for i in range(1, self.amount):
            if dependencyResults[i] < minValue:
                minValue = dependencyResults[i]
        return minValue

cdef class MaxFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float maxValue = dependencyResults[0]
        for i in range(1, self.amount):
            if dependencyResults[i] > maxValue:
                maxValue = dependencyResults[i]
        return maxValue
