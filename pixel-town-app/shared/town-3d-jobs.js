'use strict';
// Practice procedures for the later roster, whose source profiles predate structured occupationalBehaviors.
const procedures={
  firefighter:['核对值勤清单','演练报警信息复述与现场分工','记录训练结果与交接事项'],
  grocer:['核对补货清单','练习商品分类和顾客需求问询','记录货架整理计划'],
  farmer:['查看田间巡查安排','观察作物与讨论养护方法','记录下一轮田间计划'],
  driver:['复述出车检查项目','练习站点播报与安全提醒','记录交接事项'],
  hairdresser:['询问发型偏好','练习服务沟通与操作顺序','复述清洁整理流程'],
  baker:['检查配方和准备清单','练习配比与烘焙顺序','记录清洁和交接事项'],
  librarian:['核对读者需求','练习图书分类和检索引导','记录整理计划'],
  mechanic:['询问故障现象','练习排查步骤与安全检查','记录维修建议与待办'],
  innkeeper:['核对接待准备事项','练习入住说明和访客问询','记录房务交接事项'],
  florist:['询问花材与色彩偏好','练习搭配方案说明','记录养护提示'],
  barista:['询问咖啡口味','练习冲煮顺序与风味说明','记录器具清洁清单'],
  carpenter:['核对尺寸与工具清单','练习工序说明和安全检查','记录后续修缮计划'],
  postal:['核对配送准备清单','练习地址确认与路线复述','记录投递待办'],
  police:['核对社区巡访事项','练习安全提示和邻里沟通','记录值班交接'],
  doctor:['核对接待准备清单','练习一般健康服务沟通','记录交接和清洁事项']
};
function fallback(id){const key=Object.keys(procedures).find(k=>id.includes('_'+k+'_'));return key?procedures[key]:[];}
module.exports={fallback};
