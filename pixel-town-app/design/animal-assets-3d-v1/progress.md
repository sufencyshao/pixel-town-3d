# 动物3D资产制作进度

2026-10-17。仅在本目录制作独立资产，不修改正式应用、存档、原2D、整镇或人物模型。

- [x] 读取项目入口并核对原20动物的ID、名字、物种、品种、花色。
- [x] 固定来源、保存许可与SHA-256。
- [x] 制作20只可辨识动物、真实骨骼关节动作。
- [x] 输出原生Blender与GLB、manifest。
- [x] 保存重开、GLB回导、动作/骨架/形态验证、可视接触表。

坐标约定：glTF +Y向上、+Z向前、足底地面为Y=0、米制。manifest.animals 每项为 id/name/species/breed/coat/source/glb/height/length/radius/actions/headLocal/bodyLocal/groundOffset/front，动作仅声明实际存在的clips。

最终质检中发现原Cat骨架存在多个无父根骨、且骨架局部轴与场景轴不同；增加统一MotionRoot并按实际世界轴换算关节。所有来源动作重采样为24fps，逐帧蒙皮最低点修正负穿地；保留Run自然离地相位。犬Rest明确为四足站立放松，未冒称犬伏卧。

已最终冻结20份GLB/20份原生/179条动作，根任务收到冻结通知。详细证据见验收报告、qa/validation.json、qa/glb-structure.json、qa/asset-sha256.json。两张可视总览在renders/。
