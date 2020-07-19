import bpy
from bpy.props import *
from ... base_types import AnimationNode
from ... algorithms.interpolations import Linear
from .. falloff . mix_falloffs import MixFalloffs
from .. bluefox_nodes.c_utils import offsetMatrices
from .. falloff . custom_falloff import CustomFalloff
from ... events import propertyChanged, executionCodeChanged
from .. falloff . interpolate_falloff import InterpolateFalloff
from ... data_structures import Matrix4x4List, DoubleList, Vector3DList, EulerList, FloatList
from ... nodes.number.c_utils import range_DoubleList_StartStop, mapRange_DoubleList_Interpolated

class StepEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_StepEffector"
    bl_label = "Step Effector"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useLocation: BoolProperty(update = checkedPropertiesChanged)
    useRotation: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput("Vector", "Location", "location")
        self.newInput("Euler", "Rotation", "rotation")
        self.newInput("Vector", "Scale", "scale")
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Boolean", "Clamp", "clamp", value = 0, hide = True)
        self.newInput("Float", "Min", "minValue", value = 0, hide = True)
        self.newInput("Float", "Max", "maxValue", value = 1, hide = True)
        self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)
        self.newOutput("Float List", "Falloff Strength", "falloffStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "useLocation", index = 0, text = "Loc", toggle = True, icon = "EXPORT")
        subrow.prop(self, "useRotation", index = 1, text = "Rot", toggle = True, icon = "FILE_REFRESH") 
        subrow.prop(self, "useScale", index = 2, text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER") 

    def updateSocketVisibility(self):
        self.inputs[1].hide = not self.useLocation
        self.inputs[2].hide = not self.useRotation
        self.inputs[3].hide = not self.useScale
              
    def execute(self, matrices, location, rotation, scale, falloff, clamp, minValue, maxValue, interpolation):
        if matrices is None:
            return Matrix4x4List()   
        else:
            falloff_strengths, effector_strengths = self.calculateStrengths(falloff, matrices, clamp, interpolation, minValue, maxValue)
            if not self.useLocation:
                location = [0,0,0]
            if not self.useRotation:
                rotation = [0,0,0]
            if not self.useScale:
                scale = [0,0,0]         
            v = Vector3DList.fromValue(location)
            e = EulerList.fromValue(rotation)
            s = Vector3DList.fromValue(scale)
            newMatrices =  offsetMatrices(matrices, v, e, s, effector_strengths)
            return newMatrices, effector_strengths, falloff_strengths

    def calculateStrengths(self, falloff, matrices, clamp, interpolation, minValue, maxValue):
        strengths = range_DoubleList_StartStop(len(matrices), 0.00, 1.00)
        interpolatedStrengths = mapRange_DoubleList_Interpolated(strengths, interpolation, 0, 1, minValue, maxValue)
        mixedFalloff = MixFalloffs([falloff, CustomFalloff(FloatList.fromValues(interpolatedStrengths), 0)], "MULTIPLY", default = 1)
        if clamp:
            mixedFalloff = InterpolateFalloff(mixedFalloff, Linear())
        falloffEvaluator = self.getFalloffEvaluator(falloff)    
        strengthEvaluator = self.getFalloffEvaluator(mixedFalloff)
        falloff_strengths = DoubleList.fromValues(falloffEvaluator.evaluateList(matrices)) 
        effector_strengths = DoubleList.fromValues(strengthEvaluator.evaluateList(matrices))
        return falloff_strengths, effector_strengths

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("TRANSFORMATION_MATRIX")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for matrices")          
    