import cython
from ... data_structures cimport (
    DoubleList, FloatList,VirtualMatrix4x4List,
    Vector3DList, EulerList, Matrix4x4List,
    VirtualVector3DList, VirtualEulerList, VirtualFloatList, VirtualDoubleList,
    Action, ActionEvaluator, PathIndexActionChannel,
    BoundedAction, BoundedActionEvaluator,Color,
    ColorList
)

from ... math cimport (
    Vector3, Euler3, Matrix4, toMatrix4,toVector3,
    multMatrix4, toPyMatrix4,
    invertOrthogonalTransformation,
    setTranslationRotationScaleMatrix,
    setRotationXMatrix, setRotationYMatrix, setRotationZMatrix,
    setRotationMatrix, setTranslationMatrix, setIdentityMatrix,
    setScaleMatrix,
    setMatrixTranslation,
    transposeMatrix_Inplace)
from..matrix.c_utils import* 
from mathutils import Matrix, Euler
from math import *
from ... math import matrix4x4ListToEulerList
from ... math cimport (add, subtract, multiply, divide_Save, modulo_Save,
                       sin, cos, tan, asin_Save, acos_Save, atan, atan2, hypot,
                       power_Save, floor, ceil, sqrt_Save, invert, reciprocal_Save,
                       snap_Save, copySign, floorDivision_Save, logarithm_Save)

from libc.math cimport sqrt
from libc.math cimport M_PI as PI

def matrixlerp(Matrix4x4List matricesA, Matrix4x4List matricesB, DoubleList influences):
    cdef Py_ssize_t count = max(matricesA.getLength(),matricesB.getLength())
    cdef Py_ssize_t i
    cdef Matrix4x4List out_matrixlist = Matrix4x4List(length = count)
    cdef VirtualMatrix4x4List matrixlistA = VirtualMatrix4x4List.create(matricesA, Matrix.Identity(4))
    cdef VirtualMatrix4x4List matrixlistB = VirtualMatrix4x4List.create(matricesB, Matrix.Identity(4))
    cdef VirtualDoubleList influencess = VirtualDoubleList.create(influences, 0)

    for i in range(count):
        out_matrixlist[i]= matrixlistA[i] . lerp( matrixlistB[i], influencess[i] )  
    return out_matrixlist
 
def getTextureColors_moded(texture, Vector3DList locations, float multiplier):
    cdef long amount = locations.length
    cdef DoubleList reds = DoubleList(length = amount)
    cdef DoubleList greens = DoubleList(length = amount)
    cdef DoubleList blues = DoubleList(length = amount)
    cdef DoubleList alphas = DoubleList(length = amount)
    cdef ColorList colors = ColorList(length = amount)
    cdef float r, g, b, a

    for i in range(amount):
        r, g, b, a = texture.evaluate(locations[i])
        reds.data[i] = r*multiplier
        greens.data[i] = g*multiplier
        blues.data[i] = b*multiplier
        alphas.data[i] = a*multiplier
        colors.data[i] = Color(r, g, b, a)
    return colors, reds, greens, blues, alphas

def getTexturegreys(texture, Vector3DList locations, float multiplier):
    cdef long amount = locations.length
    cdef DoubleList greys = DoubleList(length = amount)
    cdef float r, g, b, a

    for i in range(amount):
        r, g, b, a = texture.evaluate(locations[i])
        greys.data[i] = ((r+g+b)/3)*multiplier
    return greys 
      
def matrix_lerp(Matrix4x4List mA, Matrix4x4List mB, DoubleList influences):
    cdef Vector3DList tA = extractMatrixTranslations(mA)
    cdef Vector3DList tB = extractMatrixTranslations(mB)
    cdef EulerList rA = extractMatrixRotations(mA)
    cdef EulerList rB = extractMatrixRotations(mB)
    cdef Vector3DList sA = extractMatrixScales(mA)
    cdef Vector3DList sB = extractMatrixScales(mB)
    cdef int count = max(mA.getLength(), mB.getLength())
    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))
    for i in range(count):
        translations_out.get(i).x = tA.data[i].x * (1-influences.data[i]) + tB.data[i].x * influences.data[i]
        translations_out.get(i).y = tA.data[i].y * (1-influences.data[i]) + tB.data[i].y * influences.data[i]
        translations_out.get(i).z = tA.data[i].z * (1-influences.data[i]) + tB.data[i].z * influences.data[i]
        rotations_out.get(i).x = rA.data[i].x * (1-influences.data[i]) + rB.data[i].x * influences.data[i]
        rotations_out.get(i).y = rA.data[i].y * (1-influences.data[i]) + rB.data[i].y * influences.data[i]
        rotations_out.get(i).z = rA.data[i].z * (1-influences.data[i]) + rB.data[i].z * influences.data[i]
        scales_out.get(i).x = sA.data[i].x * (1-influences.data[i]) + sB.data[i].x * influences.data[i]
        scales_out.get(i).y = sA.data[i].y * (1-influences.data[i]) + sB.data[i].y * influences.data[i]
        scales_out.get(i).z = sA.data[i].z * (1-influences.data[i]) + sB.data[i].z * influences.data[i]      
    return composeMatrices(count, translations_out, rotations_out, scales_out)

def vector_lerp(Vector3DList vectorsA, Vector3DList vectorsB, DoubleList influences):
    print(dir(VirtualVector3DList))
    cdef Py_ssize_t count = max(vectorsA.getLength(), vectorsB.getLength())
    cdef Py_ssize_t i
    cdef Vector3DList out_vectorlist = Vector3DList(length = count)
    for i in range(count):
        out_vectorlist.data[i].x = vectorsA.data[i].x * (1-influences.data[i]) + vectorsB.data[i].x * influences.data[i]
        out_vectorlist.data[i].y = vectorsA.data[i].y * (1-influences.data[i]) + vectorsB.data[i].y * influences.data[i]
        out_vectorlist.data[i].z = vectorsA.data[i].z * (1-influences.data[i]) + vectorsB.data[i].z * influences.data[i]
    return out_vectorlist
