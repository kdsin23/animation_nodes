import bpy
from bpy.props import *
from ... data_structures import Vector3DList
from ... utils.depsgraph import getEvaluatedID
from ... base_types import AnimationNode, VectorizedSocket

class RigidBodyTrigger(bpy.types.Node, AnimationNode):
    bl_idname = "an_RigidBodyTrigger"
    bl_label = "Rigid Body Trigger"
    errorHandlingType = "EXCEPTION"

    useObjectList: VectorizedSocket.newProperty()
    linkObject: BoolProperty(name = "Link Object", description = "link objects to rigid body collection", default = True, update = AnimationNode.refresh)
    enableLink: BoolProperty(name = "Enable Link", description = "Disabling this option will stop linking on every execution", default = True, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Scene", "Scene", "scene", hide = True)
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects")))
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "Threshold", "threshold", value = 0.5)

        self.newOutput(VectorizedSocket("Object", "useObjectList",
            ("Object", "objectOut", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objectsOut")))

    def edit(self):
        inputSocket = self.inputs[0]
        origin = inputSocket.dataOrigin
        if origin is None: return
        if origin.dataType != "Scene":
            inputSocket.removeLinks()
            inputSocket.hide = True

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "linkObject", text = "Link Objects", toggle = True)
        row2 = row.row(align = True)
        testIcon = "LAYER_USED"
        if self.enableLink:
            testIcon = "LAYER_ACTIVE"
        row2.prop(self, "enableLink", text = "", icon = testIcon)
        row.active = self.enableLink

    def execute(self, scene, objects, falloff, threshold):
        if objects is None:
            return
        if not self.useObjectList:
            objects = [objects]
        if not scene is None:
            rigidbody_world = scene.rigidbody_world
            if rigidbody_world is None:
                self.raiseErrorMessage("Rigid Body World not found")
            else:
                locations = Vector3DList.fromValues([getEvaluatedID(object).location for object in objects])
                self.rigidbody_falloff_animate(objects, rigidbody_world, locations, falloff, threshold)

        return objects

    def rigidbody_falloff_animate(self, objects, rigidbody_world, locations, falloff, threshold):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influences = falloffEvaluator.evaluateList(locations)
        
        rb_collection = rigidbody_world.collection
        if rb_collection is None:
            self.setErrorMessage("Rigid Body Collection not found")
        else:
            rb_objects = rb_collection.objects
            if self.enableLink:
                self.link_Objects(objects, rb_objects)

            for obj, influence in zip(objects, influences):
                if obj.type != "MESH":
                    self.setErrorMessage("Object is not a mesh object")
                else:
                    try:
                        obj.rigid_body.kinematic = True
                        if threshold <= influence:
                            obj.rigid_body.kinematic = False
                    except:
                        self.setErrorMessage("Link objects to rigid body collection")           

    def link_Objects(self, objects, rb_objects):
        for obj in objects:
            if self.linkObject:
                if obj.name not in rb_objects: rb_objects.link(obj)
            else:
                if obj.name in rb_objects: rb_objects.unlink(obj)

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")
