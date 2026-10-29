#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Excel 数据转换为网站所需的 JSON 格式
"""

import pandas as pd
import json
from pathlib import Path

def convert_excel_to_json(excel_path, output_dir):
    """将 Excel 转换为 JSON 数据文件"""
    
    df = pd.read_excel(excel_path)
    
    # 填充词根列（向下填充）
    df['词根'] = df['词根'].fillna(method='ffill')
    df['词根含义'] = df['词根含义'].fillna(method='ffill')
    
    # 创建词根到单词的映射
    roots_data = {}
    
    for _, row in df.iterrows():
        root = str(row['词根']).strip()
        root_meaning = str(row['词根含义']).strip() if pd.notna(row['词根含义']) else ''
        word = str(row['单词']).strip()
        word_meaning = str(row['单词释义']).strip() if pd.notna(row['单词释义']) else ''
        example = str(row['例句']).strip() if pd.notna(row['例句']) and row['例句'] != '' else ''
        source = str(row['来源']).strip() if pd.notna(row['来源']) else ''
        
        if root not in roots_data:
            roots_data[root] = {
                'name': root,
                'meaning': root_meaning,
                'words': []
            }
        
        if word and word != 'nan':
            word_data = {
                'word': word,
                'meaning': word_meaning,
                'example': example,
                'source': source
            }
            roots_data[root]['words'].append(word_data)
    
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
    
    # 为每个词根创建单独的 JSON 文件（便于加载）
    for root_data in roots_list:
        root_filename = root_data['name'].replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
        with open(output_path / f'root_{root_filename}.json', 'w', encoding='utf-8') as f:
            json.dump(root_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 数据转换完成")
    print(f"  - 词根数量: {len(roots_list)}")
    print(f"  - 总单词数: {len(df)}")
    print(f"  - 有例句的单词数: {len([w for r in roots_list for w in r['words'] if w['example']])}")
    print(f"  - 输出目录: {output_path}")
    
    return roots_list

if __name__ == '__main__':
    excel_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类-完整例句版.xlsx'
    output_dir = '/Users/tongterence/Desktop/xianyu/kaoyan-vocab-site/data'
    
    convert_excel_to_json(excel_path, output_dir)
