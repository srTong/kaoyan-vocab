#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为考研英语词汇添加真题例句 - 合并版本
"""

import pandas as pd
import sys
sys.path.append('/Users/tongterence/Desktop/xianyu')
from kaoyan_examples_db import KAoyAN_EXAMPLES
from kaoyan_examples_db_part2 import MORE_EXAMPLES

def main():
    # 合并两个数据库
    all_examples = {**KAoyAN_EXAMPLES, **MORE_EXAMPLES}
    
    # 读取原始 Excel 文件
    excel_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类.xlsx'
    output_path = '/Users/tongterence/Desktop/xianyu/material/研究生英语/考研英语词汇-词根分类-带例句.xlsx'
    
    print("正在读取 Excel 文件...")
    df = pd.read_excel(excel_path)
    print(f"共读取 {len(df)} 个单词")
    
    # 添加例句和来源列
    examples = []
    sources = []
    
    matched_count = 0
    
    for _, row in df.iterrows():
        word = str(row['单词']).strip().lower()
        
        if word in all_examples:
            examples.append(all_examples[word]['example'])
            sources.append(all_examples[word]['source'])
            matched_count += 1
        else:
            examples.append('')
            sources.append('')
    
    df['例句'] = examples
    df['来源'] = sources
    
    print(f"\n匹配结果：")
    print(f"成功匹配例句的单词数: {matched_count}")
    print(f"未匹配到例句的单词数: {len(df) - matched_count}")
    print(f"覆盖率: {matched_count / len(df) * 100:.1f}%")
    
    # 保存新的 Excel 文件
    print(f"\n正在保存到 {output_path}...")
    df.to_excel(output_path, index=False)
    
    print("\n完成！")
    print(f"\n前10个有例句的单词示例：")
    df_with_examples = df[df['例句'] != ''].head(10)
    for _, row in df_with_examples.iterrows():
        print(f"\n单词: {row['单词']}")
        print(f"例句: {row['例句']}")
        print(f"来源: {row['来源']}")

if __name__ == '__main__':
    main()
