"""
测试 LongCat-AudioDiT TTS 功能
验证模型加载和语音生成是否正常
"""

import os
import sys
from pathlib import Path

# 设置镜像加速
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("=" * 80)
print("LongCat-AudioDiT TTS 测试脚本")
print("=" * 80)

# 1. 检查 LongCat 项目是否存在
print("\n[步骤1] 检查 LongCat-AudioDiT 项目...")
longcat_dir = Path("C:/LongCat/LongCat-AudioDiT")
if not longcat_dir.exists():
    print(f"❌ LongCat 项目不存在: {longcat_dir}")
    sys.exit(1)

inference_script = longcat_dir / "inference.py"
if not inference_script.exists():
    print(f"❌ 推理脚本不存在: {inference_script}")
    sys.exit(1)

print(f"✅ LongCat 项目存在: {longcat_dir}")
print(f"✅ 推理脚本存在: {inference_script}")

# 2. 检查参考音频文件
print("\n[步骤2] 检查参考音频...")
ref_audio_path = Path("C:/LongCat/gptsovits_audio.wav")
if not ref_audio_path.exists():
    print(f"⚠️  参考音频不存在: {ref_audio_path}")
    print("   请准备一个3-8秒的清晰音频文件作为参考")
    print("   建议格式: WAV, 采样率 24kHz, 单声道")
    
    # 尝试查找其他音频文件
    wav_files = list(longcat_dir.glob("*.wav"))
    if wav_files:
        print(f"\n   找到以下音频文件:")
        for i, f in enumerate(wav_files[:5], 1):
            print(f"   {i}. {f.name}")
        ref_audio_path = wav_files[0]
        print(f"\n   使用第一个音频文件: {ref_audio_path.name}")
    else:
        print("\n❌ 没有找到可用的参考音频文件")
        sys.exit(1)
else:
    print(f"✅ 参考音频存在: {ref_audio_path.name}")

# 3. 测试文本预处理
print("\n[步骤3] 测试文本预处理模块...")
try:
    from podcast.text_preprocessor import preprocess_text, smart_split_text
    
    test_text = "2024年GDP增长5%，CEO表示AI技术很重要。这是一个测试句子，用于验证多音字和英文缩写处理。"
    
    print(f"原始文本: {test_text}")
    processed = preprocess_text(test_text)
    print(f"处理后:   {processed}")
    
    segments = smart_split_text(processed, max_chars=40)
    print(f"\n智能分句结果（共{len(segments)}段）:")
    for i, seg in enumerate(segments, 1):
        print(f"  {i}. {seg} (长度: {len(seg)})")
    
    print("✅ 文本预处理模块正常")
    
except Exception as e:
    print(f"❌ 文本预处理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试 TTS 生成器初始化
print("\n[步骤4] 测试 TTS 生成器初始化...")
try:
    from podcast.tts_generator import get_tts_generator
    
    tts_gen = get_tts_generator(
        longcat_dir=str(longcat_dir),
        model_dir="meituan-longcat/LongCat-AudioDiT-1B",
        output_dir="./data/podcast_audio/"
    )
    
    print(f"✅ TTS 生成器初始化成功")
    print(f"   LongCat 目录: {tts_gen.longcat_dir}")
    print(f"   输出目录: {tts_gen.output_dir}")
    
except Exception as e:
    print(f"❌ TTS 生成器初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试模型加载（可选，需要用户确认）
print("\n[步骤5] 测试模型加载...")
print("⚠️  注意：首次运行会从 Hugging Face 下载模型（约5.68GB）")
print("   已设置镜像加速: https://hf-mirror.com")
print("   预计下载时间: 10-30分钟（取决于网络速度）")

user_input = input("\n是否开始下载并测试模型？(y/n): ")
if user_input.lower() != 'y':
    print("⏭️  跳过模型加载测试")
    print("\n你可以稍后手动运行此脚本进行完整测试")
    sys.exit(0)

# 6. 执行实际的 TTS 测试
print("\n[步骤6] 执行 TTS 测试...")
test_prompt_text = "这是一个测试音频"
test_target_text = "你好，世界。这是语音克隆测试。"

try:
    print(f"参考音频: {ref_audio_path.name}")
    print(f"参考文本: {test_prompt_text}")
    print(f"目标文本: {test_target_text}")
    print("\n开始生成语音...")
    
    output_path = tts_gen.generate_speech(
        text=test_target_text,
        ref_audio_path=str(ref_audio_path),
        prompt_text=test_prompt_text,
        output_filename="test_output.wav",
        nfe=18,
        guidance_strength=3.5,
        enable_split=False,  # 短文本不分段
    )
    
    print(f"\n✅ TTS 测试成功！")
    print(f"   输出文件: {output_path}")
    print(f"   文件大小: {Path(output_path).stat().st_size / 1024:.2f} KB")
    
    # 计算时长
    import soundfile as sf
    data, sr = sf.read(output_path)
    duration = len(data) / sr
    print(f"   音频时长: {duration:.2f} 秒")
    
except Exception as e:
    print(f"\n❌ TTS 生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("所有测试完成！✅")
print("=" * 80)
