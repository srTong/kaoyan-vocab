#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 NETEM 5530 词表扩充词根词汇
"""

import json

# 词根前缀映射
root_prefixes = {
    'ab- (离开,相反)': ['ab'],
    'ad- (向,加强)': ['ad'],
    'anti- (反对,对抗)': ['anti'],
    'auto- (自己,自动)': ['auto'],
    'bi- (二,双)': ['bi'],
    'circum- (围绕)': ['circum'],
    'co- (共同,一起)': ['co', 'col', 'com', 'con'],
    'contra- (反对,相反)': ['contra'],
    'counter- (反对,相反)': ['counter'],
    'de- (向下,离开)': ['de'],
    'di- (二,双)': ['di'],
    'dis- (不,无;分开)': ['dis'],
    'eco- (环境,生态)': ['eco'],
    'en- (使,进入)': ['en'],
    'ex- (出,外)': ['ex'],
    'extra- (超出,额外)': ['extra'],
    'fore- (前,预先)': ['fore'],
    'hetero- (不同,异)': ['hetero'],
    'homo- (相同,同)': ['homo'],
    'hyper- (超过,过度)': ['hyper'],
    'hypo- (下,次)': ['hypo'],
    'im- (不,无;进入)': ['im'],
    'in- (不,无;向内)': ['in'],
    'inter- (之间,相互)': ['inter'],
    'macro- (大,宏观)': ['macro'],
    'mal- (坏,恶)': ['mal'],
    'micro- (小,微观)': ['micro'],
    'mid- (中间)': ['mid'],
    'mis- (错,坏)': ['mis'],
    'mono- (一,单)': ['mono'],
    'multi- (多)': ['multi'],
    'non- (不,无)': ['non'],
    'ob- (反对,朝向)': ['ob'],
    'out- (外,超过)': ['out'],
    'over- (过度,在上)': ['over'],
    'per- (完全,贯穿)': ['per'],
    'poly- (多)': ['poly'],
    'post- (后,之后)': ['post'],
    'pre- (预先,前)': ['pre'],
    'pro- (向前,赞成)': ['pro'],
    're- (再次,回)': ['re'],
    'semi- (半,部分)': ['semi'],
    'sub- (下,次)': ['sub'],
    'super- (上,超)': ['super'],
    'sym- (共同,相同)': ['sym'],
    'syn- (共同,合成)': ['syn'],
    'tele- (远,远程)': ['tele'],
    'trans- (跨越,转移)': ['trans'],
    'tri- (三)': ['tri'],
    'ultra- (超,极端)': ['ultra'],
    'un- (不,无)': ['un'],
    'under- (下,不足)': ['under'],
    'uni- (一,单)': ['uni'],
    'up- (上,增加)': ['up'],
    'with- (反对,离开)': ['with'],
}

def load_netem_words():
    """加载 NETEM 5530 词表"""
    with open('/Users/tongterence/Desktop/xianyu/netem_vocab/netem_full_list.json', 'r', encoding='utf-8') as f:
        netem = json.load(f)
    
    words = {}
    for item in netem.get('5530考研词汇词频排序表', []):
        word = item.get('单词', '').lower()
        meaning = item.get('释义', '')
        if word and meaning:
            words[word] = meaning
    
    return words

def expand_roots():
    """扩充词根词汇"""
    # 读取现有数据
    with open('data/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 加载 NETEM 词汇
    netem_words = load_netem_words()
    
    # 创建词根到前缀的映射
    prefix_to_root = {}
    for root_name, prefixes in root_prefixes.items():
        for prefix in prefixes:
            prefix_to_root[prefix] = root_name
    
    # 为每个词根查找匹配的单词
    added_count = 0
    for root in data['roots']:
        root_name = root['name']
        
        # 获取该词根的前缀
        prefixes = root_prefixes.get(root_name, [])
        if not prefixes:
            continue
        
        # 查找匹配的单词
        existing_words = {w['word'].lower() for w in root['words']}
        
        for netem_word, netem_meaning in netem_words.items():
            # 检查是否以该词根的任何一个前缀开头
            matched = False
            for prefix in prefixes:
                if netem_word.startswith(prefix):
                    matched = True
                    break
            
            # 如果匹配且不在现有单词中，则添加
            if matched and netem_word not in existing_words:
                # 检查是否已经在其他词根中
                already_in_other_root = False
                for other_root in data['roots']:
                    if other_root['name'] != root_name:
                        for other_word in other_root['words']:
                            if other_word['word'].lower() == netem_word:
                                already_in_other_root = True
                                break
                    if already_in_other_root:
                        break
                
                if not already_in_other_root:
                    root['words'].append({
                        'word': netem_word.capitalize() if netem_word[0].islower() else netem_word,
                        'meaning': netem_meaning,
                        'example': '',
                        'source': 'NETEM 5530'
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
        if root['name'] in ['eco- (环境,生态)', 'auto- (自己,自动)', 'pro- (向前,赞成)']:
            print(f'\n{root["name"]}: {len(root["words"])} 个单词')
            for word in root['words'][:10]:
                print(f'  - {word["word"]}: {word.get("meaning", "")}')

if __name__ == '__main__':
    expand_roots()
