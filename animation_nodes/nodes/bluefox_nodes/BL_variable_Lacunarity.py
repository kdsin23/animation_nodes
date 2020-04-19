import bpy
from mathutils import noise
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import DoubleList

vectorLacunarityModeItems1 = [
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

vectorLacunarityModeItems2 = [
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

class BLVariableLacunarityNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_BLVariableLacunarity"
    bl_label = "BL Variable Lacunarity"
    bl_width_default = 160

    __annotations__ = {}

    __annotations__["noisetype1"] = EnumProperty(name = "Type 1 ", default = "PERLIN_ORIGINAL",
        items = vectorLacunarityModeItems1, update = AnimationNode.refresh)
    __annotations__["noisetype2"] = EnumProperty(name = "Type 2 ", default = "PERLIN_ORIGINAL",
        items = vectorLacunarityModeItems2, update = AnimationNode.refresh)    

    useVectorList: VectorizedSocket.newProperty()    

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Vector", "vectorIn"), ("Vectors", "vectorsIn")))    
        self.newInput("Float", "Distortion", "distortion")

        self.newOutput(VectorizedSocket("Float", ["useVectorList"],
            ("Noise", "noise_out"), ("Noise", "noises_out")))
    
    def draw(self, layout):
        layout.prop(self, "noisetype1")
        layout.prop(self, "noisetype2")

    def getExecutionFunctionName(self):
        if self.useVectorList:
            return "execute_turbulanceList"
        else:
            return "execute_turbulance"

    def execute_turbulance(self, vectorIn, distortion):
        noisetype1 = self.noisetype1
        noisetype2 = self.noisetype2   
        return noise.variable_lacunarity(vectorIn, distortion, noise_type1=noisetype1, noise_type2=noisetype2)

    def execute_turbulanceList(self, vectorsIn, distortion):
        noisetype1 = self.noisetype1
        noisetype2 = self.noisetype2
        return DoubleList.fromValues([noise.variable_lacunarity(vectorIn, distortion, noise_type1=noisetype1, noise_type2=noisetype2) for vectorIn in vectorsIn])        


