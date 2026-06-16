#!/usr/bin/env python3
"""
秋招岗位抓取脚本 - 使用搜索引擎索引 + Playwright补充
策略：从搜索引擎索引的牛客企业页摘要提取岗位信息（无需登录、无反爬）
每天由 GitHub Actions 自动运行
"""

import json
import asyncio
import re
import urllib.request
import urllib.parse
from datetime import datetime, date
from playwright.async_api import async_playwright

TODAY = date.today().isoformat()
NEXT_ID = 2000

# 目标公司列表：(公司名, 牛客enterprise_id, logo, tier, companyType, applyUrl)
COMPANIES = [
    # 互联网大厂
    ("字节跳动", "665",  "🎵", "S", "互联网大厂", "https://jobs.bytedance.com/campus"),
    ("腾讯",    "138",  "🐧", "S", "互联网大厂", "https://join.qq.com"),
    ("阿里巴巴","2461", "🛒", "S", "互联网大厂", "https://talent.alibaba.com/campus/home"),
    ("美团",    "179",  "🛵", "S", "互联网大厂", "https://campus.meituan.com"),
    ("快手",    "518",  "▶️", "A", "互联网大厂", "https://campus.kuaishou.cn"),
    ("百度",    "109",  "🔍", "A", "互联网大厂", "https://talent.baidu.com/external/baidu/campus.html"),
    ("小红书",  "3001", "📕", "A", "互联网大厂", "https://job.xiaohongshu.com/campus"),
    ("京东",    "568",  "🛍️", "S", "互联网大厂", "https://campus.jd.com"),
    ("网易",    "369",  "🎮", "A", "互联网大厂", "https://campus.163.com"),
    ("滴滴",    "1559", "🚖", "A", "互联网大厂", "https://campus.didiglobal.com"),
    # 外资
    ("谷歌",   "144",  "🔎", "S", "外资科技",   "https://careers.google.com/students/"),
    ("微软",   "21",   "🪟", "S", "外资科技",   "https://careers.microsoft.com/students/"),
    # 金融
    ("高盛",   "1021", "🏛️", "S", "外资投行",   "https://www.goldmansachs.com/careers/students/"),
    ("摩根大通","423", "🏦", "S", "外资投行",   "https://careers.jpmorgan.com/global/en/students"),
    ("麦肯锡", "1022", "🎯", "S", "战略咨询",   "https://www.mckinsey.com/cn/careers"),
    ("BCG",    "1023", "📊", "S", "战略咨询",   "https://careers.bcg.com/students"),
]

# 岗位分类映射
CATEGORY_MAP = {
    "后端开发": ["后端开发"],
    "前端开发": ["前端开发"],
    "客户端开发": ["客户端开发"],
    "算法": ["AI算法"],
    "人工智能": ["AI算法"],
    "数据": ["数据科学"],
    "产品": ["产品经理"],
    "运营": ["策略运营"],
    "测试": ["测试工程师"],
    "运维": ["运维工程师"],
    "设计": ["设计"],
    "市场": ["市场营销"],
    "财务": ["财务"],
}


def make_job(company, logo, tier, company_type, position, categories,
             location, description, requirements, apply_url, tags,
             job_type="校招", season="2026秋招", deadline="以官网为准"):
    global NEXT_ID
    NEXT_ID += 1
    return {
        "id": NEXT_ID,
        "company": company,
        "logo": logo,
        "tier": tier,
        "companyType": company_type,
        "position": position,
        "category": categories,
        "location": location,
        "type": job_type,
        "season": season,
        "deadline": deadline,
        "headcount": "若干",
        "realData": True,
        "description": description,
        "requirements": requirements,
        "applyUrl": apply_url,
        "tags": tags,
        "isNew": True,
        "postedDate": TODAY,
        "scraped_at": datetime.now().isoformat(),
        "source": "nowcoder-enterprise"
    }


def parse_categories(positions_text):
    """从岗位文本中提取分类"""
    cats = []
    for key, val in CATEGORY_MAP.items():
        if key in positions_text:
            cats.extend(val)
    return list(set(cats)) if cats else ["综合岗位"]


async def scrape_nowcoder_enterprise(page, company_name, enterprise_id, logo, tier, company_type, apply_url):
    """抓取牛客网企业招聘页"""
    jobs = []
    url = f"https://www.nowcoder.com/enterprise/{enterprise_id}"
    print(f"🔍 抓取 {company_name} ({url})")

    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(4000)

        title = await page.title()
        print(f"  页面标题: {title}")

        # 尝试多个选择器找招聘批次信息
        batch_info = ""
        position_info = ""
        deadline_info = "以官网为准"
        city_info = "全国"

        # 查找招聘批次
        for sel in ['.recruit-batch', '[class*="batch"]', '.schedule-item', '[class*="schedule"]']:
            el = await page.query_selector(sel)
            if el:
                batch_info = await el.inner_text()
                print(f"  批次信息: {batch_info[:100]}")
                break

        # 查找岗位信息
        for sel in ['[class*="position-tags"]', '[class*="job-tags"]', '.recruit-position',
                    '[class*="tag-list"]', '[class*="position-list"]']:
            el = await page.query_selector(sel)
            if el:
                position_info = await el.inner_text()
                print(f"  岗位信息: {position_info[:200]}")
                break

        # 查找截止时间
        for sel in ['[class*="deadline"]', '[class*="end-time"]', '[class*="apply-time"]']:
            el = await page.query_selector(sel)
            if el:
                deadline_info = await el.inner_text()
                break

        # 查找城市
        for sel in ['[class*="city"]', '[class*="location"]', '[class*="place"]']:
            el = await page.query_selector(sel)
            if el:
                city_info = await el.inner_text()
                break

        # 查找具体职位列表
        position_items = []
        for sel in ['.position-item', '[class*="position-card"]', '.job-item',
                    '[class*="job-card"]', 'li[class*="item"]']:
            items = await page.query_selector_all(sel)
            if len(items) > 0:
                position_items = items
                print(f"  找到 {len(items)} 个岗位元素")
                break

        if position_items:
            # 有具体岗位列表，逐条解析
            for item in position_items[:15]:
                try:
                    # 找岗位名
                    title_el = None
                    for t_sel in ['h3', 'h4', '[class*="title"]', '[class*="name"]', 'a']:
                        title_el = await item.query_selector(t_sel)
                        if title_el:
                            break

                    # 找地点
                    loc_el = await item.query_selector('[class*="location"], [class*="city"], [class*="place"]')

                    pos_title = await title_el.inner_text() if title_el else ""
                    pos_loc = await loc_el.inner_text() if loc_el else city_info or "全国"

                    pos_title = pos_title.strip()
                    if pos_title and len(pos_title) > 2 and len(pos_title) < 50:
                        cats = parse_categories(pos_title)
                        jobs.append(make_job(
                            company=company_name,
                            logo=logo,
                            tier=tier,
                            company_type=company_type,
                            position=pos_title,
                            categories=cats,
                            location=pos_loc.strip() or "全国",
                            description=f"{company_name}2026校招岗位：{pos_title}",
                            requirements=["以官网岗位要求为准"],
                            apply_url=url,
                            tags=[company_name, "校招", "牛客直招"]
                        ))
                except Exception as e:
                    continue
        elif position_info:
            # 没有具体列表，用岗位分类文本生成汇总条目
            cats = parse_categories(position_info)
            # 从文本中提取每个岗位方向
            pos_list = [p.strip() for p in re.split('[、，,]', position_info) if len(p.strip()) > 1]
            for pos in pos_list[:10]:
                if pos:
                    jobs.append(make_job(
                        company=company_name,
                        logo=logo,
                        tier=tier,
                        company_type=company_type,
                        position=pos,
                        categories=parse_categories(pos),
                        location=city_info.strip() or "全国",
                        description=f"{company_name}2026校招开放岗位：{pos}。{batch_info[:50] if batch_info else ''}",
                        requirements=["以官网岗位要求为准"],
                        apply_url=apply_url,
                        tags=[company_name, "校招", "牛客"]
                    ))
        else:
            # 什么都没抓到，生成官网直达条目
            global NEXT_ID
            print(f"  ⚠️ {company_name} 未抓到岗位信息，生成官网直达")
            jobs.append({
                "id": NEXT_ID + 1,
                "company": company_name,
                "logo": logo,
                "tier": tier,
                "companyType": company_type,
                "position": "官网直达 — 查看全部校招岗位",
                "category": ["校招"],
                "location": "全国",
                "type": "校招",
                "season": "2026秋招",
                "deadline": "以官网为准",
                "headcount": "以官网为准",
                "realData": False,
                "description": f"{company_name}2026校园招聘，请前往官网查看最新岗位。",
                "requirements": ["以官网岗位要求为准"],
                "applyUrl": apply_url,
                "tags": [company_name, "校招", "官网直达"],
                "isNew": False,
                "postedDate": TODAY,
                "scraped_at": datetime.now().isoformat(),
                "source": "fallback"
            })
            NEXT_ID += 1

    except Exception as e:
        print(f"  ❌ {company_name} 抓取失败: {e}")

    print(f"  ✅ {company_name}: 获得 {len(jobs)} 条记录")
    return jobs


async def main():
    print(f"🚀 开始抓取 - {TODAY}")
    all_scraped = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for (name, eid, logo, tier, ctype, aurl) in COMPANIES:
            try:
                jobs = await scrape_nowcoder_enterprise(page, name, eid, logo, tier, ctype, aurl)
                all_scraped.extend(jobs)
            except Exception as e:
                print(f"❌ {name} 整体失败: {e}")
            await asyncio.sleep(3)

        await browser.close()

    # 读取现有数据，保留非实时抓取的静态卡片
    try:
        with open("data/jobs.json", "r", encoding="utf-8") as f:
            existing = json.load(f)
            static_jobs = [j for j in existing.get("jobs", [])
                          if not j.get("realData", True) and j.get("source") not in ["nowcoder-enterprise", "playwright-scrape"]]
    except Exception:
        static_jobs = []

    # 合并去重
    seen = set()
    unique = []
    for job in all_scraped + static_jobs:
        key = f"{job['company']}_{job['position']}"
        if key not in seen:
            seen.add(key)
            unique.append(job)

    real_count = len([j for j in unique if j.get("realData")])
    static_count = len([j for j in unique if not j.get("realData")])

    output = {
        "lastUpdated": TODAY,
        "note": "✅ realData:true 为实时抓取；🔗 realData:false 为官网直达",
        "scrapedCount": real_count,
        "staticCount": static_count,
        "jobs": unique
    }

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！共 {len(unique)} 条")
    print(f"   真实抓取: {real_count} 条")
    print(f"   官网直达: {static_count} 条")


if __name__ == "__main__":
    asyncio.run(main())
