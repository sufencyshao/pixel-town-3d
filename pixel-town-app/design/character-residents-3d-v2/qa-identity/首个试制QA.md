# 小满首个试制 QA

目前状态：阻止全批的绑定/表情问题已反馈主制作端，待重建后复检。此报告仅指首份原生试制，不代表后续修正版。

- **P1**：Skin 的 shape key Basis 仍为源底模1.7751m，Smile/Talk顶高已映射1.62m，且两个目标默认值均1.0。无动作REST时实际Skin顶高仅1.4649m。脸、眼睛、发型分层错位，手指被拉成细丝。需将Basis一起变形，并把非Basis默认目标归零。
- **P2待复核**：上衣花纹成单个巨大黑花，需在绑定修正后检查GarmentUV的active_render和纹理坐标。
- 裙身与上下身布壳边界边均0，壳体闭合。未发现重复的完整裸体网格；不能以Superhero_Female.001数据名判断重复。
- 原生文件仅打开与渲染，未保存；渲染前后输入SHA-256一致。

证据：`02_hero_female/prototype-01-failed/原图与3D动作对照.png`、`prototype-01-failed/geometry-inspection.json`、`prototype-issues.json`。

后续需重建后重新审阅眼脸、手、鞋、Walk/Sit/Wave的前侧视图，以及全45位原2D/3D对照。
