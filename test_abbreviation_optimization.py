"""
测试英文缩写读音优化
验证按字母读音和中文音译的正确性
"""

from podcast.text_preprocessor import preprocess_text

print("=" * 80)
print("英文缩写读音优化测试")
print("=" * 80)

# 测试1：按字母读音的缩写（应该被拆分为单个字母）
print("\n[测试1] 按字母读音的缩写")
print("-" * 80)

test_cases_letters = [
    "AI技术正在改变世界",
    "CEO表示公司业绩良好",
    "NASA发布了新的太空计划",
    "GDP增长5%，CPI下降2%",
    "这个API需要认证才能使用",
    "WiFi密码是多少？",
    "CPU和GPU的性能都很重要",
]

for test in test_cases_letters:
    result = preprocess_text(test)
    print(f"原始: {test}")
    print(f"处理: {result}")
    print()

# 测试2：翻译为中文音译的专有名词
print("\n[测试2] 翻译为中文音译的专有名词")
print("-" * 80)

test_cases_chinese = [
    "Python是最流行的编程语言",
    "Java在企业级应用中很常见",
    "使用Excel制作表格",
    "Word文档已经保存",
    "PowerPoint演示文稿很精彩",
    "iPhone的设计很优雅",
    "Windows系统需要更新",
]

for test in test_cases_chinese:
    result = preprocess_text(test)
    print(f"原始: {test}")
    print(f"处理: {result}")
    print()

# 测试3：混合内容（序号+缩写+数字）
print("\n[测试3] 混合内容（复杂场景）")
print("-" * 80)

mixed_text = """
1. 首先，2024年GDP增长5%，CEO表示AI技术很重要。
2、其次，NASA发布了新的计划，预计投资100亿元。
(1) 第1步：准备材料，包括PDF文档和USB设备。
"""

print(f"原始:\n{mixed_text}")
print(f"\n处理后:\n{preprocess_text(mixed_text)}")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)
print("\n💡 预期结果：")
print("1. AI → A I（按字母读，而不是'爱'）")
print("2. CEO → C E O（按字母读，而不是'首席执行官'）")
print("3. Python → 派森（中文音译）")
print("4. GDP → G D P（按字母读）")
print("5. PDF → P D F（按字母读）")
