import bpy
from .. data_structures import NDArray
from . implicit_conversion import registerImplicitConversion
from .. base_types import AnimationNodeSocket, PythonListSocket

class NDArraySocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_NDArraySocket"
    bl_label = "NDArray Socket"
    dataType = "NDArray"
    drawColor = (0.3, 0.8, 0.6, 1)
    storable = False
    comparable = True

    @classmethod
    def getDefaultValue(cls):
        return NDArray.array(0)

    @classmethod
    def correctValue(cls, value):
        if isinstance(value, NDArray.ndarray) or value is None:
            return value, 0
        return cls.getDefaultValue(), 2

registerImplicitConversion("Float", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Integer", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Vector", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Euler", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Quaternion", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Color", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Matrix", "NDArray", "NDArray.array(value)")

class NDArrayListSocket(bpy.types.NodeSocket, PythonListSocket):
    bl_idname = "an_NDArrayListSocket"
    bl_label = "NDArray List Socket"
    dataType = "NDArray List"
    baseType = NDArraySocket
    drawColor = (0.3, 0.8, 0.6, 0.5)
    storable = False
    comparable = False

    @classmethod
    def getCopyExpression(cls):
        return "value[:]"
