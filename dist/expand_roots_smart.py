#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更智能地扩充词根词汇 - 包含词根的单词（不仅是前缀开头）
"""

import json

# 词根及其变体
root_variants = {
    'eco- (环境,生态)': ['eco', 'ecol', 'econom'],
    'auto- (自己,自动)': ['auto'],
    'pro- (向前,赞成)': ['pro', 'prof', 'prog', 'prom', 'prop', 'prov'],
    'de- (向下,离开)': ['de', 'dec', 'def', 'deg', 'del', 'dem', 'den', 'dep', 'der', 'des', 'det', 'dev'],
    'co- (共同,一起)': ['co', 'col', 'com', 'con', 'cor'],
    'pre- (预先,前)': ['pre'],
    'ex- (出,外)': ['ex', 'exp'],
    'in- (不,无;向内)': ['in', 'im', 'il', 'ir'],
    're- (再次,回)': ['re'],
    'un- (不,无)': ['un'],
    'dis- (不,无;分开)': ['dis'],
    'trans- (跨越,转移)': ['trans'],
    'sub- (下,次)': ['sub'],
    'inter- (之间,相互)': ['inter'],
    'over- (过度,在上)': ['over'],
    'under- (下,不足)': ['under'],
    'super- (上,超)': ['super'],
    'anti- (反对,对抗)': ['anti'],
    'micro- (小,微观)': ['micro'],
    'macro- (大,宏观)': ['macro'],
    'tele- (远,远程)': ['tele'],
    'photo- (光)': ['photo'],
    'bio- (生命)': ['bio'],
    'geo- (地球,土地)': ['geo'],
    'hydro- (水)': ['hydro'],
    'thermo- (热)': ['thermo'],
    'electro- (电)': ['electro'],
    'aero- (空气)': ['aero'],
    'neuro- (神经)': ['neuro'],
    'psycho- (心理,精神)': ['psycho'],
    'socio- (社会)': ['socio'],
    'techno- (技术)': ['techno'],
}

# 手动添加的常见考研词汇（不在 NETEM 5530 中）
manual_words = {
    'ecosystem': '生态系统',
    'ecological': '生态的',
    'environmental': '环境的',
    'environment': '环境',
    'automotive': '汽车的',
    'autonomous': '自治的、自主的',
    'profile': '轮廓、简介',
    'profound': '深刻的',
    'progressive': '进步的',
    'prosperity': '繁荣',
    'prosperous': '繁荣的',
    'protocol': '协议',
    'prototype': '原型',
    'provoke': '激怒',
    'prudent': '谨慎的',
    'degrade': '降级',
    'dehydrate': '脱水',
    'deliberate': '深思熟虑的',
    'demographic': '人口统计的',
    'denounce': '谴责',
    'deplete': '耗尽',
    'deploy': '部署',
    'deport': '驱逐',
    'depress': '压抑',
    'deprive': '剥夺',
    'derivative': '衍生物',
    'descendant': '后代',
    'desert': '沙漠、抛弃',
    'desolate': '荒凉的',
    'despair': '绝望',
    'destination': '目的地',
    'destiny': '命运',
    'destructive': '破坏性的',
    'detain': '拘留',
    'deteriorate': '恶化',
    'devastate': '摧毁',
    'deviate': '偏离',
    'devote': '奉献',
    'coherent': '连贯的',
    'cohesive': '凝聚的',
    'collaborate': '合作',
    'commemorate': '纪念',
    'compensate': '补偿',
    'competent': '胜任的',
    'complement': '补充',
    'comply': '遵守',
    'conceive': '构想',
    'condemn': '谴责',
    'confer': '授予',
    'confine': '限制',
    'conform': '符合',
    'confront': '面对',
    'conscientious': '认真的',
    'consensus': '共识',
    'conserve': '保护',
    'consolidate': '巩固',
    'conspicuous': '显著的',
    'constitute': '构成',
    'constrain': '约束',
    'contaminate': '污染',
    'contemplate': '沉思',
    'contempt': '蔑视',
    'contend': '竞争',
    'contradict': '反驳',
    'contrive': '设法',
    'convene': '召集',
    'converge': '汇聚',
    'converse': '交谈',
    'convey': '传达',
    'convict': '定罪',
    'coop': '合作',
    'coordinate': '协调',
    'preach': '布道',
    'precede': '先于',
    'precise': '精确的',
    'predecessor': '前任',
    'predicate': '断言',
    'predominant': '主要的',
    'preliminary': '初步的',
    'premature': '过早的',
    'premise': '前提',
    'prescribe': '开处方',
    'preside': '主持',
    'prestige': '威望',
    'presume': '假设',
    'prevail': '盛行',
    'prevalent': '流行的',
    'pretext': '借口',
    'prevail': '盛行',
    'exceed': '超过',
    'excel': '优秀',
    'excerpt': '摘录',
    'exclaim': '呼喊',
    'exclude': '排除',
    'excursion': '远足',
    'execute': '执行',
    'exemplify': '例证',
    'exempt': '免除',
    'exert': '施加',
    'exile': '流放',
    'expand': '扩展',
    'expedition': '远征',
    'expel': '驱逐',
    'expend': '花费',
    'expire': '到期',
    'explicit': '明确的',
    'exploit': '开发',
    'expose': '暴露',
    'expound': '阐述',
    'express': '表达',
    'expulsion': '驱逐',
    'extend': '延伸',
    'exterior': '外部',
    'external': '外部的',
    'extinct': '灭绝的',
    'extraordinary': '非凡的',
    'extravagant': '奢侈的',
    'inhabit': '居住',
    'inaugurate': '开创',
    'incidence': '发生率',
    'incorporate': '合并',
    'incredible': '难以置信的',
    'incur': '招致',
    'induce': '引起',
    'indulge': '沉溺',
    'infectious': '传染的',
    'inferior': '低等的',
    'infinite': '无限的',
    'inflate': '膨胀',
    'inflict': '施加',
    'ingenious': '巧妙的',
    'inherent': '固有的',
    'inhibit': '抑制',
    'initiate': '发起',
    'inject': '注射',
    'innate': '天生的',
    'innovate': '创新',
    'inquire': '询问',
    'insulate': '绝缘',
    'intact': '完整的',
    'integral': '完整的',
    'integrity': '完整',
    'intellectual': '智力的',
    'intelligible': '可理解的',
    'interact': '互动',
    'intercept': '拦截',
    'intervene': '干预',
    'intimate': '亲密的',
    'intricate': '复杂的',
    'intrinsic': '固有的',
    'intuition': '直觉',
    'invalid': '无效的',
    'invaluable': '无价的',
    'invariably': '总是',
    'invert': '倒转',
    'investigate': '调查',
    'involve': '涉及',
    'irony': '讽刺',
    'irrespective': '不顾的',
    'irritate': '激怒',
}

def expand_roots_smart():
    """智能扩充词根词汇"""
    # 读取现有数据
    with open('data/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 加载 NETEM 词汇
    with open('/Users/tongterence/Desktop/xianyu/netem_vocab/netem_full_list.json', 'r', encoding='utf-8') as f:
        netem = json.load(f)
    
    netem_words = {}
    for item in netem.get('5530考研词汇词频排序表', []):
        word = item.get('单词', '').lower()
        meaning = item.get('释义', '')
        if word and meaning:
            netem_words[word] = meaning
    
    # 合并手动添加的词汇
    all_words = {**netem_words, **manual_words}
    
    # 为每个词根查找匹配的单词
    added_count = 0
    for root in data['roots']:
        root_name = root['name']
        
        # 获取该词根的变体
        variants = root_variants.get(root_name, [])
        if not variants:
            continue
        
        # 查找匹配的单词
        existing_words = {w['word'].lower() for w in root['words']}
        
        for word, meaning in all_words.items():
            # 检查是否包含该词根的任何一个变体
            matched = False
            for variant in variants:
                if word.startswith(variant):
                    matched = True
                    break
            
            # 如果匹配且不在现有单词中，则添加
            if matched and word not in existing_words:
                # 检查是否已经在其他词根中
                already_in_other_root = False
                for other_root in data['roots']:
                    if other_root['name'] != root_name:
                        for other_word in other_root['words']:
                            if other_word['word'].lower() == word:
                                already_in_other_root = True
                                break
                    if already_in_other_root:
                        break
                
                if not already_in_other_root:
                    root['words'].append({
                        'word': word,
                        'meaning': meaning,
                        'example': '',
                        'source': '扩充词汇'
                    })
                    added_count += 1
    
    # 更新总单词数
    total_words = sum(len(r['words']) for r in data['roots'])
    data['totalWords'] = total_words
    
    # 保存数据
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'已添加 {added_count} 个新单词')
    print(f'总单词数: {total_words}')
    
    # 显示一些例子
    print('\n扩充后的词根示例:')
    for root in data['roots']:
        if root['name'] in ['eco- (环境,生态)', 'auto- (自己,自动)', 'pro- (向前,赞成)', 'de- (向下,离开)']:
            print(f'\n{root["name"]}: {len(root["words"])} 个单词')
            for word in root['words'][:15]:
                print(f'  - {word["word"]}: {word.get("meaning", "")}')

if __name__ == '__main__':
    expand_roots_smart()
