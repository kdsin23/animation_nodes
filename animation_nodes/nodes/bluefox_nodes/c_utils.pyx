from ... data_structures cimport (
    DoubleList, FloatList,
    Vector3DList, EulerList, Matrix4x4List,
    VirtualVector3DList, VirtualEulerList, VirtualFloatList,
    Action, ActionEvaluator, PathIndexActionChannel,
    BoundedAction, BoundedActionEvaluator,Color,
    ColorList
)

from ... math cimport (
    Vector3, Euler3, Matrix4, toMatrix4,
    multMatrix4, toPyMatrix4,
    invertOrthogonalTransformation,
    setTranslationRotationScaleMatrix,
    setRotationXMatrix, setRotationYMatrix, setRotationZMatrix,
    setRotationMatrix, setTranslationMatrix, setIdentityMatrix,
    setScaleMatrix,
    setMatrixTranslation,
    transposeMatrix_Inplace)

from mathutils import Matrix
from math import *
from ... math import matrix4x4ListToEulerList
from ... math cimport (add, subtract, multiply, divide_Save, modulo_Save,
                       sin, cos, tan, asin_Save, acos_Save, atan, atan2, hypot,
                       power_Save, floor, ceil, sqrt_Save, invert, reciprocal_Save,
                       snap_Save, copySign, floorDivision_Save, logarithm_Save)

from libc.math cimport sqrt
from libc.math cimport M_PI as PI

def matrixlerp(Matrix4x4List matricesA, Matrix4x4List matricesB, DoubleList influences):
    cdef Matrix4x4List out_matrixlist = Matrix4x4List(length = len(matricesA))

    for i, item in enumerate( matricesA ):
        out_matrixlist[i]= item . lerp( matricesB[i], influences[i] )     
    return out_matrixlist

def vectorlerp(Vector3DList vectorsA, Vector3DList vectorsB, DoubleList influences):
    cdef Vector3DList out_vectorlist = Vector3DList(length = len(vectorsA))

    for i, item in enumerate(vectorsA):
        out_vectorlist[i]= item . lerp( vectorsB[i], influences[i] )     
    return out_vectorlist 

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
