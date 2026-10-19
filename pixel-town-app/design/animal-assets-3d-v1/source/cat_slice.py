import bpy
bpy.ops.wm.open_mainfile(filepath='/Users/summerwindy/Desktop/AI Chat/pixel-town-app/design/animal-assets-3d-v1/source/cat.blend')
o=bpy.data.objects['Cat']
print(o.matrix_world);print('parent',o.parent.name if o.parent else None)
for z in [3.1,3.3,3.45,3.6]:
 vv=[o.matrix_world@v.co for v in o.data.vertices if abs((o.matrix_world@v.co).z-z)<.09 and .95<(o.matrix_world@v.co).x<1.6]
 print(z,[(round(v.x,2),round(v.y,2),round(v.z,2)) for v in vv][:25])
