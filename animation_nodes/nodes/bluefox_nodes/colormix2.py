import bpy
from ... data_structures import *
from bpy.props import *
from ... events import executionCodeChanged
from ... base_types import AnimationNode, VectorizedSocket

modeItems = [
    ("MIX", "Mix", "Mix", "", 0),
    ("ADD", "Add", "Add", "", 1),
    ("LIGHTEN", "Lighten", "Lighten", "", 2),
    ("SCREEN", "Screen", "Screen", "", 3),
    ("OVERLAY", "Overlay", "Overlay", "", 4),
    ("DARKEN", "Darken", "Darken", "", 5),
    ("MULTIPLY", "Multiply", "Multiply", "", 6),
    ("SUBTRACT", "Subtract", "subtract", "", 7)
]

class Colormix2(bpy.types.Node, AnimationNode):
    bl_idname = "an_Colormix2"
    bl_label = "Colormix2"

    usecolor1List: VectorizedSocket.newProperty()
    usecolor2List: VectorizedSocket.newProperty()
    usefactorList: VectorizedSocket.newProperty()

    mode = EnumProperty(name = "Type", default = "MIX",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Color", "usecolor1List",
            ("Color1", "color1"), ("Colors1", "colors1")))
        self.newInput(VectorizedSocket("Color", "usecolor2List",
            ("Color2", "color2"), ("Colors2", "colors2")))
        self.newInput(VectorizedSocket("Float", "usefactorList",
            ("F", "f"), ("Fs", "fs")))

        self.newOutput(VectorizedSocket("Color", ["usecolor1List", "usecolor2List", "usefactorList"],
            ("Color", "color"), ("Colors", "colors")))

    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.usecolor1List ==0 and self.usecolor2List ==0 and self.usefactorList ==0 :
            return "executeSingle" 
        elif self.usecolor1List and self.usecolor2List and self.usefactorList==0 :
            return "execute_multicolorlist_singlefactor"
        elif self.usecolor1List ==0 and self.usecolor2List ==0 and self.usefactorList :
            return "execute_singlecolor_multifactor" 
        elif self.usecolor1List and self.usecolor2List ==0 and self.usefactorList==0 :
            return "execute_singlecolorlist1_singlefactor"
        elif self.usecolor1List and self.usecolor2List ==0 and self.usefactorList :
            return "execute_singlecolorlist1_multifactor"  
        elif self.usecolor1List==0 and self.usecolor2List and self.usefactorList==0 :
            return "execute_singlecolorlist2_singlefactor"
        elif self.usecolor1List==0 and self.usecolor2List and self.usefactorList :
            return "execute_singlecolorlist2_multifactor"              


    def execute_multicolorlist_singlefactor(self, colors1, colors2, f):
        if len(colors1)==0 or len(colors2)==0 :
            return ColorList()
        else: 
            count = max(len(colors1),len(colors2))
            self.fillList(colors1, count)
            self.fillList(colors2, count)
            results = colors1
            for i in range(count):
                res = colors1[i]
                results[i]= self.Blend_col(res, colors1[i], colors2[i],f)
            return results

    def execute_singlecolor_multifactor(self, color1, color2, fs):
        count = len(fs)
        results = ColorList.fromValues([color1])
        self.fillList(results, count)
        for i in range(count):
            res = color1
            results[i]= self.Blend_col(res, color1, color2,fs[i])
        return results  

    def execute_singlecolorlist1_singlefactor(self, colors1, color2, f):
            count = len(colors1)
            results = colors1
            for i in range(count):
                res = colors1[i]
                results[i]= self.Blend_col(res, colors1[i], color2,f)
            return results 

    def execute_singlecolorlist1_multifactor(self, colors1, color2, fs):
            count = max(len(colors1),len(fs))
            self.fillList(colors1, count)
            self.fillList(fs, count)
            results = colors1
            for i in range(count):
                res = colors1[i]
                results[i]= self.Blend_col(res, colors1[i], color2,fs[i])
            return results 

    def execute_singlecolorlist2_singlefactor(self, color1, colors2, f):
            count = len(colors2)
            results = colors2
            for i in range(count):
                res = color1
                results[i]= self.Blend_col(res, color1, colors2[i],f)
            return results 

    def execute_singlecolorlist2_multifactor(self, color1, colors2, fs):
            count = max(len(colors2),len(fs))
            self.fillList(colors2, count)
            self.fillList(fs, count)
            results = colors2
            for i in range(count):
                res = color1
                results[i]= self.Blend_col(res, color1, colors2[i],fs[i])
            return results                                           

    def executeSingle(self, color1, color2,f):
        res = color1
        return self.Blend_col(res, color1, color2, f)

    def Mix_col(self, color1, color2, f):
        res=color1
        res.r=color1[0]*(1-f) + color2[0]*f
        res.g=color1[1]*(1-f) + color2[1]*f
        res.b=color1[2]*(1-f) + color2[2]*f
        res.a=1
        return res

    def Blend_col(self, res, color1, color2,f):
            if self.mode == "ADD":
                res.r=color1[0] + color2[0]
                res.g=color1[1] + color2[1]
                res.b=color1[2] + color2[2]
                res.a=1
            elif self.mode == "SUBTRACT":
                res.r=color1[0] - color2[0]
                res.g=color1[1] - color2[1]
                res.b=color1[2] - color2[2]
                res.a=1
            elif self.mode == "MULTIPLY":
                res.r=color1[0] * color2[0]
                res.g=color1[1] * color2[1]
                res.b=color1[2] * color2[2]
                res.a=1 
            elif self.mode == "MIX":
                res = self.Mix_col(color1,color2,f)
            elif self.mode == "OVERLAY":    
                if color1[0]<0.5:
                    res.r=2*color1[0]*color2[0]
                else:
                    res.r=1-2*(1-color1[0])*(1-color2[0])
                if color1[1]<0.5:
                    res.g=2*color1[1]*color2[1]
                else:
                    res.g=1-2*(1-color1[1])*(1-color2[1])
                if color1[2]<0.5:
                    res.b=2*color1[2]*color2[2]
                else:
                    res.b=1-2*(1-color1[2])*(1-color2[2])                
                res.a=1
            elif self.mode == "LIGHTEN":    
                res.r=max(color1[0],color2[0])
                res.g=max(color1[1],color2[1])
                res.b=max(color1[2],color2[2])
                res.a=1
            elif self.mode == "DARKEN":
                res.r=min(color1[0],color2[0])
                res.g=min(color1[1],color2[1])
                res.b=min(color1[2],color2[2])
                res.a=1
            elif self.mode == "SCREEN":
                res.r=1-(1-color1[0]) * (1-color2[0])
                res.g=1-(1-color1[1]) * (1-color2[1])
                res.b=1-(1-color1[2]) * (1-color2[2])
                res.a=1
            return self.Mix_col(color1, res, f) 

    def fillList(self,l, count):
        n = len(l)
        if n == count:
            return
        d = count - n
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return         
        

         
      

