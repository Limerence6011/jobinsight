#!/usr/bin/env python3
"""测试代理连接"""
import requests
import sys

def test_proxy(proxy_url):
    """测试代理是否可用"""
    print(f"测试代理: {proxy_url}")
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }
    
    try:
        # 测试访问一个简单的网站
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10, verify=False)
        print(f"[OK] 代理连接成功")
        print(f"响应: {response.text[:200]}")
        return True
    except requests.exceptions.ProxyError as e:
        print(f"[ERROR] 代理连接失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 其他错误: {e}")
        return False

def test_remoteok_with_proxy(proxy_url):
    """测试通过代理访问 RemoteOK API"""
    print(f"\n测试通过代理访问 RemoteOK API...")
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        }
        response = requests.get('https://remoteok.com/api', headers=headers, 
                              proxies=proxies, timeout=20, verify=False)
        response.raise_for_status()
        print(f"[OK] RemoteOK API 访问成功")
        print(f"响应长度: {len(response.text)} 字符")
        return True
    except Exception as e:
        print(f"[ERROR] RemoteOK API 访问失败: {e}")
        return False

if __name__ == "__main__":
    proxy_url = "http://127.0.0.1:7897"
    
    print("=" * 50)
    print("代理连接测试")
    print("=" * 50)
    
    # 测试基本代理连接
    proxy_ok = test_proxy(proxy_url)
    
    if proxy_ok:
        # 测试 RemoteOK
        remoteok_ok = test_remoteok_with_proxy(proxy_url)
        
        if remoteok_ok:
            print("\n[SUCCESS] 代理配置正确，可以正常使用！")
            sys.exit(0)
        else:
            print("\n[WARNING] 代理可用，但无法访问 RemoteOK，可能需要检查网络或代理设置")
            sys.exit(1)
    else:
        print("\n[FAILED] 代理连接失败，请检查：")
        print("  1. 代理服务器是否在 127.0.0.1:7897 运行")
        print("  2. 代理类型是否正确（HTTP/HTTPS/SOCKS5）")
        print("  3. 防火墙是否阻止了连接")
        sys.exit(1)
