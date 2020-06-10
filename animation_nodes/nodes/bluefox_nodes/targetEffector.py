import bpy
import numpy as np
from bpy.props import *
from mathutils import Vector 
from .. matrix.c_utils import*
from ... math import scaleVector3DList
from ... events import propertyChanged
from ... utils.depsgraph import getEvaluatedID
from ... algorithms.rotations import directionsToMatrices
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList, VirtualVector3DList, VirtualEulerList, Matrix4x4List, DoubleList

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

class TargetEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TargetEffector"
    bl_label = "Target Effector"

    enableRotation = BoolProperty(name = "Enable Rotation", default = False, update = propertyChanged)

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    useObjectList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects"),
            codeProperties = dict(allowListExtension = False)))
        self.newInput("Float", "Offset", "offset")
        self.newInput("Float", "Width", "width", value = 3.0)
        self.newInput("Falloff", "Falloff", "falloff")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)

    def draw(self, layout):
        layout.prop(self, "enableRotation")
        if self.enableRotation:
            layout.prop(self, "trackAxis", expand = True)
            layout.prop(self, "guideAxis", expand = True)
            if self.trackAxis[-1:] == self.guideAxis[-1:]:
                layout.label(text = "Must be different", icon = "ERROR")

    def execute(self, matrices, objects, offset, width, falloff):
        if not self.useObjectList: objects = [objects]
        if len(objects) == 0 or len(matrices) == 0:
            return Matrix4x4List(), DoubleList()
        else:
            vectors = extractMatrixTranslations(matrices)
            rotations = extractMatrixRotations(matrices)
            scales = extractMatrixScales(matrices)
            count = len(matrices)
            vectorArray = vectors.asNumpyArray().reshape(count, 3)
            if self.enableRotation:
                targetDirections = np.zeros((count, 3), dtype='float32')
            targetOffsets = vectors.asNumpyArray().reshape(count, 3)
            falloffEvaluator = self.getFalloffEvaluator(falloff)
            influences = falloffEvaluator.evaluateList(vectors).asNumpyArray()
            influencesReshaped = np.repeat(influences, 3).reshape(-1, 3)
            strength = 0
            for i, object in enumerate(objects):
                if object is not None:
                    flag = 1
                    evaluatedObject = getEvaluatedID(object)
                    target = evaluatedObject.matrix_world
                    center = target.to_translation()
                    scale = target.to_scale().x
                    if scale < 0:
                        flag = -1
                    size = abs(scale) + offset
                    t, s = self.targetOffset(vectorArray, center, size-1, width, flag)
                    targetOffsets += t * influencesReshaped
                    if self.enableRotation:
                        targetDirections += self.targetRotation(targetOffsets, center, flag)
                    if i == 0:
                        strength = s    
                    else:    
                        strength += s
            newVectors = Vector3DList.fromNumpyArray(targetOffsets.astype('float32').flatten())
            _v = VirtualVector3DList.create(newVectors, (0, 0, 0))
            _r = VirtualEulerList.create(rotations, (0, 0, 0))
            if self.enableRotation:
                newRotations = directionsToMatrices(Vector3DList.fromNumpyArray(targetDirections.astype('float32').flatten()), Vector((0,0,1)), 
                                self.trackAxis, self.guideAxis).toEulers(isNormalized = True)  
                _r = VirtualEulerList.create(newRotations, (0, 0, 0))
            _s = VirtualVector3DList.create(scales, (1, 1, 1))
            return composeMatrices(count, _v, _r, _s), DoubleList.fromNumpyArray(np.clip(strength, 0, 1).astype('double'))

    def targetRotation(self, vectors, target, flag):
        temp = vectors - np.asarray(target)
        vectorLength = np.sqrt(temp[:,0]*temp[:,0] + temp[:,1]*temp[:,1] + temp[:,2]*temp[:,2])
        vectorLength[vectorLength == 0] = 0.00001
        reshapedLength = np.repeat(vectorLength, 3).reshape(-1, 3)
        return temp/(reshapedLength * reshapedLength) * flag

    def targetOffset(self, vectors, target, size, width, flag):
        if width < 0:
            size += width
            width = -width
        minDistance = size
        maxDistance = size + width
        if minDistance == maxDistance:
            minDistance -= 0.00001
        factor = 1 / (maxDistance - minDistance)
        distance = self.distanceVectors(target, vectors)
        distance[distance <= minDistance] = 1
        distance[distance <= maxDistance] = 1 - (distance[distance <= maxDistance] - minDistance) * factor
        distance[distance > maxDistance] = 0
        distance[distance > minDistance] = 0
        temp = (vectors - np.asarray(target)) * flag
        distanceReshaped = np.repeat(np.clip(distance, 0, 1), 3).reshape(-1, 3)
        result = temp * distanceReshaped
        return result, distance

    def distanceVectors(self, a, b):
        diff1 = a.x - b[:,0]
        diff2 = a.y - b[:,1]
        diff3 = a.z - b[:,2]
        return np.sqrt(diff1 * diff1 + diff2 * diff2 + diff3 * diff3)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")    
