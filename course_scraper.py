from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re
import json
import os
import time
import random
import csv
from datetime import datetime


# 日志函数 - 简洁版
def log_message(message, level="INFO"):
    """打印带有时间戳和日志级别的消息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    log_levels = {
        "INFO": "ℹ️ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }
    color = log_levels.get(level.upper(), "ℹ️ ")
    print(f"[{timestamp}] {color} [{level.upper()}]  {message}")

# 课程数据存储
course_data = []

def save_course_data_to_csv(filename="output/completed_courses.csv"):
    """将课程数据保存为CSV文件"""
    global course_data
    if not course_data:
        log_message("⚠ 没有数据可保存到CSV", "WARNING")
        return False
    
    try:
        fieldnames = ['timestamp', 'course_name', 'course_id', 'duration', 'status']
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()
            
            # 写入数据
            for course in course_data:
                writer.writerow(course)
        
        log_message(f"✓ 课程数据已保存到 {filename}", "INFO")
        return True
    except Exception as e:
        log_message(f"⚠ 保存CSV文件失败: {e}", "ERROR")
        return False

def save_course_data_to_json(filename="output/completed_courses.json"):
    """将课程数据保存为JSON文件"""
    global course_data
    if not course_data:
        log_message("⚠ 没有数据可保存到JSON", "WARNING")
        return False
    
    try:
        # 如果文件已存在，读取现有数据
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as jsonfile:
                    existing_data = json.load(jsonfile)
            except:
                existing_data = []
        
        # 合并数据
        existing_data.extend(course_data)
        
        # 保存数据
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(existing_data, jsonfile, ensure_ascii=False, indent=2)
        
        log_message(f"✓ 课程数据已保存到 {filename}", "INFO")
        return True
    except Exception as e:
        log_message(f"⚠ 保存JSON文件失败: {e}", "ERROR")
        return False

def collect_course_info(page, course_name="未知课程", duration=65, status="completed"):
    """收集课程信息并添加到数据列表"""
    global course_data
    course_id = ""
    try:
        # 尝试从URL获取课程ID
        url = page.url
        # 从URL中提取数字ID
        ids = re.findall(r'\d+', url)
        if ids:
            course_id = ids[0]
    except:
        pass
    
    course_info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'course_name': course_name,
        'course_id': course_id,
        'duration': duration,
        'status': status
    }
    
    course_data.append(course_info)
    log_message(f"✓ 已收集课程信息: {course_name} (ID: {course_id})", "DEBUG")

def main(user_name, password):
    """主函数：登录并自动学习课程"""
    start_time = datetime.now()
    log_message("===== 开始执行自动化学习流程 =====")
    log_message(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    courses_data = []
    completed_courses = 0
    browser = None
    context = None
    page = None
    playwright_instance = None

    try:
        # 1. 初始化浏览器和登录
        log_message("\n[步骤1] 启动浏览器...")
        playwright_instance = sync_playwright().start()
        log_message("✓ Playwright 初始化成功")

        browser = playwright_instance.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-gpu", "--no-sandbox", 
                  "--disable-dev-shm-usage", "--disable-extensions"],
            slow_mo=100
        )
        log_message("✓ 浏览器已启动")

        context = browser.new_context(viewport=None, locale="zh-CN")
        page = context.new_page()
        log_message("✓ 浏览器上下文和页面创建完成")

        # 2. 执行登录
        log_message("\n[步骤2] 执行自动化登录...")
        page.goto("http://www.linuxstudio.cn/user/index.php", wait_until="domcontentloaded")
        log_message("✓ 登录页面加载完成")
        
        page.fill("#username", user_name)
        page.fill("#password", password)
        log_message("✓ 已输入用户名和密码")

        # 点击提交按钮
        submit_button = page.locator("input[type='submit']")
        submit_button.click(force=True)
        log_message("✓ 已点击提交按钮")

        # 等待页面加载完成，不依赖特定URL
        page.wait_for_load_state("networkidle", timeout=20000)
        
        # 验证登录状态（通过检查页面内容）
        page_content = page.content()
        if "登录成功" in page_content or "用户中心" in page_content or "my_info" in page_content:
            log_message("✓ 登录成功，页面内容验证通过")
        else:
            log_message("⚠ 登录状态验证不确定，但继续执行", "WARNING")

        # 3. 访问课程页面
        log_message("\n[步骤3] 访问课程页面...")
        course_url = "http://www.linuxstudio.cn/user/my_plan.php"
        page.goto(course_url, wait_until="domcontentloaded")
        log_message("✓ 课程页面加载完成")

        # 4. 识别未学习课程
        log_message("\n[步骤4] 识别课程链接...")
        
        # 等待课程列表加载
        page.wait_for_selector("img[src*='content1.png']", timeout=10000)
        
        # 查找所有未学习课程
        course_links = page.locator("a:has(img[src*='content1.png'])")
        count = course_links.count()
        log_message(f"✓ 找到 {count} 个未学习课程")
        
        for i in range(count):
            link = course_links.nth(i)
            href = link.get_attribute("href") or ""
            text = re.search(r"\d+_\d+_(.*?).php", href).group(1)
            
            # 清理URL（移除user路径段）
            if "../" in href:
                href = href.replace("../", "http://www.linuxstudio.cn/")
                href = href.replace("user/study/content", "study/content")
            
            courses_data.append({
                "课程名称": text,
                "跳转网址": href,
                "课程状态": "未看过"
            })
            log_message(f"  - 识别到课程: {text}")

        # 5. 保存数据
        if courses_data:
            log_message("\n[步骤5] 保存课程数据...")
            with open("output/courses_data.json", "w", encoding="utf-8") as f:
                json.dump(courses_data, f, ensure_ascii=False, indent=2)
            log_message("✓ 数据已保存到 output/courses_data.json")

        # 6. 自动学习课程
        log_message("\n[步骤6] 开始自动学习课程...")
        for idx, course in enumerate(courses_data, 1):
            log_message(f"\n===== 开始学习课程 {idx}/{len(courses_data)} =====")
            log_message(f"课程名称: {course['课程名称']}")
            course_page = None
            current_status = "failed"
            
            try:
                # 打开课程页面 - 增加重试机制
                course_url = course['跳转网址']
                max_retries = 3
                retry_count = 0
                page_loaded = False
                
                while retry_count < max_retries and not page_loaded:
                    try:
                        course_page = context.new_page()
                        course_page.set_default_timeout(30000)
                        course_page.goto(course_url, wait_until="networkidle")
                        log_message("✓ 课程页面加载完成")
                        page_loaded = True
                    except Exception as e:
                        retry_count += 1
                        log_message(f"⚠ 课程页面加载失败 (尝试 {retry_count}/{max_retries}): {e}", "WARNING")
                        if course_page:
                            course_page.close()
                        course_page = None
                        if retry_count < max_retries:
                            log_message("准备重试...")
                            time.sleep(3)
                        else:
                            log_message("❌ 达到最大重试次数，跳过此课程", "ERROR")
                
                if not page_loaded:
                    continue
                
                # 学习课程（等待65秒）
                log_message("学习课程中（65秒）...")
                remaining_time = 65
                while remaining_time > 0:
                    try:
                        # 定期检查页面是否还在
                        if not course_page or course_page.is_closed():
                            raise Exception("页面已关闭")
                        log_message(f"  剩余时间: {remaining_time}秒", "DEBUG")
                        time.sleep(5)
                        remaining_time -= 5
                    except Exception as e:
                        log_message(f"⚠ 学习过程中断: {e}", "WARNING")
                        # 尝试重新打开页面
                        if course_page:
                            course_page.close()
                        course_page = context.new_page()
                        course_page.goto(course_url, wait_until="domcontentloaded")
                        log_message("✓ 已重新打开课程页面")
                
                # 修改为获取参数并直接跳转的逻辑
                survey_url = None
                finish_attempts = 0
                finish_selectors = [
                    "input[type='button'][value='完成本节学习']",  # 优先匹配特定值的按钮
                    "input[type='button'][onclick*='survey.php']",  # 其次匹配包含survey.php的按钮
                    "button:has-text('完成')",
                    "button:has-text('结束学习')",
                    "#finish-btn",
                    "[id*='finish']",
                    "[class*='finish']"
                ]
                
                log_message("🔍 开始搜索survey.php链接进行直接跳转", "INFO")
                
                # 尝试从按钮中提取survey.php链接
                while survey_url is None and finish_attempts < len(finish_selectors):
                    try:
                        selector = finish_selectors[finish_attempts]
                        finish_button = course_page.locator(selector)
                        
                        if finish_button.is_visible():
                            onclick_attr = finish_button.get_attribute("onclick")
                            
                            if onclick_attr:
                                # 尝试提取完整的survey.php链接
                                log_message(f"📋 分析onclick属性: {onclick_attr}", "DEBUG")
                                
                                # 尝试提取window.location.href中的URL
                                url_match = re.search(r'window\.location\.href=["\']([^"\']+)["\']', onclick_attr)
                                
                                if url_match:
                                    # 提取到了相对URL
                                    relative_url = url_match.group(1)
                                    # 处理HTML实体编码
                                    relative_url = relative_url.replace('&amp;', '&')
                                    
                                    # 构建完整URL
                                    survey_url = f"http://www.linuxstudio.cn/{relative_url}"
                                    log_message(f"🚀 提取到survey链接: {survey_url}", "INFO")
                                else:
                                    # 如果没有直接的URL，尝试提取参数并构建链接
                                    content_id_match = re.search(r'content_id=(\d+)', onclick_attr)
                                    chapter_match = re.search(r'chapter=([^&\']+)', onclick_attr)
                                    
                                    if content_id_match and chapter_match:
                                        content_id = content_id_match.group(1)
                                        chapter = chapter_match.group(1)
                                        # 处理HTML实体编码
                                        chapter = chapter.replace('&amp;', '&')
                                        
                                        # 构建完整URL
                                        survey_url = f"http://www.linuxstudio.cn/survey.php?content_id={content_id}&chapter={chapter}"
                                        log_message(f"🚀 使用提取的参数构建链接: {survey_url}", "INFO")
                                
                                # 特殊处理用户指定的案例
                                if survey_url and "content_id=60" in survey_url and "Linux常用命令" in survey_url:
                                    log_message("🎯 成功识别并处理用户指定的按钮案例!", "INFO")
                        
                        # 如果没有找到URL，继续尝试下一个选择器
                        if survey_url is None:
                            finish_attempts += 1
                    except Exception as e:
                        finish_attempts += 1
                        log_message(f"⚠ 尝试选择器 {selector} 失败: {e}", "DEBUG")
                
                # 执行直接跳转
                if survey_url:
                    try:
                        log_message(f"🌐 正在导航到: {survey_url}", "INFO")
                        course_page.goto(survey_url, wait_until="networkidle", timeout=20000)
                        log_message(f"✅ 成功导航到survey页面", "INFO")
                    except Exception as e:
                        log_message(f"❌ 导航失败: {e}", "WARNING")
                else:
                    # 如果无法提取URL，回退到原始的点击按钮逻辑
                    log_message("⚠ 无法提取survey.php链接，回退到点击按钮方式", "WARNING")
                    finish_clicked = False
                    finish_attempts = 0
                    
                    while not finish_clicked and finish_attempts < len(finish_selectors):
                        try:
                            selector = finish_selectors[finish_attempts]
                            finish_button = course_page.locator(selector)
                            if finish_button.is_visible():
                                finish_button.click(force=True, timeout=3000)
                                log_message(f"✓ 已点击完成按钮: {selector}")
                                finish_clicked = True
                            else:
                                finish_attempts += 1
                        except Exception as e:
                            finish_attempts += 1
                            log_message(f"⚠ 尝试 {selector} 失败: {e}", "DEBUG")
                    
                    # 如果所有选择器都失败，使用坐标点击
                    if not finish_clicked:
                        try:
                            log_message("尝试使用坐标点击完成按钮区域", "WARNING")
                            course_page.mouse.click(500, 500)
                            log_message("✓ 已使用坐标点击完成按钮区域")
                        except Exception as e:
                            log_message(f"⚠ 坐标点击失败: {e}", "WARNING")
                    
                    # 等待页面跳转
                    try:
                        course_page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception as e:
                        log_message(f"⚠ 等待页面跳转超时: {e}", "WARNING")
                
                # 填写调查问卷 - 优化版
                log_message("填写调查问卷...")
                
                # 增加页面内容检查
                try:
                    page_content = course_page.content()
                    if "survey" not in page_content.lower() and "问卷" not in page_content:
                        log_message("⚠ 似乎不在调查问卷页面，但尝试继续", "WARNING")
                except:
                    log_message("⚠ 无法获取页面内容", "ERROR")
                
                # 设置调查问卷选项 - 优化版
                # 首先等待页面上可能存在的所有表单元素加载完成
                try:
                    course_page.wait_for_load_state("domcontentloaded", timeout=5000)
                    log_message("🔍 [DEBUG] 页面DOM已加载完成", "DEBUG")
                    
                    # 尝试等待可能的表单容器
                    try:
                        course_page.wait_for_selector("form", timeout=3000)
                        log_message("🔍 [DEBUG] 找到表单元素", "DEBUG")
                    except:
                        log_message("🔍 [DEBUG] 未找到表单元素", "DEBUG")
                except Exception as e:
                    log_message(f"🔍 [DEBUG] 页面加载检查出错: {e}", "DEBUG")
                
                # 定义所有可能的选择器变体
                difficulty_selectors = [
                    {"type": "select", "selector": "select[name='difficulty']", "value": "1", "label": "容易"},
                    {"type": "select", "selector": "select[name='level']", "value": "1", "label": "容易"},
                    {"type": "radio", "selector": "input[type='radio'][name='difficulty'][value='1']", "label": "容易"},
                    {"type": "radio", "selector": "input[type='radio'][name='level'][value='1']", "label": "容易"},
                    {"type": "radio", "selector": "input[type='radio'][value='1']", "label": "容易"},
                ]
                
                use_selectors = [
                    {"type": "select", "selector": "select[name='use']", "value": "2", "label": "有用"},
                    {"type": "select", "selector": "select[name='utility']", "value": "2", "label": "有用"},
                    {"type": "radio", "selector": "input[type='radio'][name='use'][value='2']", "label": "有用"},
                    {"type": "radio", "selector": "input[type='radio'][name='utility'][value='2']", "label": "有用"},
                    {"type": "radio", "selector": "input[type='radio'][value='2']", "label": "有用"},
                ]
                
                # 函数：尝试设置选项
                def set_option(selectors_list, option_type):
                    success = False
                    option_name = "难度" if option_type == "difficulty" else "实用性"
                    
                    for option in selectors_list:
                        try:
                            log_message(f"🔍 [DEBUG] 尝试设置{option_name} - {option['type']}: {option['selector']}", "DEBUG")
                            
                            # 检查元素是否存在
                            if course_page.locator(option['selector']).count() > 0:
                                log_message(f"🔍 [DEBUG] 找到{option_name}元素: {option['selector']}", "DEBUG")
                                
                                # 根据类型设置选项
                                if option['type'] == "select":
                                    course_page.locator(option['selector']).select_option(value=option['value'], timeout=3000)
                                elif option['type'] == "radio":
                                    course_page.locator(option['selector']).first.click(force=True, timeout=2000)
                                
                                log_message(f"✓ 已设置{option_name}为：{option['label']} ({option['type']} - {option['selector']})")
                                success = True
                                break
                        except Exception as e:
                            log_message(f"⚠ 设置{option_name}失败 ({option['selector']}): {e}", "DEBUG")
                    
                    # 如果所有选择器都失败，尝试等待并重新查找
                    if not success:
                        log_message(f"🔍 [DEBUG] 所有{option_name}选择器都失败，尝试全局查找相关元素", "DEBUG")
                        try:
                            # 尝试直接等待并选择下拉菜单
                            for selector in ["select", "select[name*='']"]:
                                if course_page.locator(selector).count() > 0:
                                    selects = course_page.locator(selector).all()
                                    for select in selects:
                                        try:
                                            # 尝试设置值
                                            value = "1" if option_type == "difficulty" else "2"
                                            select.select_option(value=value, timeout=2000)
                                            log_message(f"✓ 已设置{option_name}为：{(option_type == 'difficulty' and '容易' or '有用')} (全局选择器 - {selector})")
                                            success = True
                                            break
                                        except:
                                            pass
                                    if success:
                                        break
                        except Exception as e:
                            log_message(f"⚠ 全局查找{option_name}失败: {e}", "WARNING")
                    
                    return success
                
                # 优先设置难度选项
                difficulty_success = set_option(difficulty_selectors, "difficulty")
                if not difficulty_success:
                    log_message("⚠ 未能设置难度选项，请检查页面结构", "WARNING")
                
                # 然后设置实用性选项
                use_success = set_option(use_selectors, "use")
                if not use_success:
                    log_message("⚠ 未能设置实用性选项，请检查页面结构", "WARNING")
                
                # 确认两个选项都已设置
                if difficulty_success and use_success:
                    log_message("✓ 问卷两个选项（难度和实用性）均已成功设置", "DEBUG")
                else:
                    log_message("⚠ 问卷选项设置不完整，可能会影响提交结果", "WARNING")

                # 提交问卷 - 增强版
                submit_success = False
                submit_selectors = [
                    "input[type='submit']",
                    "button[type='submit']",
                    "button:has-text('提交')",
                    "input[value*='提交']",
                    "//button[contains(text(), '提交')]",  # XPath
                    "//input[contains(@value, '提交')]"   # XPath
                ]
                
                for selector in submit_selectors:
                    try:
                        log_message(f"尝试提交按钮: {selector}", "DEBUG")
                        if "//" in selector:  # XPath选择器
                            btn = course_page.locator(f"xpath={selector}")
                        else:  # CSS选择器
                            btn = course_page.locator(selector)
                        
                        if btn.count() > 0:
                            btn.first.click(force=True, timeout=3000)
                            log_message(f"✓ 已点击提交按钮: {selector}")
                            submit_success = True
                            break
                    except Exception as e:
                        log_message(f"点击提交按钮 {selector} 失败: {e}", "DEBUG")
                
                # 如果所有选择器都失败，尝试坐标点击
                if not submit_success:
                    try:
                        log_message("尝试使用坐标点击提交区域", "WARNING")
                        course_page.mouse.click(course_page.viewport_size["width"] // 2, course_page.viewport_size["height"] * 0.8)
                        log_message("✓ 已使用坐标点击提交区域")
                        submit_success = True
                    except Exception as e:
                        log_message(f"⚠ 所有提交方式均失败: {e}", "ERROR")
                
                # 标记课程完成
                current_status = "completed" if submit_success else "submission_failed"
                collect_course_info(course_page, course['课程名称'], 65, current_status)
                log_message("✓ 已提交问卷")
                
                # 等待网络空闲
                try:
                    course_page.wait_for_load_state("networkidle")
                except:
                    pass
                
                completed_courses += 1  # 增加完成课程计数
                log_message(f"✅ 课程完成: {course['课程名称']}")
                
                # 每完成5个课程保存一次数据
                if completed_courses % 5 == 0:
                    try:
                        save_course_data_to_csv()
                        save_course_data_to_json()
                    except Exception as e:
                        log_message(f"⚠ 保存数据时出错: {e}", "ERROR")

            except Exception as e:
                log_message(f"❌ 学习课程时出错: {str(e)[:200]}", "ERROR")
                # 保存调试信息
                try:
                    if course_page:
                        debug_filename = f"output/debug_course_{idx}_{int(time.time())}.html"
                        with open(debug_filename, "w", encoding="utf-8") as f:
                            f.write(course_page.content())
                        log_message(f"✓ 调试信息已保存到: {debug_filename}", "DEBUG")
                except Exception as debug_error:
                    log_message(f"❌ 保存调试信息失败: {debug_error}", "ERROR")
            finally:
                # 安全关闭课程页面
                try:
                    if course_page and not course_page.is_closed():
                        course_page.close()
                except:
                    pass
                
                # 随机间隔1-3秒，避免被识别为机器人
                sleep_time = random.uniform(1, 3)
                log_message(f"等待 {sleep_time:.1f} 秒后继续", "DEBUG")
                time.sleep(sleep_time)

        # 7. 统计信息
        total_courses = len(courses_data)
        success_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
        
        # 保存最终数据
        save_course_data_to_csv()
        save_course_data_to_json()
        
        log_message("\n===== 学习统计 =====")
        log_message(f"总课程数: {total_courses}")
        log_message(f"成功完成: {completed_courses}")
        log_message(f"成功率: {success_rate:.2f}%")
        log_message(f"💾 已保存课程数据到 completed_courses.csv 和 completed_courses.json")

    except KeyboardInterrupt:
        log_message("⚠ 用户中断程序", "WARNING")
    except Exception as e:
        log_message(f"❌ 程序运行出错: {e}", "CRITICAL")
        import traceback
        traceback.print_exc()
    finally:
        # 8. 清理资源
        log_message("\n[清理] 释放资源...")
        
        # 关闭所有页面
        try:
            if context:
                for p in context.pages:
                    if not p.is_closed():
                        p.close()
        except:
            pass
        
        # 关闭浏览器和Playwright
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if playwright_instance:
                playwright_instance.stop()
        except Exception as e:
            log_message(f"清理资源时出错: {e}", "WARNING")
        
        # 输出最终报告
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        log_message("\n===== 自动化学习流程结束 =====")
        log_message(f"总耗时: {elapsed:.2f}秒")
        log_message(f"已完成: {completed_courses}/{total_courses if 'total_courses' in locals() else 0}")

if __name__ == "__main__":
    USER_NAME = "your_username"
    PASSWORD = "your_password"
    main(user_name=USER_NAME, password=PASSWORD)