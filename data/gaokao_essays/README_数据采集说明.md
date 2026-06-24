# 高考作文题目数据采集说明

## 📊 数据概况

**文件路径**: `d:\PixelSmile\EduRAG\data\gaokao_essays\all_gaokao_topics_complete.json`

**采集时间**: 2026-06-24

**数据来源**: https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml

## 📈 数据统计

- **总年份数**: 11个年份（2015-2026，缺少2019、2014、2013）
- **总作文数**: 239条
- **已知地区**: 119条
- **未知地区**: 120条（主要是范文标题，非原始作文题目）

### 各年份分布

| 年份 | 作文数量 | 已知地区 | 未知地区 |
|------|---------|---------|---------|
| 2026 | 7条 | 0 | 7 |
| 2025 | 5条 | 0 | 5 |
| 2024 | 7条 | 5 | 2 |
| 2023 | 8条 | 1 | 7 |
| 2022 | 18条 | 4 | 14 |
| 2021 | 24条 | 14 | 10 |
| 2020 | 22条 | 4 | 18 |
| 2018 | 35条 | 17 | 18 |
| 2017 | 7条 | 0 | 7 |
| 2016 | 100条 | 74 | 26 |
| 2015 | 6条 | 0 | 6 |

## 📝 数据结构

```json
{
  "years": [
    {
      "year": "2026",
      "main_url": "https://gaokao.eol.cn/e_html/gk/mfzw/2026.shtml",
      "essays": [
        {
          "region": "全国I卷",
          "title": "对词语理解的变化",
          "url": "https://gaokao.eol.cn/zuowen/jiqiao/202606/t20260607_2741913.shtml",
          "has_sample_essay": false
        }
      ]
    }
  ],
  "total_years": 11,
  "total_essays": 239,
  "collection_date": "2026-06-24 00:42:59",
  "source": "https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml"
}
```

## ⚠️ 注意事项

1. **地区识别**: 部分数据的地区显示为"未知"，这是因为采集的是范文标题而非原始作文题目标题。可以通过访问每个URL页面来获取更准确的地区信息。

2. **年份覆盖**: 目前采集到11个年份的数据，缺少2019、2014、2013年的数据。这些年份可能在网站上没有专门的页面或链接结构不同。

3. **数据类型**: 采集的数据包含作文题目和范文，其中"未知"地区的多为范文标题。

4. **编码格式**: JSON文件使用UTF-8编码，所有中文内容正确保存，可以使用Python的`json.load()`直接读取。

## 🔧 使用方法

```python
import json

# 读取数据
with open('data/gaokao_essays/all_gaokao_topics_complete.json', encoding='utf-8') as f:
    data = json.load(f)

# 遍历所有年份
for year_data in data['years']:
    year = year_data['year']
    print(f"\n{year}年高考作文:")
    
    for essay in year_data['essays']:
        print(f"  - [{essay['region']}] {essay['title']}")
        print(f"    URL: {essay['url']}")
```

## 📌 后续优化建议

1. **完善地区识别**: 访问每个URL页面，从页面标题或内容中提取准确的地区信息
2. **补充缺少年份**: 检查2019、2014、2013年的数据是否存在其他URL模式
3. **区分题目和范文**: 添加字段标识是原始作文题目还是范文
4. **增加作文内容**: 可以进一步爬取每个页面的作文内容和范文内容

## ✅ 验证状态

- ✅ JSON格式有效，可被Python的json模块解析
- ✅ 数据结构完整，包含所有必需字段
- ✅ 中文编码正确（使用ensure_ascii=False）
- ✅ 文件可以被正常读取和处理
