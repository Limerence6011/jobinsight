#!/usr/bin/env python3
"""测试解析HTML文件，查找职位列表结构"""
import os
import re
from bs4 import BeautifulSoup
from pathlib import Path

# 查找HTML文件
html_dir = Path(__file__).parent
html_files = [f for f in html_dir.glob('*.htm')]

if not html_files:
    print("未找到HTML文件")
    exit(1)

html_file = html_files[0]
print(f"分析文件: {html_file.name}")

# 读取HTML内容
with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
    html_content = f.read()

print(f"文件大小: {len(html_content)} 字符")

# 解析HTML
soup = BeautifulSoup(html_content, 'html.parser')

# 查找所有链接
all_links = soup.find_all('a', href=True)
print(f"\n总链接数: {len(all_links)}")

# 查找可能的职位链接
job_links = []
for link in all_links:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    if re.search(r'job|position|职位|岗位|招聘', href, re.I) or re.search(r'job|position|职位|岗位|招聘', text, re.I):
        job_links.append((href, text))

print(f"\n可能的职位链接: {len(job_links)}")
for i, (href, text) in enumerate(job_links[:10]):
    print(f"  {i+1}. {href[:80]} - {text[:50]}")

# 查找包含特定类名的div
divs_with_job = soup.find_all('div', class_=lambda x: x and ('job' in str(x).lower() or 'item' in str(x).lower() or 'card' in str(x).lower()))
print(f"\n包含job/item/card的div: {len(divs_with_job)}")

# 查找script标签中的JSON数据
scripts = soup.find_all('script')
print(f"\nScript标签数: {len(scripts)}")
for i, script in enumerate(scripts):
    content = script.string or ''
    if 'job' in content.lower() or 'position' in content.lower() or 'data' in content.lower():
        if len(content) > 100:
            print(f"\nScript {i+1} (长度: {len(content)}):")
            print(content[:500])

# 查找可能的职位列表容器
possible_containers = soup.find_all(['div', 'ul', 'section'], class_=lambda x: x and ('list' in str(x).lower() or 'result' in str(x).lower() or 'search' in str(x).lower()))
print(f"\n可能的列表容器: {len(possible_containers)}")
for i, container in enumerate(possible_containers[:5]):
    classes = container.get('class', [])
    print(f"  容器 {i+1}: class={classes}, 子元素数={len(container.find_all())}")
