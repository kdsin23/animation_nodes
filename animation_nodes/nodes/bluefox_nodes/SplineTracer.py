import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList, PolySpline, BezierSpline

pointTypeItems = [
    ("POINT", "Poly", "Add a normal point to the spline", "NONE", 0),
    ("BEZIER_POINT", "Bezier", "Add a point with handles", "NONE", 1)]

class StoreSpline(object):
    def __init__(self, spline):
        self.polyspline = PolySpline()
        self.bezierspline = BezierSpline()

p = {}

class TracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_splinetracer"
    bl_label = "Spline Tracer"

    pointType: EnumProperty(name = "Point Type", default = "POINT",
        items = pointTypeItems, update = AnimationNode.refresh)

    usevectorlist: VectorizedSocket.newProperty()
 
    def create(self):
        self.newInput(VectorizedSocket("Vector", "usevectorlist",
            ("Point ", "point"), ("Points", "points")))   
        self.newInput("Integer", "Reset frame", "resetframe", value = 1, hide = True)
        self.newInput("Integer", "Start frame", "start", value = 1, minValue = 1)
        self.newInput("Integer", "End frame", "end", value = 200, minValue = 1)
        self.newInput("Float", "Radius", "radius", value = 0.1, minValue = 0)
        self.newInput("Float", "Tilt", "tilt")
        if self.pointType == "BEZIER_POINT":
            self.newInput("Float", "Smoothness", "smoothness", value = 0.33) 
        self.newInput("Integer", "Reduce Quality", "q", value = 1, minValue = 1, hide = True)
        self.newInput("Boolean", "Use Custom Identifier", "useCustomIdentifier", value = 0, hide = True)
        self.newInput("Text", "Custom Identifier", "customIdentifier", value = "abcd", hide = True)

        self.newOutput(VectorizedSocket("Spline", "usevectorlist",
            ("Spline", "spline"), ("Splines", "splines")))

    def draw(self, layout):
        layout.prop(self, "pointType", text = "")

    def getExecutionFunctionName(self):
        if self.usevectorlist and self.pointType == "BEZIER_POINT":
            return "execute_beziersplines"
        elif self.usevectorlist and self.pointType != "BEZIER_POINT":
            return "execute_polysplines"    
        elif self.usevectorlist == False and self.pointType == "BEZIER_POINT":
            return "execute_bezierspline"
        elif self.usevectorlist == False and self.pointType != "BEZIER_POINT":
            return "execute_polyspline"    

    def execute_polysplines(self, points, resetframe, start, end, radius, tilt, q, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        identifier = self.identifier + "poly"
        if useCustomIdentifier:
            identifier = customIdentifier + "poly"  
        if T == resetframe:
            p[identifier] = []

        p_object = p.get(identifier, [])
        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return splinelist

        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if T >= start and T <= end :
                p_object[i].polyspline.appendPoint(point, radius, tilt)
            splinelist.append(p_object[i].polyspline)
        p[identifier] = p_object
        return splinelist

    def execute_beziersplines(self, points, resetframe, start, end, radius, tilt, smoothness, q, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        identifier = self.identifier + "bezier"
        if useCustomIdentifier:
            identifier = customIdentifier + "bezier" 
        if T == resetframe:
            p[identifier] = []

        p_object = p.get(identifier, [])
        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            return splinelist

        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if T >= start and T <= end and T % q == 0 :
                p_object[i].bezierspline.appendPoint(point, (0,0,0), (0,0,0), radius, tilt)    
            splinelist.append(p_object[i].bezierspline)
            splinelist[i].smoothAllHandles(smoothness)
        p[identifier] = p_object
        return splinelist    

    def execute_polyspline(self, point, resetframe, start, end, radius, tilt, q, useCustomIdentifier, customIdentifier):
        points = Vector3DList.fromValues([point])
        splines = self.execute_polysplines(points, resetframe, start, end, radius, tilt, q, useCustomIdentifier, customIdentifier)
        if len(splines) == 0: 
            return PolySpline()
        else:    
            return splines[0]

    def execute_bezierspline(self, point, resetframe, start, end, radius, tilt, smoothness, q, useCustomIdentifier, customIdentifier):
        points = Vector3DList.fromValues([point])
        splines = self.execute_beziersplines(points, resetframe, start, end, radius, tilt, smoothness, q, useCustomIdentifier, customIdentifier)
        if len(splines) == 0: 
            return BezierSpline()
        else:    
            return splines[0]    