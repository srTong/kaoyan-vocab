#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复词根分类 - 根据单词前缀正确分类
"""

import pandas as pd
import json
from pathlib import Path

def get_root_for_word(word):
    """根据单词前缀判断词根"""
    word_lower = word.lower()
    
    # 前缀映射
    prefix_map = {
        'co': 'co- (共同,一起)',
        'col': 'co- (共同,一起)',
        'com': 'co- (共同,一起)',
        'con': 'co- (共同,一起)',
        'de': 'de- (向下,离开)',
        'pro': 'pro- (向前,赞成)',
        'pre': 'pre- (预先,前)',
        'ex': 'ex- (出,外)',
        'im': 'im- (不,无;进入)',
        'in': 'in- (不,无;向内)',
        'dis': 'dis- (不,无;分开)',
        'un': 'un- (不,无)',
        're': 're- (再次,回)',
        'sub': 'sub- (下,次)',
        'trans': 'trans- (跨越,转移)',
        'ad': 'ad- (向,加强)',
        'ab': 'ab- (离开,相反)',
        'ob': 'ob- (反对,朝向)',
        'anti': 'anti- (反对,对抗)',
        'auto': 'auto- (自己,自动)',
        'bi': 'bi- (二,双)',
        'centri': 'centri- (中心)',
        'chron': 'chron- (时间)',
        'circum': 'circum- (围绕)',
        'contra': 'contra- (反对,相反)',
        'counter': 'counter- (反对,相反)',
        'deca': 'deca- (十)',
        'di': 'di- (二,双)',
        'eco': 'eco- (环境,生态)',
        'en': 'en- (使,进入)',
        'equi': 'equi- (平等,相等)',
        'extra': 'extra- (超出,额外)',
        'fore': 'fore- (前,预先)',
        'geo': 'geo- (地球,土地)',
        'hemo': 'hemo- (血)',
        'hetero': 'hetero- (不同,异)',
        'homo': 'homo- (相同,同)',
        'hyper': 'hyper- (超过,过度)',
        'hypo': 'hypo- (下,次)',
        'ideo': 'ideo- (思想,概念)',
        'inter': 'inter- (之间,相互)',
        'macro': 'macro- (大,宏观)',
        'mal': 'mal- (坏,恶)',
        'mega': 'mega- (大,百万)',
        'micro': 'micro- (小,微观)',
        'mid': 'mid- (中间)',
        'mini': 'mini- (小,微型)',
        'mis': 'mis- (错,坏)',
        'mono': 'mono- (一,单)',
        'multi': 'multi- (多)',
        'neo': 'neo- (新)',
        'non': 'non- (不,无)',
        'out': 'out- (外,超过)',
        'over': 'over- (过度,在上)',
        'paleo': 'paleo- (古,旧)',
        'pan': 'pan- (全,泛)',
        'para': 'para- (旁,类似)',
        'per': 'per- (完全,贯穿)',
        'photo': 'photo- (光)',
        'poly': 'poly- (多)',
        'post': 'post- (后,之后)',
        'pseudo': 'pseudo- (假,伪)',
        'psycho': 'psycho- (心理,精神)',
        'retro': 'retro- (后,回)',
        'semi': 'semi- (半,部分)',
        'socio': 'socio- (社会)',
        'super': 'super- (上,超)',
        'sym': 'sym- (共同,相同)',
        'syn': 'syn- (共同,合成)',
        'techno': 'techno- (技术)',
        'tele': 'tele- (远,远程)',
        'thermo': 'thermo- (热)',
        'tri': 'tri- (三)',
        'ultra': 'ultra- (超,极端)',
        'under': 'under- (下,不足)',
        'uni': 'uni- (一,单)',
        'up': 'up- (上,增加)',
        'vice': 'vice- (副,次)',
        'with': 'with- (反对,离开)',
    }
    
    # 检查前缀（从长到短）
    for prefix in sorted(prefix_map.keys(), key=len, reverse=True):
        if word_lower.startswith(prefix):
            return prefix_map[prefix]
    
    return None

def fix_root_classification(excel_path, output_dir):
    """修复词根分类"""
    
    df = pd.read_excel(excel_path)
    df['词根'] = df['词根'].ffill()
    df['词根含义'] = df['词根含义'].ffill()
    
    # 创建新的词根数据
    roots_data = {}
    
    for _, row in df.iterrows():
        original_root = str(row['词根']).strip()
        word = str(row['单词']).strip()
        word_meaning = str(row['单词释义']).strip() if pd.notna(row['单词释义']) else ''
        example = str(row['例句']).strip() if pd.notna(row['例句']) and row['例句'] != '' else ''
        source = str(row['来源']).strip() if pd.notna(row['来源']) else ''
        
        if not word or word == 'nan':
            continue
        
        # 判断正确的词根
        correct_root = get_root_for_word(word)
        
        # 如果没有匹配的前缀，归类为"其他常用词"
        if correct_root is None:
            correct_root = '其他常用词'
        
        # 获取词根含义
        if correct_root.startswith('co-'):
            root_meaning = '共同、一起'
        elif correct_root.startswith('de-'):
            root_meaning = '向下、离开'
        elif correct_root.startswith('pro-'):
            root_meaning = '向前、赞成'
        elif correct_root.startswith('pre-'):
            root_meaning = '预先、前'
        elif correct_root.startswith('ex-'):
            root_meaning = '出、外'
        elif correct_root == '其他常用词':
            root_meaning = '基础词汇'
        else:
            root_meaning = ''
        
        if correct_root not in roots_data:
            roots_data[correct_root] = {
                'name': correct_root,
                'meaning': root_meaning,
                'words': []
            }
        
        word_data = {
            'word': word,
            'meaning': word_meaning,
            'example': example,
            'source': source
        }
        roots_data[correct_root]['words'].append(word_data)
    
    # 转换为列表格式
    roots_list = list(roots_data.values())
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存主数据文件
    with open(output_path / 'data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'roots': roots_list,
            'totalWords': len(df),
            'totalWordsWithExamples': len([w for r in roots_list for w in r['words'] if w['example']])
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 词根分类修复完成")
    print(f"  - 词根数量: {len(roots_list)}")
    print(f"  - 总单词数: {len(df)}")
    print(f"  - 有例句的单词数: {len([w for r in roots_list for w in r['words'] if w['example']])}")
    
    # 显示一些例子
    print(f"\n前5个词根:")
    for i, root in enumerate(roots_list[:5]):
        print(f"  {i+1}. {root['name']}: {len(root['words'])} 个词")
        print(f"     前5个: {[w['word'] for w in root['words'][:5]]}")
    
    return roots_list

if __name__ == '__main__':
    excel_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类-完整例句版.xlsx'
    output_dir = '/Users/tongterence/Desktop/xianyu/material/website/data'
    
    fix_root_classification(excel_path, output_dir)
