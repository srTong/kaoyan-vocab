#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复词根分解 - 提供更科学的解释
"""

import json

# 更科学的词根分解字典
scientific_etymologies = {
    # co- 词根
    'companion': 'com-(共同) + pan(面包) + -ion → 一起吃面包的人 → 同伴',
    'company': 'com-(共同) + pan(面包) + -y → 一起吃面包的人群 → 公司、陪伴',
    'compassion': 'com-(共同) + passion(感受) → 共同感受 → 同情',
    'compel': 'com-(共同) + pel(驱动) → 共同驱动 → 强迫',
    'compete': 'com-(共同) + pet(追求) → 共同追求 → 竞争',
    'competent': 'com-(共同) + pet(追求) + -ent → 能共同追求的 → 胜任的',
    'competition': 'com-(共同) + pet(追求) + -ition → 共同追求 → 竞争',
    'competitive': 'com-(共同) + pet(追求) + -itive → 共同追求的 → 竞争的',
    'competitor': 'com-(共同) + pet(追求) + -or → 共同追求的人 → 竞争者',
    'compile': 'com-(共同) + pile(堆) → 堆在一起 → 编译、收集',
    'complain': 'com-(共同) + plain(拍打) → 拍打胸膛 → 抱怨',
    'complaint': 'com-(共同) + plain(拍打) + -t → 拍打胸膛 → 抱怨',
    'complement': 'com-(共同) + plement(填充) → 共同填充 → 补充',
    'complete': 'com-(完全) + plete(填充) → 完全填满 → 完成',
    'completely': 'com-(完全) + plete(填充) + -ly → 完全填满 → 完全地',
    'complex': 'com-(共同) + plex(编织) → 编织在一起 → 复杂的',
    'complicated': 'com-(共同) + plic(折叠) + -ated → 折叠在一起 → 复杂的',
    'comply': 'com-(共同) + ply(折叠) → 折叠在一起 → 遵守',
    'component': 'com-(共同) + pon(放置) + -ent → 放在一起的东西 → 组件',
    'compose': 'com-(共同) + pose(放置) → 放在一起 → 组成、作曲',
    'composition': 'com-(共同) + pos(放置) + -ition → 放在一起 → 作文',
    'compound': 'com-(共同) + pound(放置) → 放在一起 → 化合物',
    'comprehend': 'com-(完全) + prehend(抓住) → 完全抓住 → 理解',
    'comprehensive': 'com-(完全) + prehend(抓住) + -ive → 完全抓住的 → 全面的',
    'compress': 'com-(共同) + press(压) → 压在一起 → 压缩',
    'comprise': 'com-(共同) + prise(拿) → 拿在一起 → 包含',
    'compromise': 'com-(共同) + promise(承诺) → 共同承诺 → 妥协',
    'compulsory': 'com-(共同) + puls(驱动) + -ory → 共同驱动的 → 强制的',
    'compute': 'com-(共同) + pute(思考) → 共同思考 → 计算',
    'computer': 'com-(共同) + pute(思考) + -er → 共同思考的机器 → 计算机',
    'comrade': 'com-(共同) + rade(走) → 一起走的人 → 同志',
    
    # de- 词根
    'debate': 'de-(向下) + bat(打) → 向下打 → 辩论',
    'decade': 'deca-(十) + -de → 十年为一个周期',
    'decay': 'de-(向下) + cay(落下) → 向下坠落 → 腐烂、衰败',
    'deceive': 'de-(向下) + ceive(拿) → 拿错 → 欺骗',
    'decent': 'de-(向下) + cent(落下) → 向下落 → 体面的',
    'decide': 'de-(向下) + cide(切) → 切下去 → 决定',
    'decision': 'de-(向下) + cis(切) + -ion → 切下去 → 决定',
    'decisive': 'de-(向下) + cis(切) + -ive → 切下去的 → 决定性的',
    'declare': 'de-(完全) + clare(清楚) → 完全说清楚 → 宣布',
    'decline': 'de-(向下) + cline(弯) → 向下弯 → 下降、拒绝',
    'decorate': 'de-(完全) + cor(装饰) + -ate → 完全装饰 → 装饰',
    'decrease': 'de-(向下) + crease(生长) → 向下生长 → 减少',
    'decree': 'de-(向下) + cree(相信) → 向下相信 → 法令',
    'dedicate': 'de-(完全) + dic(说) + -ate → 完全说出 → 奉献',
    'deduce': 'de-(向下) + duce(引导) → 向下引导 → 推断',
    'deem': 'deem-(想) → 想 → 认为',
    'deep': 'deep-(深) → 深 → 深的',
    'deer': 'deer-(动物) → 动物 → 鹿',
    'default': 'de-(向下) + fault(错) → 向下错 → 违约、默认',
    'defeat': 'de-(向下) + feat(做) → 做下去 → 击败',
    'defend': 'de-(离开) + fend(打) → 打退 → 防御',
    'defense': 'de-(离开) + fense(打) → 打退 → 防御',
    'defiant': 'de-(离开) + fi(相信) + -ant → 不相信的 → 反抗的',
    'deficit': 'de-(向下) + fic(做) + -it → 做不下去 → 赤字',
    'define': 'de-(完全) + fine(边界) → 完全划定边界 → 定义',
    'definite': 'de-(完全) + fin(边界) + -ite → 有边界的 → 明确的',
    'defy': 'de-(离开) + fy(相信) → 不相信 → 违抗',
    'degree': 'de-(向下) + gree(步) → 向下一步 → 程度',
    'delay': 'de-(向下) + lay(放) → 放下去 → 延迟',
    'delegate': 'de-(向下) + leg(选择) + -ate → 向下选择 → 代表',
    'deliberate': 'de-(完全) + liber(称) + -ate → 完全称量 → 深思熟虑',
    'delicate': 'de-(完全) + lic(引诱) + -ate → 完全引诱 → 精致的',
    'deliver': 'de-(离开) + liver(自由) → 使自由 → 交付、释放',
    'delivery': 'de-(离开) + liver(自由) + -y → 使自由 → 交付',
    'delusion': 'de-(向下) + lude(玩) + -sion → 玩下去 → 错觉',
    'demand': 'de-(完全) + mand(委托) → 完全要求 → 需求',
    'democracy': 'demo-(人民) + cracy(统治) → 人民统治 → 民主',
    'democratic': 'demo-(人民) + crat(统治) + -ic → 人民统治的 → 民主的',
    'demographic': 'demo-(人民) + graphic(写) → 写人民 → 人口统计的',
    'demonstrate': 'de-(完全) + monstr(显示) + -ate → 完全显示 → 证明',
    'deny': 'de-(向下) + ny(说) → 向下说 → 否认',
    'depart': 'de-(离开) + part(部分) → 从整体中离开 → 离开',
    'department': 'de-(离开) + part(部分) + -ment → 分开的部分 → 部门',
    'departure': 'de-(离开) + part(部分) + -ure → 从整体中离开 → 离开',
    'depend': 'de-(向下) + pend(悬挂) → 向下悬挂 → 依赖',
    'dependent': 'de-(向下) + pend(悬挂) + -ent → 向下悬挂的 → 依赖的',
    'depict': 'de-(向下) + pict(画) → 画下来 → 描绘',
    'deplete': 'de-(向下) + plete(填充) → 向下填充 → 耗尽',
    'deploy': 'de-(向下) + ploy(折叠) → 展开 → 部署',
    'deposit': 'de-(向下) + posit(放置) → 放下去 → 存款、沉积',
    'depress': 'de-(向下) + press(压) → 向下压 → 压抑',
    'depression': 'de-(向下) + press(压) + -ion → 向下压 → 萧条',
    'deprive': 'de-(向下) + prive(单独) → 使单独 → 剥夺',
    'depth': 'depth-(深) → 深 → 深度',
    'deputy': 'de-(向下) + puty(思考) → 向下思考 → 副手',
    'derive': 'de-(向下) + rive(河) → 从河流来 → 源于',
    'describe': 'de-(向下) + scribe(写) → 写下来 → 描述',
    'description': 'de-(向下) + scribe(写) + -tion → 写下来 → 描述',
    'desert': 'de-(离开) + sert(连接) → 离开连接 → 沙漠、抛弃',
    'deserve': 'de-(向下) + serve(服务) → 向下服务 → 应得',
    'design': 'de-(向下) + sign(标记) → 做标记 → 设计',
    'designer': 'de-(向下) + sign(标记) + -er → 做标记的人 → 设计师',
    'desirable': 'de-(向下) + sir(渴望) + -able → 值得渴望的 → 值得拥有的',
    'desire': 'de-(从) + sire(主人) → 渴望成为主人 → 渴望',
    'desk': 'desk-(桌子) → 桌子 → 书桌',
    'despair': 'de-(向下) + spair(希望) → 向下希望 → 绝望',
    'desperate': 'de-(向下) + sper(希望) + -ate → 向下希望 → 绝望的',
    'despite': 'de-(向下) + spite(恶意) → 向下恶意 → 尽管',
    'destiny': 'de-(向下) + stin(站立) + -y → 站立的东西 → 命运',
    'destroy': 'de-(向下) + stroy(建造) → 拆毁 → 破坏',
    'destruction': 'de-(向下) + struct(建造) + -ion → 拆毁 → 破坏',
    'detail': 'de-(向下) + tail(切) → 切下来 → 细节',
    'detain': 'de-(向下) + tain(持有) → 持有住 → 拘留',
    'detect': 'de-(向下) + tect(覆盖) → 揭开覆盖 → 发现',
    'detection': 'de-(向下) + tect(覆盖) + -ion → 揭开覆盖 → 发现',
    'detective': 'de-(向下) + tect(覆盖) + -ive → 揭开覆盖的人 → 侦探',
    'determine': 'de-(完全) + termine(边界) → 完全确定边界 → 决定',
    'determined': 'de-(完全) + termine(边界) + -d → 完全确定边界 → 坚定的',
    'devastate': 'de-(向下) + vast(荒) + -ate → 使荒芜 → 摧毁',
    'develop': 'de-(向下) + velop(包裹) → 解开包裹 → 发展',
    'development': 'de-(向下) + velop(包裹) + -ment → 解开包裹 → 发展',
    'device': 'de-(向下) + vice(看) → 向下看 → 设备',
    'devise': 'de-(向下) + vise(看) → 向下看 → 设计',
    'devote': 'de-(完全) + vote(发誓) → 完全发誓 → 奉献',
    'devoted': 'de-(完全) + vote(发誓) + -d → 完全发誓 → 忠诚的',
    
    # pro- 词根
    'profile': 'pro-(向前) + file(线) → 向前画线 → 轮廓、简介',
    'profit': 'pro-(向前) + fit(做) → 向前做 → 利润',
    'profitable': 'pro-(向前) + fit(做) + -able → 向前做的 → 有利可图的',
    'profound': 'pro-(向前) + found(底部) → 向底部 → 深刻的',
    'program': 'pro-(向前) + gram(写) → 向前写 → 项目',
    'programmer': 'pro-(向前) + gram(写) + -er → 向前写的人 → 程序员',
    'progress': 'pro-(向前) + gress(走) → 向前走 → 进步',
    'progressive': 'pro-(向前) + gress(走) + -ive → 向前走的 → 进步的',
    'prohibit': 'pro-(向前) + hibit(持有) → 向前持有 → 禁止',
    'promising': 'pro-(向前) + mis(送) + -ing → 向前送的 → 有前途的',
    'prompt': 'pro-(向前) + mpt(拿) → 向前拿 → 敏捷的、提示',
    'proportion': 'pro-(向前) + portion(部分) → 向前部分 → 比例',
    'prosecute': 'pro-(向前) + secut(跟随) + -e → 向前跟随 → 起诉',
    'prosperity': 'pro-(向前) + sper(希望) + -ity → 向前希望 → 繁荣',
    'prosperous': 'pro-(向前) + sper(希望) + -ous → 向前希望的 → 繁荣的',
    'protect': 'pro-(向前) + tect(覆盖) → 在前面覆盖 → 保护',
    'protection': 'pro-(向前) + tect(覆盖) + -ion → 在前面覆盖 → 保护',
    'proud': 'proud-(骄傲) → 骄傲 → 骄傲的',
    'prove': 'prove-(证明) → 证明 → 证明',
    'provided': 'pro-(向前) + vide(看) + -d → 向前看 → 提供的',
    'prospect': 'pro-(向前) + spect(看) → 向前看 → 前景',
    'produce': 'pro-(向前) + duce(引导) → 向前引导 → 生产',
    'product': 'pro-(向前) + duct(引导) → 向前引导的东西 → 产品',
    'productive': 'pro-(向前) + duct(引导) + -ive → 向前引导的 → 生产的',
    'productivity': 'pro-(向前) + duct(引导) + -ivity → 向前引导的能力 → 生产力',
    'propose': 'pro-(向前) + pose(放置) → 把想法向前提出 → 提议',
    'promise': 'pro-(向前) + mise(送) → 向前送出 → 承诺',
    'provide': 'pro-(向前) + vide(看) → 向前看 → 提供',
    'procedure': 'pro-(向前) + ced(走) + -ure → 向前走 → 程序',
    'process': 'pro-(向前) + cess(走) → 向前走 → 过程',
    'project': 'pro-(向前) + ject(扔) → 向前扔 → 项目、投射',
    'projector': 'pro-(向前) + ject(扔) + -or → 向前扔的机器 → 投影仪',
    'provoke': 'pro-(向前) + voke(叫) → 向前叫 → 激怒',
    
    # 其他常见词根
    'ecosystem': 'eco-(环境) + system(系统) → 环境系统 → 生态系统',
    'ecological': 'eco-(环境) + log(学科) + -ical → 环境学科的 → 生态的',
    'economic': 'eco-(家) + nom(管理) + -ic → 管理家庭的 → 经济的',
    'economics': 'eco-(家) + nom(管理) + -ics → 管理家庭的学科 → 经济学',
    'economical': 'eco-(家) + nom(管理) + -ical → 管理家庭的 → 经济的',
    'economy': 'eco-(家) + nomy(管理) → 管理家庭 → 经济',
    'ecology': 'eco-(环境) + logy(学科) → 研究环境的学科 → 生态学',
    
    'automatic': 'auto-(自己) + mat(思考) + -ic → 自己思考的 → 自动的',
    'automation': 'auto-(自己) + mat(思考) + -ion → 自己思考 → 自动化',
    'automobile': 'auto-(自己) + mobile(移动) → 自己移动 → 汽车',
    'autonomy': 'auto-(自己) + nomy(法律) → 自己的法律 → 自治',
    'automotive': 'auto-(自己) + motiv(移动) + -ive → 自己移动的 → 汽车的',
    'autonomous': 'auto-(自己) + nom(法律) + -ous → 自己的法律的 → 自治的',
    
    'abandon': 'ab-(离开) + don(给予) → 给予离开 → 放弃',
    'ability': 'abil-(能力) + -ity → 能力',
    'able': 'able-(能够) → 能够',
    'abnormal': 'ab-(离开) + normal(正常) → 离开正常 → 异常的',
    'abolish': 'ab-(离开) + ol(生长) + -ish → 使不生长 → 废除',
    'absolute': 'ab-(离开) + solute(松开) → 完全松开 → 绝对的',
    'absorb': 'ab-(离开) + sorb(吸收) → 吸走 → 吸收',
    'abstract': 'ab-(离开) + tract(拉) → 从具体中拉出来 → 抽象的',
    'absurd': 'ab-(离开) + surd(合理) → 不合理的 → 荒谬的',
    'abuse': 'ab-(离开) + use(使用) → 错误使用 → 滥用',
}

# 读取现有数据
with open('data/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 更新词根分解
updated_count = 0
for root in data['roots']:
    for word_obj in root['words']:
        word = word_obj['word'].lower()
        
        # 如果有更科学的词根分解，更新它
        if word in scientific_etymologies:
            word_obj['etymology'] = scientific_etymologies[word]
            updated_count += 1

# 保存更新后的数据
with open('data/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'已更新 {updated_count} 个单词的词根分解')

# 显示一些例子
print('\n更新后的例子：')
examples = ['companion', 'company', 'ecosystem', 'automatic', 'abandon', 'decide', 'progress']
for root in data['roots']:
    for word in root['words']:
        if word['word'].lower() in examples:
            print(f'\n{word["word"]}: {word.get("etymology", "无")}')
