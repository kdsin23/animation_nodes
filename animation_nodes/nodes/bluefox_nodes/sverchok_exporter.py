import bpy
from bpy.props import *
from collections import defaultdict
from ... sockets.info import toIdName
from ... base_types import AnimationNode

dataByIdentifier = defaultdict(None)

class SverchokExporterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SverchokExporterNode"
    bl_label = "Sverchok Exporter"

    amount: IntProperty(name = "Amount", default = 1, min = 1, update = AnimationNode.refresh)    

    def create(self):
        self.newInput("Generic", "Value", "value", hide = True)
        for i in range(self.amount):
            self.newInput("Generic", f"data_{i}", f"data_{i}")

    def draw(self, layout):
        layout.prop(self, "amount", text = "Amount")
        row = layout.row(align = True)
        self.invokeFunction(row, "generateScript", text = "Generate Script")

    def generateScript(self):
        nodeTreeName = str(self.id_data.name)
        nodeName = str(self.name)
        textName = nodeName + "_Script"
        text = bpy.data.texts.get(textName)
        if not text:
            text = bpy.data.texts.new(textName)

        code = '"""\n'
        code += 'in input s\n'
        for i in range(self.amount):
            code += f"out data_{i} s\n"
        code += '"""\n'
        code += f'container = bpy.data.node_groups["{nodeTreeName}"].nodes["{nodeName}"].getValue()\n'
        for i in range(self.amount):
            code += f'data_{i} = [container[{i}]]\n'

        text.clear()
        text.write(code)

    def execute(self, value, *args):
        if self.inputs[0].is_linked:
            self.inputs[0].removeLinks()
        self.setValue(args)

    def setValue(self, value):
        dataByIdentifier[self.identifier] = value

    def getValue(self):
        return dataByIdentifier.get(self.identifier)

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)
