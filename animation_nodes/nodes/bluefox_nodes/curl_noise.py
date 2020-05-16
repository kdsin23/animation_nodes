import bpy
from bpy.props import *
from ... events import propertyChanged
from . c_utils import CurlEulerIntegrate
from ... base_types import AnimationNode

noiseTypesData = [
    ("SIMPLEX", "Simplex", "", "Simplex", 0),
    ("PERLIN", "Perlin", "", "Perlin", 1),
    ("VALUE", "Value", "", "Value", 2),
    ("CUBIC", "Cubic", "", "Cubic", 3),
    ("CELLULAR", "Cellular", "", "Cellular", 4)
]
fractalTypesData = [
    ("FBM", "FBM", "", "", 0),
    ("BILLOW", "Billow", "", "", 1),
    ("RIGID_MULTI", "Rigid Multi", "", "", 2)
]
perturbTypesData = [
    ("NONE", "None", "", "", 0),
    ("GRADIENT", "Gradient", "", "", 1),
    ("GRADIENT_FRACTAL", "Gradient Fractal", "", "", 2),
    ("NORMALISE", "Normalise", "", "", 3),
    ("GRADIENT_NORMALISE", "Gradient Normalise", "", "", 4),
    ("GRADIENT_FRACTAL_NORMALISE", "Gradient Fractal Normalise", "", "", 5)
]

class CurlNoiseNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_CurlNoise"
    bl_label = "Curl Noise"

    noiseType : EnumProperty(name = "Mode", default = "SIMPLEX",
        items = noiseTypesData, update = AnimationNode.refresh)
    fractalType : EnumProperty(name = "Fractal Type", default = "FBM",
        items = fractalTypesData, update = AnimationNode.refresh)    
    perturbType : EnumProperty(name = "Perturb Type", default = "NONE",
        items = perturbTypesData, update = AnimationNode.refresh)    

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors")
        self.newInput("Integer", "Iteration", "iteration", minValue = 0)
        self.newInput("Boolean", "Normalize", "normalize")
        self.newInput("Float", "Epsilon", "epsilon", value = 0.1)
        self.newInput("Integer", "Seed", "seed")
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.3)
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 10)
        self.newInput("Vector", "Scale", "scale", value = (0.5,0.5,0.5))
        self.newInput("Vector", "Offset", "offset", hide = True)
        self.newOutput("Vector List", "Vectors", "vectorsOut")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")

    def drawAdvanced(self, layout):
        layout.prop(self, "fractalType")
        layout.prop(self, "perturbType")

    def getExecutionCode(self, required):
            yield "vectorsOut = self.executeCurl(vectors, iteration, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset)"            

    def executeCurl(self, vectors, iteration, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset):
        return CurlEulerIntegrate(vectors, self.noiseType, self.fractalType, self.perturbType, epsilon, 
                        seed, octaves, amplitude, frequency, scale, offset, normalize, iteration)
