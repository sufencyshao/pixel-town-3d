"""Publish v7 reports only for the reviewed, hashed production frames."""
from pathlib import Path
import json,hashlib,shutil
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/'validation/head-turn-anatomy'
PRODUCTION=Path(__file__).resolve().parent

def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def main():
    validation=read('validation/head-turn-anatomy/validation.json')
    daily=read('validation/daily-actions/validation.json')
    full=read('validation/head-turn-anatomy/full-validation/asset-validation.json')['summary']
    review=read('validation/head-turn-anatomy/visual-review.json')
    browser=read('validation/head-turn-anatomy/browser-check.json')
    changed=read('validation/head-turn-anatomy/changed-files.json')
    assert not validation['errors'] and not daily['errors'] and not full['errors']
    assert len(review['roles'])==40 and review['uniquePosesReviewed']==280
    assert browser['allImages']['brokenImages']==0 and browser['allImages']['images']==80
    for row in review['roles']:
        for name,digest in row['reviewedFrameSHA256'].items():assert sha(ROOT/name)==digest,name
    counts=Counter()
    for name in changed['changedAssetAndMetadataFiles']:
        if '/animations/daily/shake_head/' in name:key='individualFrames'
        elif '/source/shake-head-solid/' in name:key='registeredHeads'
        elif '/source/' in name:key='existingMasks'
        elif name.endswith('.json'):key='manifests'
        else:key='atlasesGifsOverviews'
        counts[key]+=1
    total=len(changed['changedAssetAndMetadataFiles'])
    exact=sum(row['neutralFramesExact'] for row in validation['checks'])
    lines=[
        '# 全人物摇头颈肩修正 v7',
        '',
        '日期：2026-10-03。当前正式版本：`20261003-refusal-anatomy-v7`。',
        '',
        '本次重新校准全部 40 人的整头、下巴、颈部与身体连接。制作侧已逐人查看七种独立姿势的完整人物和放大颈肩区域，共 280 个姿势；正式导出 1000 张帧并通过技术检查。原来固定衣料盖住头发、肩顶缺口、颈部锚点取到发梢、脖子被拉长的问题已分别处理。',
        '',
        '[逐帧动态对照](preview.html) · [完整修改清单](changed-files.json) · [逐人视觉记录](visual-review.json) · [技术检查](validation.json) · [全库检查](full-validation/asset-validation.md)',
        '',
        '## 具体修正',
        '',
        '- 衣服、双肩和道具作为稳定底层；整头、头发、耳朵及头上配饰位于前层。解除 v6 将原衣领/围裙肩带强行盖在头发前面的做法，保留自然遮挡。',
        '- 头颅按原图发顶和下巴高度独立配准，脖子另接到原衣领开口。40 人的原下巴、原颈根和源姿势标定冻结在 `tools/head_anatomy_calibration.json`，避免长发尾端被识别成脖子。',
        '- 源头部仍复用此前保存的整头姿势表，最近邻切片并量化到该角色原色。本次没有再生成整张角色，原 sprite sheet 与基础帧不改。',
        '- 林苔、闻豆的少量被原发型遮住的衣料，复用原衣服像素补齐；章铃补全两侧肩顶及衣服轮廓，许巡复用对侧制服补全辫子移开后露出的左肩。新增不透明像素范围保存在逐角色的身体修补遮罩中。',
        '- 禾青、许巡保留原图下段辫子的细节，上段最多横向弯动 5px，越接近辫梢越归回原位置；花音保留整根源发辫，清除辫梢的误生成浅色残片。',
        '- 修补下巴与拟合颈部之间由切片产生的细小透明缝隙，仅在真实皮肤与颈部上下相接的列内复用颈部像素。',
        '',
        f'{exact} 人的五个回正相位与归一化原正面逐像素相同。章铃、许巡回正使用原头部叠到修补后的同一身体底层，避免肩顶只在转向帧出现；麦麦、陈锅沿用 v5 的匹配回正补画以处理旧白帽残影。全部原 `frame_01` 与基础动作保持哈希。原图已有的浅色衣料透明细节沿用，本次没有对原基础素材重新抠图。',
        '',
        '## 规格和节奏',
        '',
        '每组 25 张 256×256 RGBA 帧，Alpha 只有 0/255。姿势目标约为左右各 30°，头部没有整块倾斜或上下摆动；前 24 帧各 30ms，720ms 内快速往返两次后回正，最后停顿 480ms。动作配置 `loop=false`，GIF `previewLoop=true` 供重复预览。角度为二维插画姿势目标，不是三维测量值。',
        '',
        '## 检查结果',
        '',
        '| 检查 | 结果 |',
        '|---|---|',
        '| 制作侧目测 | 40 人×7 独立姿势：完整头颅、配饰、双肩、衣领、颈部比例及头发遮挡；最新章铃/许巡补肩后再次检查 |',
        '| 颈肩专项 | 40 动作、1000 帧，0 错误 |',
        '| 衣服底层 | 原衣服像素在修补范围外不改；未被头发遮住的衣服与稳定底层逐像素一致 |',
        '| 独立衣服样本 | 40 人、80 个原衣服区域，不依赖移动头部范围，全部相位通过 |',
        '| 颈部 | 原中央皮肤开口全部不透明，各相位存在跨接缝的像素连接；原下巴高度标定检查通过 |',
        '| 整头/节奏 | 每人七种独立姿势，头顶与轮廓变化；两次往返、回正策略、GIF 实际帧时长通过 |',
        '| 图像规格 | 1000 PNG 与各自图集完全一致；256×256、RGBA、二值 Alpha |',
        '| 日常动作 | 60 对象、162 动作、2936 帧，0 错误、0 提示 |',
        f"| 全库 | {full['entities']} 对象、{full['animations']} 动作，{full['errors']} 错误、{full['warnings']} 既有类别提示 |",
        f"| 原素材与备份 | {validation['preservedFiles']} 个保护文件、{validation['backupFiles']} 个 v6 备份文件哈希一致 |",
        '| 浏览器 | 40 卡片、80 张 256×256 图片，无损坏图片及横向溢出（1280×720）；暂停、逐帧、首尾切换、¼慢放、角色筛选和颈肩开关通过 |',
        '',
        '全库 137 个提示由 40 组单次事件的循环 GIF 预览、11 组宠物连续停顿帧合并和 86 个原有素材提示组成。专项检查的 0 错误表示格式、时长和像素保护通过；不能单独据此判断动作自然度。目测记录保存各角色的实际七张帧文件 SHA256，不把重复相位的 1000 张都说成人工看过。',
        '',
        '[浏览器检查记录](browser-check.json) · [林苔实机对照](browser-proof.png) · [章铃实机对照](browser-38.png) · [许巡实机对照](browser-39.png)',
        '',
        '## 修改文件',
        '',
        f"相对 v6 备份，已有 **{total} 个资产/元数据文件**内容改变：{counts['individualFrames']} 张单帧、{counts['atlasesGifsOverviews']} 个图集/GIF/总览、{counts['manifests']} 个清单、{counts['registeredHeads']} 张已配准头部切片、{counts['existingMasks']} 个旧检查遮罩。完整逐文件清单与新增 40 张身体修补遮罩见 `changed-files.json`。1000 张帧均正式重建，沿用原正面的帧内容保持一致。",
        '',
        '| 文件/目录 | 内容 |',
        '|---|---|',
        '| `characters/<40角色>/animations/daily/shake_head/frame_01.png…frame_25.png` | 颈肩配准和遮挡修正 |',
        '| 同目录 `shake_head.png`、`shake_head.gif`、`overview.gif` | 图集、透明预览、日常动作总览 |',
        '| `animation.json`、`animation-manifest.json`、`animations/daily/manifest.json` | v7 标定、来源、哈希、播放参数 |',
        '| `source/shake-head-solid/key_*.png` | 七种配准整头切片，含颈部与相应发束 |',
        '| `source/shake-head-joint-body.png`、`shake-head-joint-original-head.png` | 稳定身体底层与原移动头部范围 |',
        '| `source/shake-head-body-repair-mask.png` | 新增身体修补范围，未修补的角色为空遮罩 |',
        '| `tools/head_turn.py`、`head_anatomy.py`、`head_anatomy_calibration.json` | 完整头颅、独立颈部和身体遮挡制作代码/标定 |',
        '| `tools/revise_head_turn.py`、`verify_head_turn.py`、`preview_head_turn.py` | 批量重建、保护校验、可暂停逐帧预览 |',
        '| `validation/head-turn-anatomy/` | 当前报告、检查、八组完整关键姿势和八组颈肩放大页 |',
        '| `validation/head-turn-joints/preview.html`、`head-turn-revision/preview.html` | 用户原预览 URL 同步当前版本，图片按内容哈希刷新 |',
        '| `validation/head-turn-joints/completion.md`、`preview-v6.html` | 旧版报告标为历史，旧预览冻结到备份 |',
        '| `validation/daily-actions/generation.json`、`preview.html`、`completion.md` | 当前日常动作来源、预览、说明 |',
        '| `asset-gallery.html`、`人物工作交接.md` | 当前画廊与交接状态 |',
        '| `production/head-turn-anatomy-20261003/` | v6 资产备份、前后源码、诊断过程、最终报告脚本 |',
        '',
        '旧 v6 报告的技术检查曾通过，但没有充分覆盖发型遮挡和肩顶缺口。它已标为历史，不作为本次视觉结论依据。当前可重建代码位于 `tools/`；生产目录的 `prototype.py` 与 `candidate-*` 仅为诊断草稿，正式输出以角色 `animations/daily/shake_head/` 和本报告记录的帧哈希为准。',
        '',
        '## 逐人复查与签收状态',
        '',
        '**制作侧已完成全部 40 人的视觉复查；本次 v7 仍未记录用户最终签收。**此前“全部确认”仅属于已签收的 20 人背面走路，不迁移到这次摇头。以下名单为本次的完整角色和复查重点。',
        '',
        '| 编号 | 角色 | 复查重点 | 制作侧 | 用户签收 |',
        '|---|---|---|---|---|',
    ]
    for row in review['roles']:
        lines.append(f"| {row['role'][:2]} | {row['name']} | {row['notes']} | 7/7 已复查 | 待最终签收 |")
    lines+=['','## 重建与回退','','```bash','python3 tools/revise_head_turn.py','python3 tools/verify_head_turn.py','python3 tools/verify_daily_actions.py','python3 tools/build_gallery.py','python3 tools/validate_assets.py --output validation/head-turn-anatomy/full-validation','```','','重建只复用现有像素素材，不调用图像生成 API。v6 回退文件在 `production/head-turn-anatomy-20261003/before/`，修正前源码在 `code-before/`，当前源码快照在 `code-after/`。没有同步或重新打包 pixel-town-app；本次交付为人物素材库和本地预览。']
    (AUDIT/'completion.md').write_text('\n'.join(lines)+'\n')
    (AUDIT/'visual-review.md').write_text('\n'.join([
        '# 制作侧逐人视觉复查 v7','','已查看全部 40 人、每人七种独立姿势的完整人物与颈肩放大区域。重复相位由专项检查核对；不把程序连通性视为视觉验收。用户签收尚未记录。','',
        '| 角色 | 复查重点 | 完整人物/颈肩页 |','|---|---|---|',
        *[f"| {r['role'][:2]} {r['name']} | {r['notes']} | [完整人物]({r['fullBodyBoard']}) / [颈肩放大]({r['seamBoard']}) |" for r in review['roles']],
        '', '[被复查的帧 SHA256](visual-review.json) · [完整报告](completion.md)'])+'\n')
    old=ROOT/'validation/head-turn-joints/completion.md';text=old.read_text()
    if '> 历史版本说明' not in text:
        text=text.replace('# 全部人物摇头颈肩修正 v6','# 全部人物摇头颈肩修正 v6（历史版本）',1)
        text=text.replace('当前版本：','历史版本：',1)
        marker='> 历史版本说明：用户继续反馈肩膀消失、颈部错位及衣料挡住头发。v6 的技术检查并未证明视觉问题已解决；本页保留历史记录，当前实现、制作侧逐人复查及签收状态见 [v7 报告](../head-turn-anatomy/completion.md)。\n\n'
        text=text.replace('已按用户反馈',marker+'已按用户反馈',1)
        text=text.replace('(preview.html)','(preview-v6.html)')
        old.write_text(text)
    handoff=ROOT/'人物工作交接.md';text=handoff.read_text()
    current_note='> 当前摇头素材：全部 40 人已更新为 v7，并完成制作侧七姿势复查；[最新报告](validation/head-turn-anatomy/completion.md) 和 [逐帧预览](validation/head-turn-anatomy/preview.html)。本次摇头尚未记录用户签收，原背面走路签收继续有效。'
    if current_note not in text:
        anchor='## 一、'
        index=text.find(anchor)
        if index>=0:text=text[:index].rstrip()+'\n\n'+current_note+'\n\n'+text[index:]
        else:text=text.replace('\n\n','\n\n'+current_note+'\n\n',1)
    text=text.replace('## 十、人物摇头修正（2026-10-03）','## 十、人物摇头修正（2026-10-03，历史版本）')
    text=text.replace('## 十一、30° 快速拒绝摇头（2026-10-03）','## 十一、30° 快速拒绝摇头（2026-10-03，已被第十二节替换）')
    text=text.replace('当前版本见第十一节','当前版本见第十五节')
    text=text.replace('## 十四、全部人物颈肩接缝修正（2026-10-03，当前版本）','## 十四、全部人物颈肩接缝修正（2026-10-03，已被第十五节替换）')
    text=text.replace('[当前动态对照](validation/head-turn-joints/preview.html)','[v6 历史动态对照](validation/head-turn-joints/preview-v6.html)')
    title='## 十五、整头独立配准与颈肩遮挡修正（2026-10-03，当前版本）'
    section=f'''{title}

当前正式版本为 `20261003-refusal-anatomy-v7`，替换全部 40 人的 shake_head。头颅按原发顶和下巴独立配准，颈部单独连接到原衣领开口；衣服作为稳定底层，转向的整头与头发在前，解决 v6 固定肩带/衣领盖住头发及拉长脖子的问题。逐角色冻结原下巴、原颈根和七种源姿势标定，继续复用此前保存的原素材与整头姿势表。

林苔、闻豆的隐藏衣料复用原衣服补齐；章铃重建两侧肩顶，许巡复用对侧制服补齐发辫移开后露出的左肩。禾青/许巡下段辫子沿用原图细节，上段小幅弯动，花音保留完整源发辫并修正辫梢浅色残片。新增逐角色身体修补范围遮罩。{exact} 人回正完全复用原正面；章铃/许巡回正是原头部加修补身体，麦麦/陈锅继续沿用匹配白帽回正补画。原基础 frame_NN 与 sprite sheet 均不改。

仍为 25 张 256×256 透明硬边帧、约 ±30° 姿势目标、720ms 快速往返两次、480ms 回正停顿。制作侧逐人查看完整人物及放大颈肩，共 40×7=280 个独立姿势，章铃/许巡补肩后再次复查；重复相位由程序核对。专项 40 动作/1000 帧、日常 162 动作/2936 帧均 0 错误；全库 65 对象/920 动作，0 错误、137 个既有类别提示。4784 个保护文件、1600 个 v6 备份哈希一致。相对 v6 修改 {total} 个已有资产/元数据文件，新增 40 张身体修补遮罩。

当前 [报告与完整角色名单](validation/head-turn-anatomy/completion.md)、[逐人视觉记录](validation/head-turn-anatomy/visual-review.md)、[逐帧/慢放对照](validation/head-turn-anatomy/preview.html)、[完整修改清单](validation/head-turn-anatomy/changed-files.json)。用户已打开的 head-turn-joints 和 head-turn-revision 预览同步 v7；v6 页面冻结为 preview-v6.html。预览包含暂停、前后帧、25相位滑杆、角色筛选和颈肩放大，并按输出内容哈希防止读取旧图。

制作侧全部角色复查完成，用户尚未最终签收这次 v7；原背面走路签收继续有效。当前重建使用 tools/ 代码，不运行旧 production/head-turn-joints-20261003/finalize_reports.py，以免回写旧版交接。v6 回退文件、前后源码及诊断稿在 production/head-turn-anatomy-20261003/；正式帧以角色 animations/daily/shake_head/ 为准。重建不调用图像 API；未同步或重新打包 pixel-town-app。
'''
    if title in text:text=text[:text.index(title)].rstrip()+'\n\n'+section
    else:text=text.rstrip()+'\n\n'+section
    handoff.write_text(text)
    daily_path=ROOT/'validation/daily-actions/completion.md';text=daily_path.read_text()
    old_sentence='当前 v6 逐角色校准头身分界和颈部锚点，原肩膀、衣领、颈根固定为前景；花音、禾青、许巡胸前下段发辫保留原遮挡。详见 [当前全角色颈肩修正记录](../head-turn-joints/completion.md)。38 人回正相位精确复用原正面，两位厨师另补画匹配回正姿势以修正旧白帽透明残影。'
    new_sentence=f'当前 v7 独立标定原下巴与颈根，头颅和脖子分别配准，原衣服作为稳定底层，头发自然遮挡肩膀；章铃/许巡补齐发型遮住的肩顶，长辫保留原图细节。详见 [当前全角色颈肩修正记录](../head-turn-anatomy/completion.md)。{exact} 人回正相位精确复用原正面；章铃/许巡保留原头部并叠到修补后的身体；两位厨师沿用匹配白帽回正姿势。'
    text=text.replace(old_sentence,new_sentence).replace('（v6 颈肩修正后）','（v7 颈肩修正后）').replace('validation/head-turn-joints/full-validation/','validation/head-turn-anatomy/full-validation/').replace('40 人 v6 颈肩修正版仍待视觉确认','40 人 v7 已完成制作侧七姿势复查，尚待用户最终签收').replace('[head-turn-joints/changed-files.json](../head-turn-joints/changed-files.json)','[head-turn-anatomy/changed-files.json](../head-turn-anatomy/changed-files.json)')
    daily_path.write_text(text)
    code_after=PRODUCTION/'code-after';code_after.mkdir(exist_ok=True)
    for name in changed['implementation']+['tools/head_joint_calibration.json']:
        shutil.copy2(ROOT/name,code_after/Path(name).name)
    summary={'revision':validation['revision'],'existingChangedFiles':total,'groups':dict(counts),'newBodyRepairMasks':40,'productionVisualReviewRoles':40,'uniquePosesReviewed':280,'originalExactNeutralRoles':exact,'tests':{'shakeHeadErrors':len(validation['errors']),'dailyErrors':len(daily['errors']),'fullErrors':full['errors'],'fullWarnings':full['warnings']},'userApproval':'not yet recorded for v7'}
    write_json(AUDIT/'final-summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
