#!/usr/bin/env python3
"""
秋招岗位抓取脚本 - 使用 Playwright 模拟真实浏览器
每天由 GitHub Actions 自动运行，抓取最新校招岗位
"""

import json
import asyncio
import re
from datetime import datetime, date
from playwright.async_api import async_playwright

TODAY = date.today().isoformat()
RESULTS = []
NEXT_ID = 1000  # 从1000开始，避免与手动数据冲突


def make_job(company, logo, tier, company_type, position, category,
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
        "category": category if isinstance(category, list) else [category],
        "location": location,
        "type": job_type,
        "season": season,
        "deadline": deadline,
        "headcount": "若干",
        "realData": True,
        "description": description,
        "requirements": requirements if isinstance(requirements, list) else [requirements],
        "applyUrl": apply_url,
        "tags": tags if isinstance(tags, list) else [tags],
        "isNew": True,
        "postedDate": TODAY,
        "source": "playwright-scrape"
    }


async def scrape_bytedance(page):
    """抓取字节跳动校招"""
    print("🔍 抓取字节跳动...")
    jobs = []
    try:
        await page.goto("https://jobs.bytedance.com/campus/position?keywords=&category=&location=&project=&type=2&job_hot_flag=&current=1&limit=10&functionCategory=&tag=", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(3000)

        # 抓取岗位列表
        items = await page.query_selector_all(".position-item, [class*='position-card'], [class*='job-item']")
        print(f"  字节: 找到 {len(items)} 个元素")

        for item in items[:10]:
            try:
                title = await item.query_selector("[class*='title'], h3, h4")
                location = await item.query_selector("[class*='location'], [class*='city']")
                dept = await item.query_selector("[class*='department'], [class*='category']")

                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "全国"
                dept_text = await dept.inner_text() if dept else ""

                if title_text.strip():
                    jobs.append(make_job(
                        company="字节跳动",
                        logo="🎵",
                        tier="S",
                        company_type="互联网大厂",
                        position=title_text.strip(),
                        category=[dept_text.strip() or "技术"],
                        location=location_text.strip(),
                        description=f"字节跳动校招岗位：{title_text.strip()}，部门：{dept_text.strip()}",
                        requirements=["以官网岗位要求为准"],
                        apply_url="https://jobs.bytedance.com/campus",
                        tags=["字节跳动", "校招", dept_text.strip()]
                    ))
            except Exception as e:
                print(f"  字节单条解析失败: {e}")
                continue
    except Exception as e:
        print(f"  字节抓取失败: {e}")
    return jobs


async def scrape_tencent(page):
    """抓取腾讯校招"""
    print("🔍 抓取腾讯...")
    jobs = []
    try:
        await page.goto("https://join.qq.com/post.html?type=2", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(3000)

        items = await page.query_selector_all(".recruit-item, [class*='position-item'], .item-bd")
        print(f"  腾讯: 找到 {len(items)} 个元素")

        for item in items[:10]:
            try:
                title = await item.query_selector("h3, h4, .recruit-title, [class*='title']")
                location = await item.query_selector("[class*='location'], [class*='place']")
                dept = await item.query_selector("[class*='type'], [class*='category']")

                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "全国"
                dept_text = await dept.inner_text() if dept else ""

                if title_text.strip():
                    jobs.append(make_job(
                        company="腾讯",
                        logo="🐧",
                        tier="S",
                        company_type="互联网大厂",
                        position=title_text.strip(),
                        category=[dept_text.strip() or "技术"],
                        location=location_text.strip(),
                        description=f"腾讯校招岗位：{title_text.strip()}",
                        requirements=["以官网岗位要求为准"],
                        apply_url="https://join.qq.com/post.html?type=2",
                        tags=["腾讯", "校招"]
                    ))
            except Exception as e:
                continue
    except Exception as e:
        print(f"  腾讯抓取失败: {e}")
    return jobs


async def scrape_alibaba(page):
    """抓取阿里巴巴校招"""
    print("🔍 抓取阿里巴巴...")
    jobs = []
    try:
        await page.goto("https://talent.alibaba.com/campus/position-list?lang=zh", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(4000)

        items = await page.query_selector_all("[class*='position-item'], [class*='job-card'], .position-card")
        print(f"  阿里: 找到 {len(items)} 个元素")

        for item in items[:10]:
            try:
                title = await item.query_selector("[class*='title'], h3, h4")
                location = await item.query_selector("[class*='location'], [class*='city']")
                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "全国"

                if title_text.strip():
                    jobs.append(make_job(
                        company="阿里巴巴",
                        logo="🛒",
                        tier="S",
                        company_type="互联网大厂",
                        position=title_text.strip(),
                        category=["技术/产品/运营"],
                        location=location_text.strip(),
                        description=f"阿里巴巴校招岗位：{title_text.strip()}",
                        requirements=["以官网岗位要求为准"],
                        apply_url="https://talent.alibaba.com/campus/home",
                        tags=["阿里巴巴", "校招"]
                    ))
            except Exception as e:
                continue
    except Exception as e:
        print(f"  阿里抓取失败: {e}")
    return jobs


async def scrape_meituan(page):
    """抓取美团校招"""
    print("🔍 抓取美团...")
    jobs = []
    try:
        await page.goto("https://campus.meituan.com/recruit-info", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(3000)

        items = await page.query_selector_all("[class*='position'], [class*='job-item'], .recruit-item")
        print(f"  美团: 找到 {len(items)} 个元素")

        for item in items[:10]:
            try:
                title = await item.query_selector("[class*='title'], h3, h4")
                location = await item.query_selector("[class*='location'], [class*='city']")
                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "全国"

                if title_text.strip():
                    jobs.append(make_job(
                        company="美团",
                        logo="🛵",
                        tier="S",
                        company_type="互联网大厂",
                        position=title_text.strip(),
                        category=["技术/产品/运营/数据"],
                        location=location_text.strip(),
                        description=f"美团校招岗位：{title_text.strip()}",
                        requirements=["以官网岗位要求为准"],
                        apply_url="https://campus.meituan.com/recruit-info",
                        tags=["美团", "校招"]
                    ))
            except Exception as e:
                continue
    except Exception as e:
        print(f"  美团抓取失败: {e}")
    return jobs


async def scrape_51job_estee_lauder(page):
    """抓取雅诗兰黛51job校招页（已验证可抓）"""
    print("🔍 抓取雅诗兰黛（51job）...")
    jobs = []
    try:
        await page.goto("https://campus.51job.com/elccampus", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(2000)

        items = await page.query_selector_all(".j-job-card, .job-item, [class*='position']")
        print(f"  雅诗兰黛: 找到 {len(items)} 个元素")

        for item in items[:15]:
            try:
                title = await item.query_selector("[class*='title'], h3, h4, .job-name")
                location = await item.query_selector("[class*='location'], [class*='city'], .job-area")
                desc = await item.query_selector("[class*='desc'], [class*='intro'], p")

                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "上海"
                desc_text = await desc.inner_text() if desc else ""

                if title_text.strip():
                    jobs.append(make_job(
                        company="雅诗兰黛集团",
                        logo="💄",
                        tier="S",
                        company_type="消费（美妆）",
                        position=title_text.strip(),
                        category=["品牌市场", "电商运营", "供应链"],
                        location=location_text.strip() or "上海",
                        description=desc_text.strip() or f"雅诗兰黛校招：{title_text.strip()}",
                        requirements=["本科及以上学历", "热爱美妆行业"],
                        apply_url="https://campus.51job.com/elccampus",
                        tags=["雅诗兰黛", "美妆", "校招"]
                    ))
            except Exception as e:
                continue
    except Exception as e:
        print(f"  雅诗兰黛抓取失败: {e}")
    return jobs


async def scrape_mckinsey(page):
    """抓取麦肯锡校招"""
    print("🔍 抓取麦肯锡...")
    jobs = []
    try:
        await page.goto("https://www.mckinsey.com/cn/careers/search-jobs#experienced=false", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await page.wait_for_timeout(4000)

        items = await page.query_selector_all("[class*='job'], [class*='position'], article")
        print(f"  麦肯锡: 找到 {len(items)} 个元素")

        for item in items[:10]:
            try:
                title = await item.query_selector("h2, h3, h4, [class*='title']")
                location = await item.query_selector("[class*='location'], [class*='city']")
                title_text = await title.inner_text() if title else ""
                location_text = await location.inner_text() if location else "北京/上海"

                if title_text.strip():
                    jobs.append(make_job(
                        company="麦肯锡",
                        logo="🎯",
                        tier="S",
                        company_type="战略咨询",
                        position=title_text.strip(),
                        category=["战略咨询"],
                        location=location_text.strip(),
                        description=f"麦肯锡校招：{title_text.strip()}",
                        requirements=["以官网岗位要求为准"],
                        apply_url="https://www.mckinsey.com/cn/careers",
                        tags=["麦肯锡", "咨询", "MBB", "校招"]
                    ))
            except Exception as e:
                continue
    except Exception as e:
        print(f"  麦肯锡抓取失败: {e}")
    return jobs


async def load_existing_jobs():
    """读取现有的官网直达数据（不被覆盖）"""
    try:
        with open("data/jobs.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # 只保留 realData:false 的官网直达卡片
            return [j for j in data.get("jobs", []) if not j.get("realData", True)]
    except Exception:
        return []


async def main():
    print(f"🚀 开始抓取 - {TODAY}")

    # 读取现有官网直达数据
    static_jobs = await load_existing_jobs()
    print(f"📋 保留 {len(static_jobs)} 个官网直达卡片")

    scraped_jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        # 逐一抓取各平台
        scrapers = [
            scrape_51job_estee_lauder,
            scrape_bytedance,
            scrape_tencent,
            scrape_alibaba,
            scrape_meituan,
            scrape_mckinsey,
        ]

        for scraper in scrapers:
            try:
                jobs = await scraper(page)
                scraped_jobs.extend(jobs)
                print(f"  ✅ {scraper.__name__}: 抓到 {len(jobs)} 个岗位")
            except Exception as e:
                print(f"  ❌ {scraper.__name__} 失败: {e}")
            await asyncio.sleep(2)  # 避免被封

        await browser.close()

    # 合并：真实抓取 + 官网直达
    all_jobs = scraped_jobs + static_jobs

    # 去重（按公司+岗位名）
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = f"{job['company']}_{job['position']}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    output = {
        "lastUpdated": TODAY,
        "note": "✅ realData:true 为实时抓取岗位；🔗 realData:false 为官网直达入口",
        "scrapedCount": len(scraped_jobs),
        "staticCount": len(static_jobs),
        "jobs": unique_jobs
    }

    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！共 {len(unique_jobs)} 个岗位")
    print(f"   - 真实抓取: {len(scraped_jobs)} 个")
    print(f"   - 官网直达: {len(static_jobs)} 个")


if __name__ == "__main__":
    asyncio.run(main())
