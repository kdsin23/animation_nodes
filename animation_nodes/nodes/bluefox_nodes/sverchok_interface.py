import bpy
from bpy.props import *
from collections import defaultdict
from ... sockets.info import toIdName
from ... base_types import AnimationNode

dataByIdentifier = defaultdict(None)

dataDirectionItems = {
    ("IMPORT", "Import", "Receive data from Sverchok", "IMPORT", 0),
    ("EXPORT", "Export", "Send data to Sverchok", "EXPORT", 1) }

class SverchokInterfaceNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SverchokInterfaceNode"
    bl_label = "Sverchok Interface"
    bl_width_default = 180

    dataDirection: EnumProperty(name = "Data Direction", default = "IMPORT",
        items = dataDirectionItems, update = AnimationNode.refresh)

    amount: IntProperty(name = "Amount", default = 1, min = 1, update = AnimationNode.refresh)

    def create(self):
        if self.dataDirection == "IMPORT":
            self.newOutput("Generic", "Raw List", "value", hide = True)
            for i in range(self.amount):
                self.newOutput("Generic", f"data_{i}", f"data_{i}")
        if self.dataDirection == "EXPORT":
            self.newInput("Generic", "Value", "value", hide = True)
            for i in range(self.amount):
                self.newInput("Generic", f"data_{i}", f"data_{i}")        

    def draw(self, layout):
        layout.prop(self, "dataDirection", text = "")
        row2 = layout.row(align = True)
        row2.prop(self, "amount", text = "")
        self.invokeFunction(row2, "generateScript", text = "Generate", 
                description = "Generate script for sverchok", icon = "TEXT")   

    def generateScript(self):
        nodeTreeName = str(self.id_data.name)
        nodeName = str(self.name)
        textName = nodeName
        code = ""

        if self.dataDirection == "IMPORT":
            textName += "_Import_Script"
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

        elif self.dataDirection == "EXPORT":
            textName += "_Export_Script"
            code = '"""\n'
            code += 'in input s\n'
            for i in range(self.amount):
                code += f"out data_{i} s\n"
            code += '"""\n'
            code += f'container = bpy.data.node_groups["{nodeTreeName}"].nodes["{nodeName}"].getValue()\n'
            for i in range(self.amount):
                code += f'data_{i} = [container[{i}]]\n'

        text = bpy.data.texts.get(textName)
        if not text:
            text = bpy.data.texts.new(textName)
        text.clear()
        text.write(code)

    def execute(self, *args):
        if self.dataDirection == "IMPORT":
            value = self.getValue()
            result = [value]
            for i in range(self.amount):
                result.append(self.returnValue(value, i))
            return tuple(result)
        elif self.dataDirection == "EXPORT":
            if self.inputs[0].is_linked:
                self.inputs[0].removeLinks()
            self.setValue(args[1:])

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
