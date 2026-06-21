"""测试播客文案生成功能"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_generate_podcast():
    """测试生成播客文案"""
    
    # 首先获取素材列表
    print("=" * 60)
    print("步骤1: 获取素材列表")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/writing/podcast-materials")
    if response.status_code != 200:
        print(f"❌ 获取素材列表失败: {response.text}")
        return
    
    data = response.json()
    materials = data.get('materials', [])
    
    if not materials:
        print("❌ 没有可用的素材，请先在写作训练中生成并导入素材")
        return
    
    print(f"✅ 找到 {len(materials)} 个素材")
    for i, mat in enumerate(materials[:3], 1):
        print(f"  {i}. [{mat['stage']}] {mat['topic']} - {mat['ai_model']}")
    
    # 选择前2个素材进行测试
    selected_ids = [m['id'] for m in materials[:2]]
    
    print("\n" + "=" * 60)
    print("步骤2: 生成播客文案")
    print("=" * 60)
    print(f"选中的素材ID: {selected_ids}")
    
    payload = {
        "material_ids": selected_ids,
        "prompt": "请将这些素材整理成一段播客对话，风格轻松有趣",
        "model": "qwen3:8b"
    }
    
    print("\n发送请求...")
    try:
        response = requests.post(
            f"{BASE_URL}/writing/podcast-generate",
            json=payload,
            timeout=300  # 5分钟超时
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 生成成功！")
            print(f"AI模型: {result.get('ai_model')}")
            print(f"素材数量: {result.get('materials_count')}")
            print(f"\n生成的播客文案（前500字）:")
            print("-" * 60)
            script = result.get('script', '')
            print(script[:500] + "..." if len(script) > 500 else script)
        else:
            print(f"\n❌ 请求失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时（300秒），LLM生成可能需要更长时间")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    test_generate_podcast()
