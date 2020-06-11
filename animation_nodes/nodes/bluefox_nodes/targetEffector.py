import bpy
import numpy as np
from bpy.props import *
from mathutils import Vector 
from .. matrix.c_utils import*
from ... math import scaleVector3DList
from ... utils.depsgraph import getEvaluatedID
from ... algorithms.rotations import directionsToMatrices
from ... base_types import AnimationNode, VectorizedSocket
from ... events import propertyChanged, executionCodeChanged
from ... data_structures import Vector3DList, VirtualVector3DList, VirtualEulerList, Matrix4x4List, DoubleList

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

class TargetEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TargetEffector"
    bl_label = "Target Effector"

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    useTargetList: VectorizedSocket.newProperty()

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useLocation: BoolProperty(update = checkedPropertiesChanged)
    useRotation: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Matrix", "useTargetList",
            ("Target", "target"), ("Targets", "targets")))
        self.newInput("Float", "Offset", "offset")
        self.newInput("Float", "Width", "width", value = 3.0)
        self.newInput("Vector", "Scale", "scaleIn")
        self.newInput("Falloff", "Falloff", "falloff")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "useRotation", index = 1, text = "Rot", toggle = True, icon = "CON_TRACKTO") 
        subrow.prop(self, "useLocation", index = 0, text = "Loc", toggle = True, icon = "TRANSFORM_ORIGINS")
        subrow.prop(self, "useScale", index = 2, text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER") 
        if self.useRotation:
            layout.prop(self, "trackAxis", expand = True)
            layout.prop(self, "guideAxis", expand = True)
            if self.trackAxis[-1:] == self.guideAxis[-1:]:
                layout.label(text = "Must be different", icon = "ERROR")

    def updateSocketVisibility(self):
        self.inputs[2].hide = not self.useLocation
        self.inputs[3].hide = not self.useLocation
        self.inputs[4].hide = not self.useScale

    def execute(self, matrices, targets, offset, width, scaleIn, falloff):
        if not self.useTargetList: targets = [targets]
        if len(targets) == 0 or len(matrices) == 0:
            return Matrix4x4List(), DoubleList()
        else:
            if [self.useRotation, self.useLocation, self.useScale] == [0,0,0]:
                return matrices, DoubleList()
            else:    
                vectors = extractMatrixTranslations(matrices)
                rotations = extractMatrixRotations(matrices)
                scales = extractMatrixScales(matrices)
                count = len(matrices)
                vectorArray = vectors.asNumpyArray().reshape(count, 3)
                if self.useRotation:
                    targetDirections = np.zeros((count, 3), dtype='float32')
                targetOffsets = vectors.asNumpyArray().reshape(count, 3)
                falloffEvaluator = self.getFalloffEvaluator(falloff)
                influences = falloffEvaluator.evaluateList(vectors).asNumpyArray()
                influencesReshaped = np.repeat(influences, 3).reshape(-1, 3)
                strength = 0
                for i, target in enumerate(targets):
                    flag = 1
                    center = target.to_translation()
                    scale = target.to_scale().x
                    if scale < 0:
                        flag = -1
                    size = abs(scale) + offset
                    t, s = self.targetSphericalDistance(vectorArray, center, size-1, width, flag)
                    if self.useLocation:
                        targetOffsets += t * influencesReshaped
                    if self.useRotation:
                        targetDirections += self.targetRotation(targetOffsets, center, flag)
                    if i == 0:
                        strength = s[:,0]    
                    else:    
                        strength += s[:,0]
                _v = VirtualVector3DList.create(vectors, (0, 0, 0))
                if self.useLocation:               
                    newVectors = Vector3DList.fromNumpyArray(targetOffsets.astype('float32').flatten())
                    _v = VirtualVector3DList.create(newVectors, (0, 0, 0))
                _r = VirtualEulerList.create(rotations, (0, 0, 0))
                if self.useRotation:
                    newRotations = directionsToMatrices(Vector3DList.fromNumpyArray(targetDirections.astype('float32').flatten()), Vector((0,0,1)), 
                                    self.trackAxis, self.guideAxis).toEulers(isNormalized = True)  
                    _r = VirtualEulerList.create(newRotations, (0, 0, 0))    
                _s = VirtualVector3DList.create(scales, (1, 1, 1))
                if self.useScale:
                    newScales = scales.asNumpyArray().reshape(count, 3)
                    newScales += np.asarray(scaleIn) * influencesReshaped * s
                    _s = VirtualVector3DList.create(Vector3DList.fromNumpyArray(newScales.astype('float32').flatten()), (1, 1, 1))
                return composeMatrices(count, _v, _r, _s), DoubleList.fromNumpyArray(np.clip(strength, 0, 1).astype('double'))

    def targetRotation(self, vectors, target, flag):
        temp = vectors - np.asarray(target)
        vectorLength = np.sqrt(temp[:,0]*temp[:,0] + temp[:,1]*temp[:,1] + temp[:,2]*temp[:,2])
        vectorLength[vectorLength == 0] = 0.00001
        reshapedLength = np.repeat(vectorLength, 3).reshape(-1, 3)
        return temp/(reshapedLength * reshapedLength) * flag

    def targetSphericalDistance(self, vectors, target, size, width, flag):
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
        return result, distanceReshaped

    def distanceVectors(self, a, b):
        diff1 = a.x - b[:,0]
        diff2 = a.y - b[:,1]
        diff3 = a.z - b[:,2]
        return np.sqrt(diff1 * diff1 + diff2 * diff2 + diff3 * diff3)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")    
