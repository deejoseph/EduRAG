"""
高考作文题目和范文采集脚本
从 https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml 采集历年高考作文
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path

# 配置
BASE_URL = "https://gaokao.eol.cn"
MAIN_PAGE = "https://gaokao.eol.cn/e_html/gk/mfzw/index.shtml"
OUTPUT_DIR = Path("data/gaokao_essays")
PDF_DIR = OUTPUT_DIR / "pdfs"
JSON_FILE = OUTPUT_DIR / "gaokao_essays.json"

# 创建目录
PDF_DIR.mkdir(parents=True, exist_ok=True)

# HTTP会话
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})


def fetch_page(url):
    """获取页面内容"""
    try:
        print(f"  📥 获取页面: {url}")
        response = session.get(url, timeout=30)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")
        return None


def extract_year_from_url(url):
    """从URL中提取年份"""
    match = re.search(r'(\d{4})', url)
    return match.group(1) if match else "unknown"


def parse_main_page():
    """解析主页面，提取所有年份和链接"""
    print("=" * 60)
    print("开始解析主页面...")
    print("=" * 60)
    
    html = fetch_page(MAIN_PAGE)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找所有年份区块
    years_data = []
    
    # 查找所有包含年份的标题
    year_sections = soup.find_all(['h2', 'h3', 'div'], class_=re.compile(r'year|title'))
    
    # 更简单的方法：查找所有链接并按年份分组
    all_links = soup.find_all('a', href=True)
    
    current_year = None
    current_region = None
    year_dict = {}
    
    for link in all_links:
        href = link['href']
        text = link.get_text(strip=True)
        
        # 跳过空链接或JavaScript链接
        if not text or href.startswith('javascript'):
            continue
        
        # 检测年份（2013-2026）
        year_match = re.search(r'(20[1-2]\d)', text)
        if year_match:
            current_year = year_match.group(1)
            if current_year not in year_dict:
                year_dict[current_year] = {'year': current_year, 'regions': []}
            continue
        
        # 检测地区/试卷类型
        region_keywords = ['全国I卷', '全国II卷', '全国甲卷', '全国乙卷', 
                          '北京卷', '天津卷', '上海卷', '浙江卷', 
                          '江苏卷', '山东卷', '广东卷']
        
        for keyword in region_keywords:
            if keyword in text:
                current_region = keyword
                break
        
        # 如果是作文题目链接
        if current_year and ('zuowen' in href or 'jiqiao' in href):
            essay_info = {
                'title': text,
                'url': urljoin(BASE_URL, href),
                'region': current_region or '未知',
                'has_analysis': '解析' in text or 'jiqiao' in href,
                'has_sample_essay': False,
                'sample_essays': []
            }
            
            # 添加到对应年份
            if current_year in year_dict:
                year_dict[current_year]['regions'].append(essay_info)
    
    # 转换为列表
    years_data = list(year_dict.values())
    
    print(f"\n✅ 找到 {len(years_data)} 个年份的数据")
    for year_data in years_data:
        print(f"  - {year_data['year']}年: {len(year_data['regions'])} 个地区")
    
    return years_data


def parse_essay_page(url):
    """解析作文题目页面，提取题目内容和范文链接"""
    print(f"\n  🔍 解析作文页面: {url}")
    
    html = fetch_page(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取作文题目
    title = ""
    content = ""
    
    # 尝试不同的选择器
    title_elem = soup.find(['h1', 'h2', 'h3'])
    if title_elem:
        title = title_elem.get_text(strip=True)
    
    # 提取正文内容
    content_div = soup.find('div', class_=re.compile(r'content|article|text'))
    if content_div:
        content = content_div.get_text(separator='\n', strip=True)
    else:
        #  fallback: 提取所有段落
        paragraphs = soup.find_all('p')
        content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    
    # 查找范文链接
    sample_essays = []
    essay_links = soup.find_all('a', href=True, string=re.compile(r'范文|优秀'))
    for link in essay_links:
        essay_url = urljoin(BASE_URL, link['href'])
        essay_title = link.get_text(strip=True)
        sample_essays.append({
            'title': essay_title,
            'url': essay_url
        })
    
    return {
        'title': title,
        'content': content,
        'sample_essays': sample_essays
    }


def save_as_pdf(url, filename):
    """将网页保存为PDF（使用wkhtmltopdf或打印为PDF）"""
    # 注意：这里我们保存HTML文件，后续可以转换为PDF
    html_file = PDF_DIR / f"{filename}.html"
    
    try:
        html = fetch_page(url)
        if html:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"    💾 已保存: {html_file.name}")
            return str(html_file)
    except Exception as e:
        print(f"    ❌ 保存失败: {e}")
    
    return None


def process_all_essays(years_data):
    """处理所有作文，下载并保存"""
    print("\n" + "=" * 60)
    print("开始采集作文题目和范文...")
    print("=" * 60)
    
    all_essays = []
    
    for year_data in years_data:
        year = year_data['year']
        print(f"\n📅 处理 {year} 年...")
        
        for region_info in year_data['regions']:
            region = region_info['region']
            title = region_info['title']
            url = region_info['url']
            
            print(f"\n  📝 处理: {region} - {title[:30]}...")
            
            # 解析作文页面
            essay_data = parse_essay_page(url)
            if not essay_data:
                continue
            
            # 生成文件名：年份_地区_是否范文
            safe_region = re.sub(r'[^\w]', '_', region)
            safe_title = re.sub(r'[^\w]', '_', title)[:50]
            
            # 保存作文题目
            filename = f"{year}_{safe_region}_{safe_title}"
            pdf_path = save_as_pdf(url, filename)
            
            essay_record = {
                'year': year,
                'region': region,
                'title': title,
                'url': url,
                'content': essay_data['content'],
                'pdf_path': pdf_path,
                'is_sample': False,
                'tags': ['高考']
            }
            all_essays.append(essay_record)
            
            # 处理范文
            for i, sample in enumerate(essay_data['sample_essays']):
                print(f"    📄 处理范文: {sample['title'][:30]}...")
                
                sample_filename = f"{year}_{safe_region}_{safe_title}_范文{i+1}"
                sample_pdf = save_as_pdf(sample['url'], sample_filename)
                
                sample_record = {
                    'year': year,
                    'region': region,
                    'title': sample['title'],
                    'url': sample['url'],
                    'parent_title': title,
                    'pdf_path': sample_pdf,
                    'is_sample': True,
                    'tags': ['高考', '范文']
                }
                all_essays.append(sample_record)
            
            # 避免请求过快
            time.sleep(1)
    
    print(f"\n✅ 共采集 {len(all_essays)} 篇作文（含范文）")
    
    # 保存JSON
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_essays, f, ensure_ascii=False, indent=2)
    
    print(f"💾 数据已保存到: {JSON_FILE}")
    
    return all_essays


def main():
    """主函数"""
    print("🚀 高考作文采集工具启动")
    print(f"📁 输出目录: {OUTPUT_DIR.absolute()}")
    print()
    
    # 1. 解析主页面
    years_data = parse_main_page()
    
    if not years_data:
        print("❌ 未找到任何数据")
        return
    
    # 2. 处理所有作文
    all_essays = process_all_essays(years_data)
    
    # 3. 统计信息
    print("\n" + "=" * 60)
    print("📊 采集完成统计")
    print("=" * 60)
    
    by_year = {}
    by_type = {'题目': 0, '范文': 0}
    
    for essay in all_essays:
        year = essay['year']
        by_year[year] = by_year.get(year, 0) + 1
        
        if essay['is_sample']:
            by_type['范文'] += 1
        else:
            by_type['题目'] += 1
    
    print(f"\n按年份统计:")
    for year in sorted(by_year.keys()):
        print(f"  {year}年: {by_year[year]} 篇")
    
    print(f"\n按类型统计:")
    print(f"  作文题目: {by_type['题目']} 篇")
    print(f"  范文: {by_type['范文']} 篇")
    
    print(f"\n📁 PDF文件保存在: {PDF_DIR.absolute()}")
    print(f"📄 JSON数据保存在: {JSON_FILE.absolute()}")
    
    print("\n✅ 采集完成！下一步：运行 import_gaokao_essays.py 导入知识库")


if __name__ == '__main__':
    main()
