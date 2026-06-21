"""
测试文本预处理优化
验证数字序号转换和灵活分段策略
"""

from podcast.text_preprocessor import preprocess_text, smart_split_text

print("=" * 80)
print("文本预处理优化测试")
print("=" * 80)

# 测试1：数字序号转换
print("\n[测试1] 数字序号转换")
print("-" * 80)

test_cases = [
    "1. 首先，我们要了解AI技术",
    "2、其次，分析GDP增长",
    "(1) 第一步是准备材料",
    "第2章介绍了CEO的职责",
    "第3步需要输入密码",
]

for test in test_cases:
    result = preprocess_text(test)
    print(f"原始: {test}")
    print(f"处理: {result}")
    print()

# 测试2：混合内容
print("\n[测试2] 混合内容（序号+英文缩写+数字）")
print("-" * 80)

mixed_text = """
1. 首先，2024年GDP增长5%，CEO表示AI技术很重要。
2、其次，NASA发布了新的计划，预计投资100亿元。
(1) 第1步：准备材料
(2) 第2步：提交申请
"""

print("原始文本:")
print(mixed_text)
print("\n处理后:")
processed = preprocess_text(mixed_text)
print(processed)

# 测试3：灵活分段策略
print("\n[测试3] 灵活分段策略对比")
print("-" * 80)

long_text = "人工智能技术的发展正在改变世界。首先，AI在医疗领域的应用越来越广泛。其次，自动驾驶技术也取得了重大突破。最后，教育领域的智能化转型也在加速推进。这是一个充满机遇和挑战的时代。"

print(f"原文长度: {len(long_text)} 字\n")

# 精准模式
segments_precise = smart_split_text(long_text, mode='precise')
print(f"精准模式 (30字/段): 共 {len(segments_precise)} 段")
for i, seg in enumerate(segments_precise, 1):
    print(f"  {i}. [{len(seg)}字] {seg}")

print()

# 标准模式
segments_standard = smart_split_text(long_text, mode='standard')
print(f"标准模式 (45字/段): 共 {len(segments_standard)} 段")
for i, seg in enumerate(segments_standard, 1):
    print(f"  {i}. [{len(seg)}字] {seg}")

print()

# 快速模式
segments_fast = smart_split_text(long_text, mode='fast')
print(f"快速模式 (60字/段): 共 {len(segments_fast)} 段")
for i, seg in enumerate(segments_fast, 1):
    print(f"  {i}. [{len(seg)}字] {seg}")

print("\n" + "=" * 80)
print("测试完成！✅")
print("=" * 80)
