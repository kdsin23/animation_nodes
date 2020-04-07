import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList, PolySpline

class Storevector(object):
    def __init__(self, spline):
        self.spline = PolySpline()

p = {}

class TracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_splinetracer"
    bl_label = "Spline Tracer"

    usevectorlist: VectorizedSocket.newProperty()
 
    def create(self):
        self.newInput(VectorizedSocket("Vector", "usevectorlist",
            ("Point ", "point"), ("Points", "points")))
        self.newInput("Integer", "Reset frame", "resetframe", value = 1, hide = True)
        self.newInput("Integer", "Start frame", "start", value = 1, minValue = 1)
        self.newInput("Integer", "End frame", "end", value = 200, minValue = 1)
        self.newInput("Float", "Radius", "radius", value = 0.1, minValue = 0)
        self.newInput("Float", "Tilt", "tilt")
        self.newInput("Integer", "Quality", "q", value = 1, minValue = 1, hide = True)

        self.newOutput(VectorizedSocket("Spline", "usevectorlist",
            ("Spline", "spline"), ("Splines", "splines")))

    def getExecutionFunctionName(self):
        if self.usevectorlist:
            return "execute_points"
        else:
            return "execute_point"

    def execute_points(self, points, resetframe, start, end, radius, tilt, q):
        T = bpy.context.scene.frame_current
        identifier = self.identifier
        if T == resetframe:
            p[identifier] = []

        p_object = p.get(identifier, [])
        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return splinelist

        for i, point in enumerate(points):
            p_object.append(Storevector(i))
            if T >= start and T <= end and T % q == 0 :
                p_object[i].spline.appendPoint(point, radius, tilt)
            splinelist.append(p_object[i].spline)
        p[identifier] = p_object
        return splinelist

    def execute_point(self, point, resetframe, start, end, radius, tilt, q):
        points = Vector3DList.fromValues([point])
        T = bpy.context.scene.frame_current
        identifier = self.identifier
        if T == resetframe:
            p[identifier] = []

        p_object = p.get(identifier, [])
        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return PolySpline()

        for i, point in enumerate(points):
            p_object.append(Storevector(i))
            if T >= start and T <= end and T % q == 0 :
                p_object[i].spline.appendPoint(point, radius, tilt)
            splinelist.append(p_object[i].spline)
        p[identifier] = p_object
        return splinelist[0] 