#!/usr/bin/env python3
"""查看职位数据结构"""
import json

with open('api_response_2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['resultbody']['job']['items']
print(f'职位数量: {len(items)}')
print('\n第一个职位字段:')
job = items[0]
print(f'  jobId: {job.get("jobId")}')
print(f'  jobName: {job.get("jobName")}')
print(f'  companyName: {job.get("companyName")}')
print(f'  jobAreaString: {job.get("jobAreaString")}')
print(f'  provideSalaryString: {job.get("provideSalaryString")}')
print(f'  workYearString: {job.get("workYearString")}')
print(f'  degreeString: {job.get("degreeString")}')
print(f'  jobHref: {job.get("jobHref")}')
print(f'  jobTags: {job.get("jobTags", [])[:5]}')
print(f'  jobDescribe: {job.get("jobDescribe", "")[:100]}...')
