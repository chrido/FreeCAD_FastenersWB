# -*- coding: utf-8 -*-
###################################################################################
#
#  FastenerBase.py
#  
#  Copyright 2015 Shai Seger <shaise at gmail dot com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################
from FreeCAD import Gui
import FreeCAD, FreeCADGui, Part, os
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Icons' )

class FSBaseObject:
  '''Base Class for all fasteners'''
  def __init__(self, obj, attachTo):
    obj.addProperty("App::PropertyLength","offset","Parameters","Offset from surface").offset = 0.0
    obj.addProperty("App::PropertyBool", "invert", "Parameters", "Invert screw direction").invert = False
    obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base object").baseObject = attachTo
  
FSCommands = []
FSClassIcons = {}

def FSGetCommands():
  return FSCommands


# common helpers 
class FSFaceMaker:
  '''Create a face point by point on the x,z plane'''
  def __init__(self):
    self.edges = []
    self.firstPoint = None
    
  def AddPoint(self, x, z):
    curPoint = FreeCAD.Base.Vector(x,0,z)
    if (self.firstPoint == None):
      self.firstPoint = curPoint
    else:
      self.edges.append(Part.makeLine(self.lastPoint, curPoint))
    self.lastPoint = curPoint
    FreeCAD.Console.PrintLog("Add Point: " + str(curPoint) + "\n")

    
  def GetFace(self):
    self.edges.append(Part.makeLine(self.lastPoint, self.firstPoint))
    w = Part.Wire(self.edges)
    return Part.Face(w)
    
def FSAutoDiameterM(holeObj, table, tablepos):
  res = 'M5'
  if holeObj != None and hasattr(holeObj, 'Curve') and hasattr(holeObj.Curve, 'Radius'):
    d = holeObj.Curve.Radius * 2
    mindif = 10.0
    for m in table:
        if tablepos == -1:
          dia = float(m.lstrip('M')) + 0.1
        else:
          dia = table[m][tablepos] + 0.1
        if (dia > d):
          dif = dia - d
          if dif < mindif:
            mindif = dif
            res = m
  return res

class FSViewProviderIcon:
  "A View provider for custom icon"
      
  def __init__(self, obj):
    obj.Proxy = self
    self.Object = obj.Object
      
  def attach(self, obj):
    self.Object = obj.Object
    return

  def updateData(self, fp, prop):
    return

  def getDisplayModes(self,obj):
    modes=[]
    return modes

  def setDisplayMode(self,mode):
    return mode

  def onChanged(self, vp, prop):
    return

  def __getstate__(self):
    #        return {'ObjectName' : self.Object.Name}
    return None

  def __setstate__(self,state):
    if state is not None:
      import FreeCAD
      doc = FreeCAD.ActiveDocument #crap
      self.Object = doc.getObject(state['ObjectName'])
 
  def getIcon(self):
    for type in FSClassIcons:
      if isinstance(self.Object.Proxy, type):
        return os.path.join( iconPath , FSClassIcons[type])
    return None


def FSGenerateObjects(objectClass, name):
  baseObjectNames = [ None ]
  obj = None
  selObjects = Gui.Selection.getSelectionEx()
  if len(selObjects) > 0:
    baseObjectNames = selObjects[0].SubElementNames
    obj = selObjects[0].Object
  for baseObjectName in baseObjectNames:      
    a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    if baseObjectName == None:
      baseObject = None
    else:
      baseObject = (obj, [baseObjectName])
    objectClass(a, baseObject)
    FSViewProviderIcon(a.ViewObject)
  FreeCAD.ActiveDocument.recompute()



# common actions on fateners:
class FSFlipCommand:
  """Flip Screw command"""

  def GetResources(self):
    icon = os.path.join( iconPath , 'IconFlip.svg')
    return {'Pixmap'  : icon , # the name of a svg file available in the resources
            'MenuText': "Flip fastner" ,
            'ToolTip' : "flip fastner orientation"}
 
  def Activated(self):
    selObj = self.GetSelection()
    if selObj == None:
      return
    selObj.invert = not(selObj.invert)
    FreeCAD.ActiveDocument.recompute()
    return
   
  def IsActive(self):
    selObj = self.GetSelection()
    if selObj != None:
      return True
    return False

  def GetSelection(self):
    screwObj = None
    if len(Gui.Selection.getSelectionEx()) == 1:
      obj = Gui.Selection.getSelectionEx()[0].Object
      if (hasattr(obj, 'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
        if obj.baseObject != None:
          screwObj = obj
    return screwObj
        
        
Gui.addCommand('FSFlip',FSFlipCommand())
FSCommands.append('FSFlip')

class FSMoveCommand:
  """Move Screw command"""

  def GetResources(self):
    icon = os.path.join( iconPath , 'IconMove.svg')
    return {'Pixmap'  : icon , # the name of a svg file available in the resources
            'MenuText': "Move fastner" ,
            'ToolTip' : "Move fastner to a new location"}
 
  def Activated(self):
    selObj = self.GetSelection()
    if selObj[0] == None:
      return
    selObj[0].baseObject = selObj[1]
    FreeCAD.ActiveDocument.recompute()
    return
   
  def IsActive(self):
    selObj = self.GetSelection()
    if selObj[0] != None:
      return True
    return False

  def GetSelection(self):
    screwObj = None
    edgeObj = None
    for selObj in Gui.Selection.getSelectionEx():
      obj = selObj.Object
      if (hasattr(obj, 'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
        screwObj = obj
      elif (len(selObj.SubObjects) == 1 and isinstance(selObj.SubObjects[0],Part.Edge)):
        edgeObj = (obj, [selObj.SubElementNames[0]])
    return (screwObj, edgeObj)
        
        
Gui.addCommand('FSMove',FSMoveCommand())
FSCommands.append('FSMove')
 