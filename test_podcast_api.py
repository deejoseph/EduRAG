"""
测试播客模块API功能
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_multi_ai_analyze():
    """测试多AI审题分析"""
    print("=" * 60)
    print("测试1: 多AI审题分析")
    print("=" * 60)
    
    data = {
        "topic": "人工智能与未来",
        "models": ["qwen3:8b", "gemma3:4b"],  # 使用2个差异化模型
        "grade_level": "高中"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/writing/multi-ai/analyze",
            json=data,
            timeout=300  # 增加到300秒（5分钟）
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('success'):
            print(f"\n✅ 成功！返回了 {result.get('count', 0)} 个AI的结果")
        else:
            print(f"\n❌ 失败: {result.get('error')}")
            
    except requests.exceptions.Timeout:
        print(f"\n⚠️  请求超时（300秒），LLM生成可能需要较长时间")
        print(f"💡 建议：")
        print(f"   1. 确保Ollama服务正常运行: ollama serve")
        print(f"   2. 检查模型是否已下载: ollama list")
        print(f"   3. 首次使用模型需要加载，后续会更快")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_export_to_podcast():
    """测试导出素材到播客"""
    print("\n" + "=" * 60)
    print("测试2: 导出素材到播客模块")
    print("=" * 60)
    
    data = {
        "stage": "analysis",
        "topic": "测试题目",
        "content": "这是一段测试的审题分析内容",
        "ai_model": "test_model",
        "metadata": {"test": True}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/writing/export-to-podcast",
            json=data,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get('success'):
            material_id = result.get('material_id')
            print(f"\n✅ 成功！素材ID: {material_id}")
            return material_id
        else:
            print(f"\n❌ 失败: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_list_materials():
    """测试获取播客素材列表"""
    print("\n" + "=" * 60)
    print("测试3: 获取播客素材列表")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/writing/podcast-materials",
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            materials = result.get('materials', [])
            print(f"\n✅ 成功！共有 {len(materials)} 个素材")
            
            if materials:
                print("\n最近的3个素材:")
                for i, mat in enumerate(materials[:3], 1):
                    print(f"  {i}. [{mat.get('stage')}] {mat.get('topic')} - {mat.get('ai_model')}")
        else:
            print(f"\n❌ 失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")


if __name__ == "__main__":
    print("\n🚀 开始测试播客模块API\n")
    
    # 测试1: 多AI审题分析
    test_multi_ai_analyze()
    
    # 测试2: 导出素材到播客
    test_export_to_podcast()
    
    # 测试3: 获取素材列表
    test_list_materials()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
