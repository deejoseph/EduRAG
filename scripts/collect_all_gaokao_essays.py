"""
完整高考作文题目采集脚本 - 采集2013-2026年所有年份数据
目标网站: https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin
import re
from pathlib import Path

# 配置
BASE_URL = "https://gaokao.eol.cn"
MAIN_PAGE = "https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml"
OUTPUT_DIR = Path("data/gaokao_essays")
OUTPUT_FILE = OUTPUT_DIR / "all_gaokao_topics_complete.json"

# 创建目录
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# HTTP会话
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})


def fetch_page(url):
    """获取页面内容"""
    try:
        response = session.get(url, timeout=30)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None


def collect_all_years():
    """采集所有年份的高考作文题目"""
    print("=" * 80)
    print("开始采集2013-2026年高考作文题目...")
    print("=" * 80)
    
    # 从主索引页面获取所有作文链接
    print("\n从主索引页面获取所有作文链接...")
    html = fetch_page(MAIN_PAGE)
    if not html:
        print("❌ 无法获取主索引页面")
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    
    # 筛选作文相关链接
    essay_links = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        
        # 只保留包含zuowen或jiqiao的链接
        if 'zuowen' in href or 'jiqiao' in href:
            # 跳过解析类文章（通常标题是"解析"）
            if text == '解析' or text == '':
                continue
            
            essay_links.append({
                'title': text,
                'url': urljoin(BASE_URL, href) if not href.startswith('http') else href
            })
    
    print(f"✅ 找到 {len(essay_links)} 个作文相关链接")
    
    # 按年份分组
    years_dict = {}
    
    for item in essay_links:
        url = item['url']
        title = item['title']
        
        # 从URL中提取年份 (例如: /202606/ -> 2026)
        year_match = re.search(r'/(\d{4})\d{2}/', url)
        if not year_match:
            continue
        
        year = year_match.group(1)
        
        # 只处理2013-2026年
        if int(year) < 2013 or int(year) > 2026:
            continue
        
        if year not in years_dict:
            years_dict[year] = []
        
        # 提取地区信息
        region_keywords = [
            '全国I卷', '全国II卷', '全国甲卷', '全国乙卷',
            '新高考I卷', '新高考II卷',
            '北京', '天津', '上海', '浙江', '江苏', 
            '山东', '广东', '湖南', '湖北', '河北',
            '河南', '安徽', '江西', '四川', '重庆',
            '福建', '辽宁', '陕西', '广西', '贵州',
            '云南', '甘肃', '青海', '宁夏', '新疆',
            '西藏', '内蒙古', '海南', '黑龙江', '吉林',
            '山西'
        ]
        
        region = "未知"
        for keyword in region_keywords:
            if keyword in title:
                region = keyword
                break
        
        # 如果标题中包含地区，但还没匹配到，尝试从URL判断
        if region == "未知":
            url_lower = url.lower()
            if 'beijing' in url_lower or 'bei_jing' in url_lower:
                region = '北京'
            elif 'tianjin' in url_lower or 'tian_jin' in url_lower:
                region = '天津'
            elif 'shanghai' in url_lower or 'shang_hai' in url_lower:
                region = '上海'
            elif 'zhejiang' in url_lower or 'zhe_jiang' in url_lower:
                region = '浙江'
            elif 'jiangsu' in url_lower or 'jiang_su' in url_lower:
                region = '江苏'
            elif 'shandong' in url_lower or 'shan_dong' in url_lower:
                region = '山东'
            elif 'guangdong' in url_lower or 'guang_dong' in url_lower:
                region = '广东'
            elif 'hunan' in url_lower:
                region = '湖南'
            elif 'hubei' in url_lower:
                region = '湖北'
            elif 'hebei' in url_lower:
                region = '河北'
            elif 'henan' in url_lower:
                region = '河南'
            elif 'anhui' in url_lower:
                region = '安徽'
            elif 'jiangxi' in url_lower:
                region = '江西'
            elif 'sichuan' in url_lower:
                region = '四川'
            elif 'chongqing' in url_lower:
                region = '重庆'
            elif 'fujian' in url_lower:
                region = '福建'
            elif 'liaoning' in url_lower:
                region = '辽宁'
            elif 'shaanxi' in url_lower or ('shan' in url_lower and 'x' in url_lower):
                region = '陕西'
            elif 'shanxi' in url_lower:
                region = '山西'
            elif 'guangxi' in url_lower:
                region = '广西'
            elif 'guizhou' in url_lower:
                region = '贵州'
            elif 'yunnan' in url_lower:
                region = '云南'
            elif 'gansu' in url_lower:
                region = '甘肃'
            elif 'qinghai' in url_lower:
                region = '青海'
            elif 'ningxia' in url_lower:
                region = '宁夏'
            elif 'xinjiang' in url_lower:
                region = '新疆'
            elif 'neimenggu' in url_lower or 'nei_meng_gu' in url_lower:
                region = '内蒙古'
            elif 'hainan' in url_lower:
                region = '海南'
            elif 'heilongjiang' in url_lower:
                region = '黑龙江'
            elif 'jilin' in url_lower:
                region = '吉林'
            elif 'xizang' in url_lower or 'xi_zang' in url_lower:
                region = '西藏'
        
        essay_info = {
            "region": region,
            "title": title,
            "url": url,
            "has_sample_essay": False
        }
        
        years_dict[year].append(essay_info)
    
    # 构建最终数据结构
    years_data = []
    total_essays = 0
    
    for year in sorted(years_dict.keys(), reverse=True):
        essays = years_dict[year]
        if essays:
            print(f"{year}年: {len(essays)}条作文题目")
            total_essays += len(essays)
            
            # 构造该年份的主URL
            main_url = f"https://gaokao.eol.cn/e_html/gk/mfzw/{year}.shtml"
            
            year_data = {
                "year": year,
                "main_url": main_url,
                "essays": essays
            }
            years_data.append(year_data)
    
    result = {
        "years": years_data,
        "total_years": len(years_data),
        "total_essays": total_essays,
        "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": MAIN_PAGE
    }
    
    # 保存JSON文件
    print(f"\n{'='*80}")
    print(f"保存数据...")
    print(f"{'='*80}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 采集完成！")
    print(f"📊 总计: {len(years_data)} 个年份, {total_essays} 条作文题目")
    print(f"💾 文件保存至: {OUTPUT_FILE.absolute()}")
    
    # 打印统计信息
    print(f"\n{'='*80}")
    print("详细统计:")
    print(f"{'='*80}")
    for year_data in years_data:
        year = year_data['year']
        count = len(year_data['essays'])
        regions = list(set([e['region'] for e in year_data['essays']]))
        print(f"{year}年: {count}条 | 地区: {', '.join(regions[:5])}{'...' if len(regions) > 5 else ''}")
    
    return result


if __name__ == '__main__':
    try:
        collect_all_years()
    except Exception as e:
        print(f"\n❌ 采集过程中出错: {e}")
        import traceback
        traceback.print_exc()
