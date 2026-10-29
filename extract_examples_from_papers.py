#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从考研英语真题中提取例句并匹配到词汇表
"""

import pandas as pd
import re
import os
from pathlib import Path

def extract_text_from_md(md_file):
    """从 Markdown 文件中提取英语文本"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有英语句子（包含至少3个单词的行）
    lines = content.split('\n')
    sentences = []
    
    for line in lines:
        line = line.strip()
        # 跳过空行、标题、中文行
        if not line or line.startswith('#') or any('\u4e00' <= char <= '\u9fff' for char in line):
            continue
        
        # 提取英语句子
        if len(line.split()) >= 3:
            # 清理句子
            sentence = re.sub(r'\[.*?\]', '', line)  # 移除选项标记
            sentence = re.sub(r'\d+\.', '', sentence)  # 移除题号
            sentence = sentence.strip()
            
            if sentence and len(sentence.split()) >= 3:
                sentences.append(sentence)
    
    return sentences

def extract_examples_from_all_papers(papers_dir):
    """从所有真题文件中提取例句"""
    all_examples = {}
    
    solutions_dir = Path(papers_dir) / 'solutions'
    
    for year_dir in solutions_dir.iterdir():
        if year_dir.is_dir():
            year = year_dir.name
            for md_file in year_dir.glob('*.md'):
                print(f"处理 {year} 年真题...")
                sentences = extract_text_from_md(md_file)
                
                for sentence in sentences:
                    # 提取句子中的单词
                    words = re.findall(r'\b[a-z]+\b', sentence.lower())
                    
                    for word in words:
                        if word not in all_examples:
                            all_examples[word] = {
                                'example': sentence,
                                'source': f'{year}年真题'
                            }
    
    return all_examples

def main():
    papers_dir = '/Users/tongterence/Desktop/xianyu/Kaoyan-English1-Papers'
    excel_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类.xlsx'
    output_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类-完整例句版.xlsx'
    
    print("正在从真题中提取例句...")
    examples_from_papers = extract_examples_from_all_papers(papers_dir)
    print(f"从真题中提取了 {len(examples_from_papers)} 个单词的例句")
    
    print("\n正在读取 Excel 文件...")
    df = pd.read_excel(excel_path)
    print(f"共读取 {len(df)} 个单词")
    
    # 匹配例句
    examples = []
    sources = []
    matched_count = 0
    
    for _, row in df.iterrows():
        word = str(row['单词']).strip().lower()
        
        if word in examples_from_papers:
            examples.append(examples_from_papers[word]['example'])
            sources.append(examples_from_papers[word]['source'])
            matched_count += 1
        else:
            examples.append('')
            sources.append('')
    
    df['例句'] = examples
    df['来源'] = sources
    
    print(f"\n匹配结果：")
    print(f"成功匹配例句的单词数: {matched_count}")
    print(f"覆盖率: {matched_count / len(df) * 100:.1f}%")
    
    # 保存
    print(f"\n正在保存到 {output_path}...")
    df.to_excel(output_path, index=False)
    
    print("\n完成！")
    
    # 显示示例
    print(f"\n前10个有例句的单词示例：")
    df_with_examples = df[df['例句'] != ''].head(10)
    for _, row in df_with_examples.iterrows():
        print(f"\n单词: {row['单词']}")
        print(f"例句: {row['例句'][:80]}...")
        print(f"来源: {row['来源']}")

if __name__ == '__main__':
    main()
