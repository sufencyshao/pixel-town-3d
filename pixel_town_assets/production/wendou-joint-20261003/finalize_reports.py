"""Record this isolated corrective pass; never rebuild or change sprite files."""
from pathlib import Path
import json,hashlib,shutil,re

ROOT=Path(__file__).resolve().parents[2]
PROD=Path(__file__).resolve().parent
AUDIT=ROOT/'validation/wendou-joint'
GLOBAL=ROOT/'validation/head-turn-anatomy'
ROLE='36_barista_female'
REV='20261003-wendou-joint-v1'
PHASES=[0,1,2,3,7,8,9]

def read(path):return json.loads(path.read_text())
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    tech=read(AUDIT/'validation.json');assert not tech['errors']
    head=read(GLOBAL/'validation.json');assert not head['errors']
    daily=read(ROOT/'validation/daily-actions/validation.json');assert not daily['errors']
    full=read(AUDIT/'full-validation/asset-validation.json')
    assert full['summary']['errors']==0
    browser=read(AUDIT/'browser-check.json')
    assert len(browser['steps'])==25 and all(not r['overflow'] and all(im['loaded'] for im in r['images']) for r in browser['steps'])
    change=read(AUDIT/'changed-files.json')
    if 'tools/verify_head_turn.py' not in change['implementation']:change['implementation'].append('tools/verify_head_turn.py')
    write(AUDIT/'changed-files.json',change)
    hashes={f'characters/{ROLE}/animations/daily/shake_head/frame_{i+1:02d}.png':
            sha(ROOT/f'characters/{ROLE}/animations/daily/shake_head/frame_{i+1:02d}.png') for i in PHASES}
    review={'role':ROLE,'name':'闻豆','revision':REV,'supersedes':'v7 review missed the displaced neck and incorrect garment samples',
        'uniquePosesReviewed':7,'phaseIndicesZeroBased':PHASES,'technicalPhasesChecked':25,
        'reviewMethod':'Viewed final-keyposes.png full sprites and neck crops for all seven unique poses; browser max-turn comparison at phases 3 and 9, quarter-speed playback and 25-step image-loading check. Repeated phases are verified by pixels, not claimed as 25 separate visual reviews.',
        'frameSHA256':hashes,'visualArtifactSHA256':{n:sha(AUDIT/n) for n in ['final-keyposes.png','browser-proof-negative.png','browser-proof-positive.png']},
        'findings':'Neck root now follows the original V collar; original neck/collar rectangle is exact in all25 phases; real apron straps are fixed body pixels. Whole skull/hair source poses are reused.',
        'userApproval':'pending for this corrective revision'}
    write(AUDIT/'visual-review.json',review)
    (AUDIT/'completion.md').write_text('''# 闻豆摇头：颈根追加修正

日期：2026-10-03。角色：闻豆 `36_barista_female`。当前角色修订：`20261003-wendou-joint-v1`，基础批次仍为 v7。

用户指出闻豆的脖子形状或位置异常，上一轮制作侧复查确实漏掉了这一处。本次只重新制作闻豆的摇头；另外 39 人沿用原资产与上一轮记录，不能把它们说成本轮重新人工验收过。

[逐帧对照](preview.html) · [七种正式姿态](final-keyposes.png) · [技术检查](validation.json) · [视觉记录和帧哈希](visual-review.json) · [逐文件修改清单](changed-files.json)

## 问题与处理

- 原图的 V 形领口尖端位于 `(140,137)`；旧颈根目标设为 `(130,134)`，让转向头部接在偏左、偏高的位置。现在把颈根定位到 `(140,138)`，并将原下巴阴影的起行标为 y=125。
- 原图露出的脖子是衣领内的窄 V 形区域。现在直接复用其原始形状和阴影，去除源头部遗留的宽颈轮廓，不再把另一种脖子压缩后塞入领口。
- 蓝色围裙肩带、米色衣领及其深色边缘属于固定身体；修正误切进头部的衣料。取消旧自动补肩中复制到错误位置的颜色，本角色当前不新增身体像素。
- 旧“衣服样本”取到了马尾及颈部边缘，检查结果不能证明真实衣料保留。新增四处实际蓝色肩带/米色衣领样本，并独立核对整个原颈根与衣领下缘。

仍复用既有完整整头姿势表、原调色板及最近邻切片。单帧 256×256 RGBA，Alpha 仅 0/255；约 ±30° 的插画姿势目标，720ms 内快速往返两次，回正停顿 480ms。五个回正相位与归一化原图逐像素相同。

## 复查结果

| 项目 | 结果 |
|---|---|
| 正式帧 | 25 帧；7 个独立姿态已查看完整人物和放大颈肩 |
| 颈根和衣领下缘 | 原图区域 x126…152、y128…139 在全部 25 相位逐像素一致；V 领尖端位置、颜色不变 |
| 实际衣料 | 4 处独立样本、53 个像素保留在身体底层，未混入原移动头部切片 |
| 透明与颜色 | 256×256、二值 Alpha、原图颜色；专项 0 错误 |
| 全人物摇头 | 40 组、1000 帧，技术检查 0 错误；其中独立衣料样本更新为 82 处 |
| 日常动作 | 60 对象、162 动作、2936 帧，0 错误、0 提示 |
| 全库 | 65 对象、920 动作，0 错误、137 个既有类别提示 |
| 保护范围 | 6383 个文件哈希一致，包含其余 39 人的摇头、原素材、其他动作和宠物；另单独比较闻豆日常清单中非摇头条目，全部一致 |
| 回退 | 41 个旧 v7 资产/清单备份哈希一致 |
| 浏览器 | 双侧最大转角、¼慢放、25 相位切换已核对；无损坏图片、无横向溢出 |

保护快照最初同时把闻豆整份日常清单列为待替换和待保护，保留原快照不改。核对脚本明确只排除它的整文件哈希比较，改为逐项保护非摇头内容；因此为 6383 个整文件哈希加一份清单的非摇头条目比较。

## 修改文件

闻豆目录中 **36 个已有资产/元数据文件**内容改变：20 张转向单帧，3 个图集/GIF/总览，3 份清单，7 张头部切片，3 张检查遮罩。25 张帧均导出，5 张回正帧的内容沿用原图。逐文件路径和 SHA 证据见 `changed-files.json`、`before.json`、`visual-review.json`。

| 文件或目录 | 修改内容 |
|---|---|
| `characters/36_barista_female/animations/daily/shake_head/` | 重新配准的 25 张正式帧 |
| 同角色 `shake_head.png`、`shake_head.gif`、`overview.gif` | 图集、透明循环预览、日常动作总览 |
| 同角色三份动作清单 | 角色修订号、纠正后的标定、来源和哈希 |
| 同角色 `source/shake-head-solid/key_*.png`、`shake-head-joint-*.png`、`shake-head-body-repair-mask.png` | 整头切片、正确衣料底层、原移动区域和空身体补画遮罩 |
| `tools/head_anatomy.py`、`head_turn.py`、`wendou_joint_calibration.json` | 闻豆颈根与衣料分区制作逻辑、独立校准 |
| `tools/revise_wendou_joint.py`、`verify_wendou_joint.py`、`verify_head_turn.py` | 单角色重建、真实颈领区域校验、旧错误衣料样本替换 |
| `tools/preview_head_turn.py` | 可生成单角色专项对照，保留全人物原预览入口 |
| `validation/wendou-joint/` | 本报告、实际衣料样本、检查、截图、七姿态和逐文件记录 |
| `validation/head-turn-anatomy/`、旧预览 URL、日常报告/画廊、`人物工作交接.md` | 最新版本与闻豆追加修正状态 |
| `production/wendou-joint-20261003/` | v7 回退、代码前后快照、历史报告与当前交付记录 |

## 确认状态与重建

本次闻豆的颈根位置、比例和转动衔接仍待用户视觉确认。40 人的新摇头整体最终签收尚未记录，完整名单继续保留在 [全人物报告](../head-turn-anatomy/completion.md)；此前背面走路的签收不受影响。技术检查通过不等于用户认定动作自然。

本轮使用原像素校准，没有重新生成原 sprite sheet。正式资产以角色 `animations/daily/shake_head/` 为准；`candidate-*` 为诊断稿。

可在素材根目录运行 `python3 tools/revise_wendou_joint.py` 仅重建闻豆，再运行 `python3 tools/verify_wendou_joint.py` 与 `python3 tools/verify_head_turn.py`。不要运行旧批次的报告终结脚本覆盖本次追加记录。
''')
    # Keep historical v7 evidence frozen; current combined record carries 39
    # unchanged reviews and replaces only the explicitly reopened role36.
    combined=read(PROD/'v7-visual-review.json')
    for row in combined['roles']:
        if row['role']==ROLE:
            row.update({'reviewedFrameSHA256':hashes,'roleRevision':REV,
                'notes':'原 V 领颈根重新定位；蓝肩带、米色衣领与下缘固定；七姿态追加复查',
                'productionVisualStatus':'re-reviewed after user rejected the prior v7 neck result',
                'userApproval':'pending for Wendou corrective v1',
                'correctiveReview':'../wendou-joint/visual-review.json'})
        else:
            assert all(sha(ROOT/n)==v for n,v in row['reviewedFrameSHA256'].items())
    combined['method']='Previous v7 review missed Wendou. Carry forward 273 unchanged reviewed poses for the other39; replace only Wendou with the seven newly viewed full sprites/neck crops and browser max-turn proofs. Script checks repeated phases; no new blanket visual signoff is inferred.'
    combined['latestRoleCorrection']={'role':ROLE,'revision':REV,'freshUniquePosesReviewed':7,'unchangedPriorUniquePosesCarried':273,'record':'../wendou-joint/visual-review.json'}
    combined['boardSHA256']={n:sha(GLOBAL/n) for n in combined['boardSHA256']}
    write(GLOBAL/'visual-review.json',combined)
    md=(PROD/'v7-visual-review.md').read_text()
    note='> 追加纠正：用户反馈闻豆的脖子仍有问题，原 v7 目测漏检。闻豆现为 `20261003-wendou-joint-v1`，重新查看七个姿态并核对实际领口；其余 39 人仅沿用旧记录和未变化的帧哈希。本轮没有重新宣布全部角色人工验收通过。见 [闻豆追加记录](../wendou-joint/completion.md)。\n\n'
    md=md.replace('\n\n','\n\n'+note,1).replace('完整马尾和耳饰转向，原蓝围裙及衣袖稳定','原 V 领颈根重新定位，蓝肩带和米色衣领固定；追加七姿态复查')
    md=md.replace('已查看全部 40 人、每人七种独立姿势的完整人物与颈肩放大区域。重复相位由专项检查核对；不把程序连通性视为视觉验收。用户签收尚未记录。',
        '本轮重新查看闻豆七种独立姿态；其余 39 人的 273 个姿态仅沿用上轮记录与未变化的帧哈希。重复相位由专项检查核对，不把程序连通性视为视觉验收。用户最终签收尚未记录。')
    (GLOBAL/'visual-review.md').write_text(md)
    # Recompute the current difference from the frozen v6 assets, rather than
    # preserving a stale file count from the first v7 report.
    origin=read(GLOBAL/'before.json')
    changed=[n for n,v in origin['replacedFileSHA256'].items() if sha(ROOT/n)!=v]
    groups={'manifests':0,'atlasesGifsOverviews':0,'individualFrames':0,'registeredHeads':0,'existingMasks':0}
    for n in changed:
        if n.endswith('.json'):groups['manifests']+=1
        elif '/animations/daily/shake_head/frame_' in n:groups['individualFrames']+=1
        elif '/source/shake-head-solid/key_' in n:groups['registeredHeads']+=1
        elif '/source/' in n:groups['existingMasks']+=1
        else:groups['atlasesGifsOverviews']+=1
    current_changes=read(GLOBAL/'changed-files.json');current_changes['changedAssetAndMetadataFiles']=changed
    current_changes['latestRoleCorrection']={'role':ROLE,'revision':REV,'changeList':'validation/wendou-joint/changed-files.json'}
    for n in change['implementation']:
        if n not in current_changes['implementation']:current_changes['implementation'].append(n)
    if 'validation/wendou-joint/' not in current_changes['reportsAndPreview']:current_changes['reportsAndPreview'].append('validation/wendou-joint/')
    write(GLOBAL/'changed-files.json',current_changes)
    summary=read(PROD/'v7-final-summary.json');summary.update({'existingChangedFiles':len(changed),'groups':groups,
        'latestRoleCorrection':{'role':ROLE,'revision':REV,'changedAssetAndMetadataFiles':len(change['changedAssetAndMetadataFiles']),
            'technicalFramesChecked':25,'freshUniquePosesReviewed':7,'unchangedPriorPosesCarried':273,'report':'../wendou-joint/completion.md'},
        'userApproval':'pending for v7 and Wendou corrective revision'})
    write(GLOBAL/'final-summary.json',summary)
    doc=(PROD/'v7-completion.md').read_text()
    notice='''> **闻豆追加修正（当前）**：用户反馈揭示本报告原 v7 复查漏掉了闻豆颈根偏位，旧衣服检查样本也选错。闻豆已独立修正为 `20261003-wendou-joint-v1`；原 V 领颈根及衣领下缘在全部 25 相位精确保留，七种独立姿态重新查看。其余 39 人保留原资产和上一轮记录。当前不新增全人物人工验收结论，用户最终签收仍待记录。见 [闻豆对照](../wendou-joint/preview.html)、[追加修正与文件清单](../wendou-joint/completion.md)。

'''
    doc=doc.replace('本次重新校准全部 40 人',notice+'此前 v7 重新校准全部 40 人',1)
    doc=doc.replace('林苔、闻豆的少量被原发型遮住的衣料','林苔的少量被原发型遮住的衣料')
    doc=doc.replace('新增不透明像素范围保存在逐角色的身体修补遮罩中。','新增不透明像素范围保存在逐角色的身体修补遮罩中。闻豆原自动补肩现已撤销，当前不新增身体像素；她的颈部改为复用原 V 领内的阴影形状，具体标定位于 `tools/wendou_joint_calibration.json`。',1)
    doc=doc.replace('40 人、80 个原衣服区域','40 人、82 个原衣服区域（闻豆四处样本重新定位）')
    doc=doc.replace('**制作侧已完成全部 40 人的视觉复查；本次 v7 仍未记录用户最终签收。**','**上一轮制作侧复查漏掉了闻豆；本轮仅重新复查闻豆七姿态，其余 39 人沿用旧记录。v7 与闻豆追加修正均未记录用户最终签收。**')
    doc=doc.replace('完整马尾和耳饰转向，原蓝围裙及衣袖稳定 | 7/7 已复查','原 V 领颈根重新定位；蓝肩带和米色衣领固定 | 7/7 追加复查')
    doc=doc.replace('| 制作侧目测 | 40 人×7 独立姿势：完整头颅、配饰、双肩、衣领、颈部比例及头发遮挡；最新章铃/许巡补肩后再次检查 |',
        '| 制作侧目测 | 本轮闻豆七姿态重新查看完整人物/颈肩；其余39人的273个姿态为上一轮记录，原闻豆漏检结论已被追加记录替换 |')
    doc=doc.replace('1337',str(len(changed)))
    doc=re.sub(r'820 张单帧、120 个图集/GIF/总览、120 个清单、246 张已配准头部切片、31 个旧检查遮罩',
        f'{groups["individualFrames"]} 张单帧、{groups["atlasesGifsOverviews"]} 个图集/GIF/总览、{groups["manifests"]} 个清单、{groups["registeredHeads"]} 张已配准头部切片、{groups["existingMasks"]} 个旧检查遮罩',doc)
    doc+='\n最新闻豆的独立检查为 25 相位、53 个真实衣料样本像素和 6383 个文件哈希保护；修改 36 个角色资产/元数据文件，5 个回正帧内容保持原图。全库检查已刷新到闻豆追加修正后的正式资产，仍为 0 错误、137 个既有提示。详见 [专项检查](../wendou-joint/validation.json)、[双侧转角对照](../wendou-joint/browser-proof-positive.png) 与 [本次回退记录](../../production/wendou-joint-20261003/)。\n'
    (GLOBAL/'completion.md').write_text(doc)
    for p in (AUDIT/'full-validation').iterdir():
        if p.is_file():shutil.copy2(p,GLOBAL/'full-validation'/p.name)
    handoff=ROOT/'人物工作交接.md'
    text=handoff.read_text();heading='## 十六、闻豆颈根单独追加修正'
    if heading in text:text=text[:text.index(heading)].rstrip()+'\n'
    text=text.replace('## 十五、整头独立配准与颈肩遮挡修正（2026-10-03，当前版本）','## 十五、整头独立配准与颈肩遮挡修正（2026-10-03，基础批次；闻豆最新见第十六节）')
    text+='''
## 十六、闻豆颈根单独追加修正（2026-10-03，当前）

用户反馈第十五节的闻豆脖子仍有形状/位置异常，原制作侧复查漏检。本次只重建 `36_barista_female` 的 `shake_head`，角色修订号 `20261003-wendou-joint-v1`。原颈根目标 `(130,134)` 偏离实际 V 领尖端，现配准到 `(140,138)`；下巴阴影行定位到 y125，原窄 V 颈部形状/阴影直接复用。正确固定蓝肩带、米色领口及深色边缘，撤销错误的自动补肩，去掉源宽颈残留。

25 帧仍为 256×256 透明硬边、约 ±30°、720ms 两次快速往返、480ms 回正停顿；五个回正相位与原图逐像素一致。原颈根与衣领下缘在全部 25 相位精确保留。四处实际衣料样本共 53 像素，替换误选马尾/颈缘的旧检查区域。正式七姿态已查看完整人物/颈肩放大，并在浏览器核对双侧最大转角、¼慢放和25相位加载。

角色专项与全人物40动作/1000帧、日常162动作/2936帧均0错误；全库65对象/920动作为0错误、137既有类别提示。6383个文件哈希一致，另外单独保护闻豆日常清单内的非摇头条目；41个旧v7回退文件哈希一致。本次36个角色资产/元数据文件内容改变：20张转向帧、3个图集/GIF/总览、3份清单、7张头部切片、3张检查遮罩。

当前 [闻豆逐帧对照](validation/wendou-joint/preview.html)、[修正与文件清单](validation/wendou-joint/completion.md)、[专项检查](validation/wendou-joint/validation.json)、[七姿态视觉记录](validation/wendou-joint/visual-review.json)。全人物旧预览入口同步新闻豆，其他39人资产未重建、仅沿用上一轮记录，本轮不新增全人物人工验收结论。闻豆这次颈部位置/比例仍待用户视觉确认；全部新摇头的最终签收尚未记录，原背面走路签收继续有效。

独立标定在 `tools/wendou_joint_calibration.json`；只重建闻豆可运行 `python3 tools/revise_wendou_joint.py`，再运行 `tools/verify_wendou_joint.py` 与 `tools/verify_head_turn.py`。代码前后快照、v7回退和历史报告在 `production/wendou-joint-20261003/`。不要运行旧批次的报告终结脚本覆盖本次追加记录。原sprite sheet、基础帧、其他人物动作及宠物不变；未重新打包pixel-town-app。
'''
    handoff.write_text(text)
    p=ROOT/'validation/daily-actions/completion.md';d=p.read_text()
    if '## 闻豆颈部追加修正' in d:d=d[:d.index('## 闻豆颈部追加修正')].rstrip()+'\n'
    d+='''
## 闻豆颈部追加修正（2026-10-03）

用户反馈暴露出 v7 中闻豆的颈根标定和原衣料检查样本错误，已独立纠正为 `20261003-wendou-joint-v1`。现在原 V 领颈根及衣领下缘在 25 相位保持原形/原位，蓝肩带和米色衣领属于稳定身体。其余39人沿用原资产及上一轮视觉记录；不把本次单角色修正当作全人物的新人工验收结论。见 [最新专项对照](../wendou-joint/preview.html)、[追加报告与清单](../wendou-joint/completion.md)。新摇头最终用户签收仍待记录，原背面签收有效。日常专项仍0错误；全库最新检查仍0错误、137既有提示。
''';p.write_text(d)
    code=PROD/'code-after';code.mkdir(exist_ok=True)
    for n in change['implementation']:shutil.copy2(ROOT/n,code/Path(n).name)
    write(PROD/'delivery-record.json',{'role':ROLE,'revision':REV,'changedFiles':len(change['changedAssetAndMetadataFiles']),
        'protectedFileHashes':6383,'backupFiles':41,'headErrors':0,'dailyErrors':0,'fullErrors':0,'fullWarnings':137,
        'userApproval':'pending','report':'validation/wendou-joint/completion.md'})
    print(json.dumps({'wendouChangedFiles':len(change['changedAssetAndMetadataFiles']),
        'currentGlobalChangesFromV6':len(changed),'globalGroups':groups,'freshReviewedPoses':7,
        'priorUnchangedPosesCarried':273},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
