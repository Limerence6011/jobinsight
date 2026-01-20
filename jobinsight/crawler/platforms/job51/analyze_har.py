#!/usr/bin/env python3
"""分析HAR文件，提取API接口和响应数据"""
import json
import sys
from pathlib import Path

def analyze_har(har_file: str):
    """分析HAR文件"""
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data['log']['entries']
    print(f"总请求数: {len(entries)}")
    
    # 查找API请求
    api_entries = []
    for entry in entries:
        url = entry['request']['url']
        if 'api/job/search' in url:
            api_entries.append(entry)
    
    print(f"\n找到 {len(api_entries)} 个API请求")
    
    # 分析每个API请求
    for i, entry in enumerate(api_entries, 1):
        print(f"\n{'='*80}")
        print(f"API请求 #{i}")
        print(f"{'='*80}")
        
        req = entry['request']
        resp = entry['response']
        
        print(f"\n请求URL: {req['url']}")
        print(f"请求方法: {req['method']}")
        print(f"响应状态: {resp['status']}")
        print(f"响应类型: {resp.get('content', {}).get('mimeType', 'unknown')}")
        
        # 提取请求参数
        print("\n请求参数:")
        for param in req.get('queryString', []):
            print(f"  {param['name']}: {param['value']}")
        
        # 提取请求头
        print("\n重要请求头:")
        important_headers = ['sign', 'uuid', 'From-Domain', 'partner', 'property']
        for header in req.get('headers', []):
            if header['name'] in important_headers:
                value = header['value']
                if len(value) > 100:
                    value = value[:100] + '...'
                print(f"  {header['name']}: {value}")
        
        # 提取响应内容
        content = resp.get('content', {})
        text = content.get('text', '')
        mime_type = content.get('mimeType', '')
        
        print(f"\n响应内容类型: {mime_type}")
        print(f"响应内容长度: {len(text)} 字符")
        
        # 如果是JSON响应，尝试解析
        if 'application/json' in mime_type or text.strip().startswith('{'):
            try:
                data = json.loads(text)
                print("\n响应JSON结构:")
                print(f"  顶层键: {list(data.keys())}")
                
                # 查找职位数据
                if 'resultBody' in data:
                    result = data['resultBody']
                    print(f"  resultBody类型: {type(result)}")
                    if isinstance(result, dict):
                        print(f"  resultBody键: {list(result.keys())}")
                        if 'jobList' in result:
                            job_list = result['jobList']
                            print(f"  jobList类型: {type(job_list)}")
                            if isinstance(job_list, list):
                                print(f"  职位数量: {len(job_list)}")
                                if len(job_list) > 0:
                                    print(f"  第一个职位键: {list(job_list[0].keys())}")
                                    print(f"  第一个职位示例: {json.dumps(job_list[0], ensure_ascii=False, indent=2)[:500]}")
                
                # 保存JSON到文件
                output_file = f"api_response_{i}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n  已保存完整响应到: {output_file}")
                
            except json.JSONDecodeError:
                print("\n  响应不是有效的JSON")
                print(f"  响应预览: {text[:500]}")
        else:
            print(f"\n响应预览: {text[:500]}")

if __name__ == '__main__':
    har_file = 'we.51job.com_Archive [26-01-19 22-48-21].har'
    if not Path(har_file).exists():
        print(f"错误: 找不到文件 {har_file}")
        sys.exit(1)
    
    analyze_har(har_file)
