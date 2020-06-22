import bpy
import numpy as np
from bpy.props import *
from .. matrix.c_utils import*
from .. bluefox_nodes.c_utils import vector_lerp
from ... base_types import AnimationNode, VectorizedSocket
from ... events import propertyChanged, executionCodeChanged
from ... algorithms.rotations import directionsToMatrices, eulersToDirections
from ... data_structures import Vector3DList, VirtualVector3DList, VirtualEulerList, Matrix4x4List, DoubleList

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]
directionAxisItems = [(axis, axis, "", "", i)
                      for i, axis in enumerate(("X", "Y", "Z", "-X", "-Y", "-Z"))]

class TargetEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TargetEffector"
    bl_label = "Target Effector"
    bl_width_default = 150

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")
    directionAxis: EnumProperty(name = "Direction Axis", default = "Z",
        items = directionAxisItems, update = propertyChanged)

    useTargetList: VectorizedSocket.newProperty()

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useOffset: BoolProperty(update = checkedPropertiesChanged)
    useDirection: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)
    considerRotationsIn: BoolProperty(name = "Consider Incoming Rotations", default = False, update = propertyChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Matrix", "useTargetList",
            ("Target", "target"), ("Targets", "targets")))
        self.newInput("Float", "Distance", "distanceIn")
        self.newInput("Float", "Width", "width", value = 3.0)
        self.newInput("Float", "Strength", "offsetStrength", value = 1.0)
        self.newInput("Vector", "Scale", "scaleIn")
        self.newInput("Vector", "Guide", "guideIn", value = (0,0,1), hide = True)
        self.newInput("Falloff", "Falloff", "falloff")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)
        self.newOutput("Float List", "Falloff Strength", "falloffStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "useDirection", text = "Direction", toggle = True, icon = "CON_TRACKTO")
        row = col.row(align = True)
        row.prop(self, "useOffset", text = "Offset", toggle = True, icon = "TRANSFORM_ORIGINS")
        row.prop(self, "useScale", text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER")
        if self.useDirection:
            layout.prop(self, "trackAxis", expand = True)
            layout.prop(self, "guideAxis", expand = True)
            if self.trackAxis[-1:] == self.guideAxis[-1:]:
                layout.label(text = "Must be different", icon = "ERROR")

    def drawAdvanced(self, layout):
        layout.prop(self, "considerRotationsIn") 
        layout.prop(self, "directionAxis", expand = True)
            
    def updateSocketVisibility(self):
        condition = self.useOffset or self.useScale
        self.inputs[2].hide = not condition
        self.inputs[3].hide = not condition
        self.inputs[4].hide = not self.useOffset
        self.inputs[5].hide = not self.useScale

    def execute(self, matrices, targets, distanceIn, width, offsetStrength, scaleIn, guideIn, falloff):
        if not self.useTargetList: targets = [targets]
        count = len(matrices)
        if len(targets) == 0 or len(matrices) == 0:
            return Matrix4x4List(), DoubleList(), DoubleList()
        else:
            DefaultList = DoubleList(length = count)
            DefaultList.fill(0)
            if [self.useDirection, self.useOffset, self.useScale] == [0,0,0]:
                return matrices, DefaultList, DefaultList
            else:
                vectors = extractMatrixTranslations(matrices)
                rotations = extractMatrixRotations(matrices)
                scales = extractMatrixScales(matrices)
                Directions = eulersToDirections(rotations, self.directionAxis)
                vectorArray = vectors.asNumpyArray().reshape(count, 3)
                scalesArray = scales.asNumpyArray().reshape(count, 3)
                if self.useDirection:
                    targetDirections = np.zeros((count, 3), dtype='float32')
                    if self.considerRotationsIn:
                        targetDirections = Directions.asNumpyArray().reshape(count, 3)
                targetOffsets = vectors.asNumpyArray().reshape(count, 3)
                falloffEvaluator = self.getFalloffEvaluator(falloff)
                influences = DoubleList.fromValues(falloffEvaluator.evaluateList(vectors))
                influencesArray = influences.asNumpyArray()
                strength = 0
                for i, target in enumerate(targets):
                    flag = 1
                    center = target.to_translation()
                    scale = target.to_scale().x
                    if scale < 0:
                        flag = -1
                    size = abs(scale) + distanceIn
                    newPositions, distances = self.targetSphericalDistance(vectorArray, center, size-1, width, flag)
                    if self.useOffset:
                        targetOffsets[:,0] += newPositions[:,0] * offsetStrength * influencesArray
                        targetOffsets[:,1] += newPositions[:,1] * offsetStrength * influencesArray
                        targetOffsets[:,2] += newPositions[:,2] * offsetStrength * influencesArray
                    if self.useDirection:
                        targetDirections += self.targetRotation(targetOffsets, center, flag)
                    if self.useScale:
                        scalesArray[:,0] += scaleIn.x * distances * influencesArray
                        scalesArray[:,1] += scaleIn.y * distances * influencesArray
                        scalesArray[:,2] += scaleIn.z * distances * influencesArray
                    if i == 0:
                        strength = distances
                    else:    
                        strength += distances
                newVectors = vectors
                newRotations = rotations
                newScales = scales
                if self.useOffset:
                    newVectors = Vector3DList.fromNumpyArray(targetOffsets.astype('float32').flatten())
                if self.useDirection:
                    newDirections = Vector3DList.fromNumpyArray(targetDirections.astype('float32').flatten())
                    newDirections = vector_lerp(Directions, newDirections, influences)
                    newDirections.normalize()
                    newRotations = directionsToMatrices(newDirections, guideIn, self.trackAxis, self.guideAxis).toEulers(isNormalized = True)
                if self.useScale:
                    newScales = Vector3DList.fromNumpyArray(scalesArray.astype('float32').flatten())
                _v = VirtualVector3DList.create(newVectors, (0, 0, 0))    
                _r = VirtualEulerList.create(newRotations, (0, 0, 0))
                _s = VirtualVector3DList.create(newScales, (1, 1, 1))
                return composeMatrices(count, _v, _r, _s), DoubleList.fromNumpyArray(np.clip(strength, 0, 1).astype('double')), influences 

    def targetRotation(self, vectors, target, flag):
        temp = vectors - np.asarray(target)
        vectorLength = np.sqrt(temp[:,0] * temp[:,0] + temp[:,1] * temp[:,1] + temp[:,2] * temp[:,2])
        vectorLength[vectorLength == 0] = 0.00001
        reshapedLength = np.repeat(vectorLength, 3).reshape(-1, 3)
        return temp / (reshapedLength * reshapedLength) * flag

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
        distance = np.clip(distance,-1,1)
        temp = (vectors - np.asarray(target)) * flag
        temp[:,0] *= distance
        temp[:,1] *= distance
        temp[:,2] *= distance
        return temp, distance

    def distanceVectors(self, a, b):
        diff1 = a.x - b[:,0]
        diff2 = a.y - b[:,1]
        diff3 = a.z - b[:,2]
        return np.sqrt(diff1 * diff1 + diff2 * diff2 + diff3 * diff3)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")    
