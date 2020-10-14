import bpy
from bpy.props import *
from collections import defaultdict
from ... sockets.info import toIdName
from ... base_types import AnimationNode

dataByIdentifier = defaultdict(None)

class SverchokImporterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SverchokImporterNode"
    bl_label = "Sverchok Importer"

    amount: IntProperty(name = "Amount", default = 1, min = 1, update = AnimationNode.refresh)

    def create(self):
        self.newOutput("Generic", "Raw List", "value", hide = True)
        for i in range(self.amount):
            self.newOutput("Generic", f"data_{i}", f"data_{i}")

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
        for i in range(self.amount):
            code += f"in data_{i} s\n"
        code += '"""\n'
        code += "container = ["
        for i in range(self.amount):
            if i == self.amount - 1:
                code += f"data_{i}"
            else:
                code += f"data_{i}, "
        code += "]\n"
        code += f'bpy.data.node_groups["{nodeTreeName}"].nodes["{nodeName}"].setValue(container)'

        text.clear()
        text.write(code)

    def getExecutionCode(self, required):
        yield "value = self.getValue()"
        for i in range(self.amount):
            yield f"data_{i} = self.returnValue(value, {i})"

    def returnValue(self, value, index):
        try:
            if type(value[index][0]) is list:
                flat_list = [item for i in value[index] for item in i]
                return flat_list
            return value[index]
        except:
            return None

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
