import bpy
from mathutils import noise
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList

vectorTurbulanceModeItems = [
    ("PERLIN_ORIGINAL", "Perlin Orginal", "", "", 0),
    ("PERLIN_NEW", "Perlin New", "", "", 1),
    ("VORONOI_F1", "Voronoi F1", "", "", 2),
    ("VORONOI_F2", "Voronoi F2", "", "", 3),
    ("VORONOI_F3", "Voronoi F3", "", "", 4),
    ("VORONOI_F4", "Voronoi F4", "", "", 5),
    ("VORONOI_F2F1", "Voronoi F2F1", "", "", 6),
    ("VORONOI_CRACKLE", "Voronoi Crackle", "", "", 7),
    ("CELLNOISE", "Cell Noise", "", "", 8)
]

class BLVectorTurbulanceNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_BLVectorTurbulance"
    bl_label = "BL Vector Turbulance"
    bl_width_default = 160

    __annotations__ = {}

    __annotations__["noisetype"] = EnumProperty(name = "Noise ", default = "PERLIN_ORIGINAL",
        items = vectorTurbulanceModeItems, update = AnimationNode.refresh)

    useVectorList: VectorizedSocket.newProperty()    

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Vector", "vectorIn"), ("Vectors", "vectorsIn")))
        self.newInput("Integer", "Seed", "seed", minValue = 1)    
        self.newInput("Integer", "Octaves", "octaves", value = 2, minValue = 1)
        self.newInput("Boolean", "Hard", "hard", value = 0)
        self.newInput("Float", "Amplitude", "amplitude", value = 0.5)
        self.newInput("Float", "Frequency", "frequency", value = 2.5)
    
        self.newOutput(VectorizedSocket("Vector", ["useVectorList"],
            ("Noise", "noise_out"), ("Noise", "noises_out")))
    
    def draw(self, layout):
        layout.prop(self, "noisetype")

    def getExecutionFunctionName(self):
        if self.useVectorList:
            return "execute_turbulanceList"
        else:
            return "execute_turbulance"

    def execute_turbulance(self, vectorIn, seed, octaves, hard, amplitude, frequency):
        noiseName = self.noisetype 
        noise.seed_set(seed)   
        return noise.turbulence_vector(vectorIn, octaves, hard, noise_basis=noiseName, amplitude_scale=amplitude, frequency_scale=frequency)

    def execute_turbulanceList(self, vectorsIn, seed, octaves, hard, amplitude, frequency):
        noiseName = self.noisetype
        vectors_out = Vector3DList()
        noise.seed_set(seed)
        for vectorIn in vectorsIn:
            vectors_out.append(noise.turbulence_vector(vectorIn, octaves, hard, noise_basis=noiseName, amplitude_scale=amplitude, frequency_scale=frequency))
        return vectors_out         


