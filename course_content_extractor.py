#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Studio课程内容提取脚本
访问指定页面并提取已完成和未完成的学习项目链接
自动进入未完成链接并处理练习页面
"""

from playwright.sync_api import sync_playwright, expect
import time
import json
import csv
import re
import os
from datetime import datetime

# 配置信息
PRACTICE_PAGE_URL = [
    "http://www.linuxstudio.cn/practice.php?chapter=Linux常用命令",
    "http://www.linuxstudio.cn/practice.php?chapter=Shell脚本编程基础",
    "http://www.linuxstudio.cn/practice.php?chapter=VI编辑器"
]

# 用户名和密码将从外部传入或通过配置文件加载
USER_NAME = None
PASSWORD = None

# 输出文件
OUTPUT_JSON_FILE = "output/completed_courses.json"
OUTPUT_CSV_FILE = "output/completed_courses.csv"


def log_message(message):
    """带时间戳的日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def extract_green_links(page):
    """
    从页面中提取ID为"study_content"的ul元素中视觉呈现为绿色的URL链接
    
    Args:
        page: Playwright页面对象
    
    Returns:
        list: 符合条件的URL链接列表
    """
    green_links = []
    
    try:
        log_message("开始提取绿色链接...")
        
        # 定位到ID为"study_content"的元素
        study_content_element = page.locator("#study_content")
        
        # 检查元素是否存在
        if not study_content_element.count():
            log_message("❌ 未找到ID为'study_content'的元素")
            return green_links
        
        log_message("✅ 已找到ID为'study_content'的元素")
        
        # 定位到study_content下的ul元素 (路径为//*[@id="study_content"]/ul)
        ul_element = study_content_element.locator("ul")
        
        # 检查ul元素是否存在
        if not ul_element.count():
            log_message("❌ 未找到'study_content'下的ul元素")
            return green_links
        
        log_message("✅ 已找到'study_content'下的ul元素")
        
        # 获取ul元素中的所有链接(a标签)
        links = ul_element.locator("a")
        links_count = links.count()
        log_message(f"📊 在ul元素中找到{links_count}个链接")
        
        # 绿色相关的颜色值定义（包括常见的绿色表示方式）
        green_keywords = [
            'green', 'rgb(0,128,0)', 'rgb(0, 128, 0)', 
            '#008000', '#008000', '#00ff00', '#00FF00',
            'rgb(0,255,0)', 'rgb(0, 255, 0)', '#32cd32', '#32CD32',
            'rgb(50,205,50)', 'rgb(50, 205, 50)', 'rgba(0,128,0,', 'rgba(0, 128, 0,',
            'rgba(0,255,0,', 'rgba(0, 255, 0,', 'rgba(50,205,50,', 'rgba(50, 205, 50,'
        ]
        
        # 遍历所有链接，检查是否为绿色
        for i in range(links_count):
            link = links.nth(i)
            
            try:
                # 获取元素的style属性（内联样式）
                style = link.get_attribute("style") or ""
                
                # 使用Playwright的API获取样式信息，避免JavaScript评估错误
                color = link.evaluate('(el) => getComputedStyle(el).color')
                background_color = link.evaluate('(el) => getComputedStyle(el).backgroundColor')
                class_name = link.get_attribute('class') or ''
                computed_style = {"color": color, "backgroundColor": background_color, "className": class_name}
                
                # 组合所有可能包含颜色信息的样式
                all_styles = f"{style} {computed_style['color']} {computed_style['backgroundColor']} {computed_style['className']}".lower()
                
                # 检查是否包含绿色相关的样式
                is_green = False
                for keyword in green_keywords:
                    if keyword.lower() in all_styles:
                        is_green = True
                        break
                
                # 额外检查是否有green类名或其他绿色相关的类
                if 'green' in computed_style['className'].lower() or 'success' in computed_style['className'].lower():
                    is_green = True
                
                # 记录样式信息用于调试
                log_message(f"🔍 链接{i+1}样式分析: color={computed_style['color']}, bg={computed_style['backgroundColor']}, class={computed_style['className']}")
                
                if is_green:
                    # 提取URL链接
                    url = link.get_attribute("href")
                    if url:
                        log_message(f"🟢 链接{i+1}被识别为绿色，URL: {url}")
                        green_links.append(url)
                    else:
                        log_message(f"🟢 链接{i+1}被识别为绿色，但没有找到有效URL")
                else:
                    log_message(f"⚪ 链接{i+1}不是绿色")
            except Exception as link_error:
                log_message(f"❌ 分析链接{i+1}时出错: {str(link_error)}")
        
        # 提取完成后的统计信息
        log_message(f"✅ 绿色链接提取完成，共找到{len(green_links)}个绿色URL链接")
        for idx, url in enumerate(green_links):
            log_message(f"  [{idx+1}] {url}")
    except Exception as e:
        log_message(f"❌ 提取绿色链接时出错: {str(e)}")
    
    return green_links


def test_green_links_extraction():
    """
    测试绿色链接提取功能的正确性
    """
    log_message("===== 开始测试绿色链接提取功能 =====")
    
    try:
        # 创建一个简单的HTML测试页面
        test_html = '''<!DOCTYPE html><html><head><title>测试绿色链接提取</title><style>.green-text { color: green; }.green-bg { background-color: #008000; color: white; }.normal-link { color: blue; }</style></head><body><div id="study_content"><ul><li><a href="https://example.com/link1" style="color: green;">绿色文本链接1</a></li><li><a href="https://example.com/link2" class="green-text">绿色类链接2</a></li><li><a href="https://example.com/link3" class="green-bg">绿色背景链接3</a></li><li><a href="https://example.com/link4" style="color: #32cd32;">浅绿色链接4</a></li><li><a href="https://example.com/link5" class="normal-link">普通蓝色链接5</a></li><li><a href="https://example.com/link6" style="color: rgb(0,128,0);">RGB绿色链接6</a></li></ul></div></body></html>'''
        
        # 使用Playwright测试
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, timeout=10000)
            page = browser.new_page()
            
            try:
                # 加载测试页面
                page.set_content(test_html, timeout=5000)
                log_message("✅ 已加载测试页面")
                
                # 调用提取函数
                green_links = extract_green_links(page)
                log_message(f"✅ 提取到{len(green_links)}个绿色链接")
                log_message(f"绿色链接列表: {green_links}")
                
                # 预期的绿色链接
                expected_links = [
                    "https://example.com/link1",
                    "https://example.com/link2",
                    "https://example.com/link3",
                    "https://example.com/link4",
                    "https://example.com/link6"
                ]
                
                # 检查结果
                missing_links = set(expected_links) - set(green_links)
                unexpected_links = set(green_links) - set(expected_links)
                
                if not missing_links and not unexpected_links:
                    log_message("🎉 测试通过! 绿色链接提取功能工作正常")
                else:
                    if missing_links:
                        log_message(f"❌ 未找到的绿色链接: {missing_links}")
                    if unexpected_links:
                        log_message(f"⚠️ 错误识别的绿色链接: {unexpected_links}")
            
            finally:
                page.close()
                browser.close()
                log_message("✅ 已关闭浏览器")
    
    except Exception as e:
        log_message(f"❌ 测试过程中发生错误: {str(e)}")
    
    log_message("===== 测试完成 =====")



def login_to_system(page):
    """
    在已打开的页面上执行登录操作
    
    Args:
        page: Playwright页面对象
    
    Returns:
        bool: 登录是否成功
    """
    try:
        log_message("开始登录流程...")
        
        # 访问登录页面
        login_url = "http://www.linuxstudio.cn/user/index.php"
        page.goto(login_url, wait_until="domcontentloaded")
        log_message(f"✓ 已访问登录页面: {login_url}")
        
        # 等待页面元素加载完成
        page.wait_for_selector("#username", state="visible", timeout=15000)
        
        # 填写用户名和密码
        page.fill("#username", USER_NAME)
        page.fill("#password", PASSWORD)
        log_message("✓ 已输入用户名和密码")
        
        # 尝试点击提交按钮
        try:
            # 使用多种方式尝试点击登录按钮
            submit_button = page.locator("input[type='submit'][name='submit']")
            submit_button.scroll_into_view_if_needed()
            submit_button.click(force=True)  # 使用force参数确保点击成功
            log_message("✓ 已点击登录按钮")
        except Exception as e:
            log_message(f"警告：直接点击登录按钮失败，尝试通过坐标点击: {e}")
            # 备选方案：通过坐标点击
            button_bounding_box = submit_button.bounding_box()
            if button_bounding_box:
                x = button_bounding_box['x'] + button_bounding_box['width'] / 2
                y = button_bounding_box['y'] + button_bounding_box['height'] / 2
                page.mouse.click(x, y)
                log_message("✓ 已通过坐标点击登录按钮")
        
        # 等待页面跳转和加载完成
        page.wait_for_url("**", timeout=20000)
        page.wait_for_load_state("networkidle", timeout=20000)
        
        # 验证登录状态
        if "my_info.php" in page.content():
            log_message("✓ 登录成功")
            return True
        else:
            log_message("✗ 登录失败：页面中未找到登录成功的标识")
            return False
    
    except Exception as e:
        log_message(f"✗ 登录过程中发生错误: {e}")
        return False


def visit_practice_page(page, url):
    """
    访问指定的练习页面
    
    Args:
        page: Playwright页面对象
    
    Returns:
        bool: 页面访问是否成功
    """
    try:
        log_message(f"访问练习页面: {url}")
        page.goto(url, wait_until="domcontentloaded")
        
        # 等待页面加载完成
        page.wait_for_load_state("networkidle", timeout=20000)
        
        log_message(f"✓ 页面访问成功，当前URL: {page.url}")
        log_message(f"页面标题: {page.title()}")
        
        return True
    except Exception as e:
        log_message(f"✗ 访问练习页面失败: {e}")
        return False


def extract_course_links(page):
    """
    从页面中提取已完成和未完成的课程链接
    
    Args:
        page: Playwright页面对象
    
    Returns:
        tuple: (已完成的链接列表, 未完成的链接列表)
    """
    completed_links = []
    incomplete_links = []
    
    try:
        # 保存页面HTML用于调试
        with open("./output/course_page.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        log_message("✓ 已保存页面HTML到course_page.html")
        
        # 查找id="study_content"的div块中的<ul>元素，然后获取其中的<li>元素
        try:
            # 先找到study_content div
            study_content_div = page.locator("#study_content").first
            if study_content_div:
                # 查找div中的ul元素
                ul_elements = study_content_div.locator("ul").all()
                log_message(f"✓ 找到{len(ul_elements)}个ul元素在study_content div中")
                
                # 收集所有ul中的li元素
                list_items = []
                for ul in ul_elements:
                    ul_list_items = ul.locator("li").all()
                    list_items.extend(ul_list_items)
                
                log_message(f"✓ 找到{len(list_items)}个列表项在study_content div的ul中")
            else:
                log_message("! 未找到id='study_content'的div元素，回退到查找所有li元素")
                # 回退到原来的方式
                list_items = page.locator("li").all()
                log_message(f"✓ 回退后找到{len(list_items)}个列表项")
        except Exception as e:
            log_message(f"! 查找study_content div中的列表项时出错: {str(e)}")
            # 出错时回退到原来的方式
            list_items = page.locator("li").all()
            log_message(f"✓ 出错回退后找到{len(list_items)}个列表项")
        
        for index, item in enumerate(list_items):
            try:
                # 检查是否包含蓝色对勾标记
                has_blue_check = False
                try:
                    font_elements = item.locator("font[color='blue']").all()
                    for font_element in font_elements:
                        text = font_element.text_content().strip()
                        if "✓" in text or "✔" in text:
                            has_blue_check = True
                            break
                except:
                    pass
                
                # 提取<a>标签的href属性
                a_elements = item.locator("a").all()
                for a_element in a_elements:
                    try:
                        href = a_element.get_attribute("href")
                        if href:
                            # 处理相对路径，转换为绝对路径
                            if not href.startswith("http"):
                                if href.startswith("/"):
                                    href = f"http://www.linuxstudio.cn{href}"
                                else:
                                    href = f"http://www.linuxstudio.cn/{href}"
                            
                            # 提取链接文本
                            link_text = a_element.text_content().strip() or "未知链接文本"
                            
                            # 记录链接信息
                            link_info = {
                                "index": index + 1,
                                "href": href,
                                "text": link_text,
                                "completed": has_blue_check,
                                "extraction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            if has_blue_check:
                                completed_links.append(link_info)
                            else:
                                incomplete_links.append(link_info)
                            
                            log_message(f"{'✓' if has_blue_check else '○'} 发现{'' if has_blue_check else '未'}完成项目 {index + 1}: {link_text} -> {href}")
                    except Exception as e:
                        log_message(f"处理链接时出错: {e}")
                        continue
            except Exception as e:
                log_message(f"处理列表项 {index + 1} 时出错: {e}")
                continue
        
        log_message(f"✓ 提取完成：已完成项目{len(completed_links)}个，未完成项目{len(incomplete_links)}个")
        return completed_links, incomplete_links
    
    except Exception as e:
        log_message(f"✗ 提取课程链接时发生错误: {e}")
        return completed_links, incomplete_links


def save_to_json(completed_links, incomplete_links):
    """
    将提取的链接保存到JSON文件
    
    Args:
        completed_links: 已完成的链接列表
        incomplete_links: 未完成的链接列表
    """
    try:
        data = {
            "extraction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed_links": completed_links,
            "incomplete_links": incomplete_links,
            "summary": {
                "total_completed": len(completed_links),
                "total_incomplete": len(incomplete_links),
                "total": len(completed_links) + len(incomplete_links)
            }
        }
        
        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log_message(f"✓ 已将数据保存到JSON文件: {OUTPUT_JSON_FILE}")
    except Exception as e:
        log_message(f"✗ 保存JSON文件失败: {e}")


def save_to_csv(completed_links, incomplete_links):
    """
    将提取的链接保存到CSV文件
    
    Args:
        completed_links: 已完成的链接列表
        incomplete_links: 未完成的链接列表
    """
    try:
        all_links = []
        
        # 添加已完成的链接
        for link in completed_links:
            link_copy = link.copy()
            link_copy["status"] = "completed"
            all_links.append(link_copy)
        
        # 添加未完成的链接
        for link in incomplete_links:
            link_copy = link.copy()
            link_copy["status"] = "incomplete"
            all_links.append(link_copy)
        
        # 按照索引排序
        all_links.sort(key=lambda x: x["index"])
        
        # 保存到CSV
        with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as f:
            if all_links:
                fieldnames = ["index", "text", "href", "status", "completed", "extraction_time"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_links)
        
        log_message(f"✓ 已将数据保存到CSV文件: {OUTPUT_CSV_FILE}")
    except Exception as e:
        log_message(f"✗ 保存CSV文件失败: {e}")







def process_practice_page(page):
    """
    处理练习页面：
    1. 找到特定颜色的文本并提取数字
    2. 修改隐藏表单字段
    3. 提交表单
    
    Args:
        page: Playwright页面对象
    
    Returns:
        bool: 处理是否成功
    """
    try:
        log_message("🔍 开始处理练习页面")
        
        # 1. 查找特定颜色文本并提取数字
        red_text_element = page.locator("font[color='#FF5809']").first
        if red_text_element.count() > 0:
            red_text = red_text_element.text_content().strip()
            log_message(f"✓ 找到红色文本: {red_text}")
            
            # 提取括号中的数字
            match = re.search(r'（共 (\d+) 关）', red_text)
            if match:
                total_steps = match.group(1)
                log_message(f"✓ 提取到总关卡数: {total_steps}")
                
                # 2. 修改隐藏表单字段
                step_input = page.locator("input[type='hidden'][name='step']")
                if step_input.count() > 0:
                    # 使用evaluate修改隐藏字段的值（始终设置为total_steps + 1）
                    page.evaluate(f"document.querySelector('input[type=\\'hidden\\'][name=\\'step\\']').value = '{int(total_steps) + 1}'")
                    log_message(f"✓ 已修改step值为: {int(total_steps) + 1}")
                    
                    # 点击提交按钮
                    submit_button = page.locator("input[type='submit'][name='button_prac_process']")
                    if submit_button.count() > 0:
                        submit_button.click()
                        page.wait_for_load_state("networkidle")
                        log_message("✓ 已点击提交按钮")
                        return True
                    else:
                        log_message("✗ 未找到提交按钮")
                        return False
                else:
                    log_message("✗ 未找到step隐藏字段")
                    return False
            else:
                log_message("✗ 未能从红色文本中提取数字")
                return False
        else:
            log_message("✗ 未找到特定颜色的文本")
            return False
        
    except Exception as e:
        log_message(f"✗ 处理练习页面时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_incomplete_links(page, incomplete_links):
    """
    依次进入未完成的链接并处理
    
    Args:
        page: Playwright页面对象
        incomplete_links: 未完成的链接列表
    """
    log_message(f"\n=== 开始处理未完成的链接（共{len(incomplete_links)}个） ===")
    
    for index, link_info in enumerate(incomplete_links):
        try:
            log_message(f"\n🔍 处理第{index + 1}/{len(incomplete_links)}个未完成链接")
            log_message(f"📄 链接: {link_info['text']} -> {link_info['href']}")
            
            # 先访问链接
            page.goto(link_info['href'], wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            log_message(f"✓ 已访问链接: {link_info['href']}")
            
            # 检查访问后的页面是否是练习页面
            if "practice" in page.url or "prac" in page.url:
                log_message("⚠ 检测到练习页面，开始处理")
                process_practice_page(page)
            else:
                log_message("ℹ️ 访问的页面不是练习页面，跳过处理")
            
            # 等待几秒，避免过快操作
            time.sleep(2)
            
        except Exception as e:
            log_message(f"✗ 处理链接时出错: {e}")
            continue
    
    log_message("\n✓ 所有未完成链接处理完毕")

def main(user_name=None, password=None):
    """
    主函数：执行完整的提取和处理流程
    
    Args:
        user_name: 用户名，如果为None则使用默认值
        password: 密码，如果为None则使用默认值
    """
    completed_links = []
    incomplete_links = []
    
    # 使用全局变量存储用户名和密码
    global USER_NAME, PASSWORD
    if user_name:
        USER_NAME = user_name
    if password:
        PASSWORD = password
    
    # 如果没有提供用户名和密码，尝试从配置文件加载
    if not USER_NAME or not PASSWORD:
        try:
            import configparser
            config = configparser.ConfigParser()
            config_path = "d:/code/python_code/ai_factory/linuxclass_quick_done/config.txt"
            
            # 读取配置文件（使用简单的文本格式）
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        if key == 'USER_NAME':
                            USER_NAME = value
                        elif key == 'PASSWORD':
                            PASSWORD = value
        except Exception as e:
            log_message(f"✗ 从配置文件加载用户名和密码失败: {e}")
            return
    
    # 验证用户名和密码
    if not USER_NAME or not PASSWORD:
        log_message("✗ 用户名或密码为空，无法执行登录")
        return
    
    with sync_playwright() as p:
        try:
            log_message("自动化提取流程开始...")
            
            # 启动浏览器
            browser = p.chromium.launch(
                headless=False,  # 显示浏览器窗口便于调试
                args=["--start-maximized"]
            )
            context = browser.new_context(
                viewport=None,
                locale="zh-CN"
            )
            page = context.new_page()
            
            # 登录系统
            if not login_to_system(page):
                log_message("✗ 登录失败，无法继续执行")
                return
            
            for url in PRACTICE_PAGE_URL:
                # 访问练习页面
                if not visit_practice_page(page, url):
                    log_message("✗ 页面访问失败，无法继续执行")
                    return
                
                # 提取课程链接
                completed_links, incomplete_links = extract_course_links(page)
                
                # 保存提取的链接
                save_to_json(completed_links, incomplete_links)
                save_to_csv(completed_links, incomplete_links)
                
                # 处理未完成的链接
                if incomplete_links:
                    process_incomplete_links(page, incomplete_links)
            
            # 输出总结信息
            log_message("\n=== 提取结果总结 ===")
            log_message(f"已完成的学习项目: {len(completed_links)} 个")
            log_message(f"未完成的学习项目: {len(incomplete_links)} 个")
            log_message(f"总共提取的链接: {len(completed_links) + len(incomplete_links)} 个")
            log_message(f"数据已保存到: {OUTPUT_JSON_FILE} 和 {OUTPUT_CSV_FILE}")
            
        except Exception as e:
            log_message(f"✗ 自动化流程发生严重错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 等待一段时间以便查看结果
            log_message("\n等待5秒后关闭浏览器...")
            time.sleep(5)
            # 关闭资源
            if 'page' in locals():
                page.close()
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()
            log_message("✓ 浏览器已关闭")




if __name__ == "__main__":
    # 运行绿色链接提取测试
    # test_green_links_extraction()
    
    main()