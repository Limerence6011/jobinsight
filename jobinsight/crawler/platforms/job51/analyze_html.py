#!/usr/bin/env python3
"""分析HTML文件，查找职位列表结构"""
import re
from bs4 import BeautifulSoup
from pathlib import Path

html_file = Path('【C(全文)招聘，求职】-前程无忧_C.htm')
if not html_file.exists():
    print(f"文件不存在: {html_file}")
    exit(1)

print(f"分析文件: {html_file}")
with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

print(f"文件大小: {len(html)} 字符")
soup = BeautifulSoup(html, 'html.parser')

# 查找所有链接
all_links = soup.find_all('a', href=True)
print(f"\n总链接数: {len(all_links)}")

# 查找职位相关链接
job_links = []
for link in all_links:
    href = link.get('href', '')
    if re.search(r'/jobs/\d+|/job/\d+|jobId=|jobid=', href, re.I):
        job_links.append((href, link.get_text(strip=True)[:50]))

print(f"\n职位相关链接: {len(job_links)}")
for i, (href, text) in enumerate(job_links[:10], 1):
    print(f"  {i}. {href[:80]} - {text}")

# 查找包含职位的div
divs_with_job = []
for div in soup.find_all('div'):
    text = div.get_text()
    href = div.find('a', href=re.compile(r'/jobs/\d+', re.I))
    if href or ('职位' in text and '公司' in text and len(text) < 500):
        classes = div.get('class', [])
        divs_with_job.append((classes, text[:100]))

print(f"\n可能的职位div: {len(divs_with_job)}")
for i, (classes, text) in enumerate(divs_with_job[:5], 1):
    print(f"  {i}. class={classes}, text={text}")

# 查找script标签中的JSON数据
scripts = soup.find_all('script')
print(f"\nScript标签数: {len(scripts)}")
for i, script in enumerate(scripts):
    content = script.string or ''
    if 'job' in content.lower() and ('{' in content or '[' in content):
        if len(content) > 100:
            print(f"\nScript {i+1} (长度: {len(content)}):")
            # 查找JSON对象
            json_match = re.search(r'\{[^{}]*"job"[^{}]*\}', content, re.I)
            if json_match:
                print(f"  找到可能的JSON: {json_match.group()[:200]}")
