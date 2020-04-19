import bpy
from mathutils import noise
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket

distanceMetricItems = [
    ("DISTANCE", "Distance", "", "", 0),
    ("DISTANCE_SQUARED", "Distance Squared", "", "", 1),
    ("MANHATTAN", "Manhattan", "", "", 2),
    ("CHEBYCHEV", "Chebychev", "", "", 3),
    ("MINKOVSKY", "Minkovsky", "", "", 4),
    ("MINKOVSKY_HALF", "Minkovsky Half", "", "", 5),
    ("MINKOVSKY_FOUR", "Minkovsky Four", "", "", 6)
]

class BLVoronoiNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_BLVoronoi"
    bl_label = "BL Voronoi"
    bl_width_default = 160

    __annotations__ = {}

    __annotations__["metrictype"] = EnumProperty(name = "Distance Metric ", default = "DISTANCE",
        items = distanceMetricItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector", "Position", "position")
        self.newInput("Float", "Exponent", "exponent", value = 2.5)

        self.newOutput("Float", "Distance 1","distance1")
        self.newOutput("Float", "Distance 2","distance2")
        self.newOutput("Float", "Distance 3","distance3")
        self.newOutput("Float", "Distance 4","distance4")
        self.newOutput("Vector", "Point 1","point1")
        self.newOutput("Vector", "Point 2","point2")
        self.newOutput("Vector", "Point 3","point3")
        self.newOutput("Vector", "Point 4","point4")

    def draw(self, layout):
        layout.prop(self, "metrictype")

    def execute(self,position, exponent):
        metrictype = self.metrictype
        out = noise.voronoi(position, distance_metric=metrictype, exponent=exponent)
        distances = out[0]
        points = out[1]
        return distances[0],distances[1],distances[2],distances[3],points[0],points[1],points[2],points[3]

  


