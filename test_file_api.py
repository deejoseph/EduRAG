"""
测试文件访问API
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_list_files():
    """测试列出文件API"""
    print("📋 测试列出PDF文件...")
    try:
        response = requests.get(f"{BASE_URL}/api/search/files/list?type=pdf&recursive=false")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 共 {data['total']} 个文件")
            if data['files']:
                print(f"前3个文件:")
                for f in data['files'][:3]:
                    print(f"  - {f['name']} ({f['size']} bytes)")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_serve_file():
    """测试文件服务API"""
    print("\n📄 测试文件访问...")
    # 使用一个已知存在的文件名
    test_filename = "高考满分作文精选39篇.pdf"
    try:
        url = f"{BASE_URL}/api/search/files/pdfs/{test_filename}"
        print(f"请求URL: {url}")
        response = requests.get(url, stream=True)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"✅ 成功! Content-Type: {content_type}")
            print(f"文件大小: {len(response.content)} bytes")
        else:
            print(f"❌ 失败: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("文件访问API测试")
    print("=" * 60)
    
    # 先检查后端是否运行
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ 后端服务运行正常\n")
    except:
        print("❌ 后端服务未运行，请先启动后端服务")
        print("   运行命令: python start_backend.py")
        exit(1)
    
    test_list_files()
    test_serve_file()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
