#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Studio自动化学习主程序
整合课程内容提取和课程爬取功能
"""

import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Config:
    """配置类，用于从配置文件读取参数"""
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """从配置文件读取配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    # 解析配置项
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 处理布尔值
                        if value.lower() in ('true', 'false'):
                            self.config_data[key] = value.lower() == 'true'
                        else:
                            # 处理字符串值（去除引号）
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            self.config_data[key] = value
            logger.info(f"成功从配置文件加载 {len(self.config_data)} 个配置项")
        except FileNotFoundError:
            logger.error(f"配置文件 {self.config_file} 不存在")
            raise
        except Exception as e:
            logger.error(f"加载配置文件时出错: {str(e)}")
            raise
    
    def get(self, key, default=None):
        """获取配置项，支持默认值"""
        return self.config_data.get(key, default)
    
    def __getattr__(self, name):
        """支持通过属性访问配置项"""
        if name in self.config_data:
            return self.config_data[name]
        raise AttributeError(f"配置项 {name} 不存在")

def main():
    """主函数"""
    start_time = datetime.now()
    logger.info("===== 开始执行Linux Studio自动化学习流程 =====")
    logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    os.makedirs("output", exist_ok=True)
    
    # 配置文件路径（使用相对路径）
    config_path = "config.txt"
    
    try:
        # 1. 加载配置文件
        logger.info("\n[步骤1] 加载配置文件...")
        config = Config(config_path)
        
        # 验证必要的配置项
        required_configs = ['USER_NAME', 'PASSWORD']
        for config_item in required_configs:
            if config_item not in config.config_data:
                logger.error(f"配置文件缺少必要项: {config_item}")
                sys.exit(1)
        
        # 2. 调用course_content_extractor.py的核心功能
        logger.info("\n[步骤2] 执行课程内容提取...")
        try:
            # 动态导入模块
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from course_content_extractor import main as extract_main
            extract_main(config.USER_NAME, config.PASSWORD)
            logger.info("课程内容提取完成")
        except ImportError as e:
            logger.error(f"导入course_content_extractor模块失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"执行课程内容提取时出错: {str(e)}")
            raise
        
        # 3. 调用course_scraper.py的核心功能
        logger.info("\n[步骤3] 执行课程信息爬取...")
        try:
            from course_scraper import main as scraper_main
            scraper_main(config.USER_NAME, config.PASSWORD)
            logger.info("课程信息爬取完成")
        except ImportError as e:
            logger.error(f"导入course_scraper模块失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"执行课程信息爬取时出错: {str(e)}")
            raise
        
        end_time = datetime.now()
        logger.info(f"\n===== 自动化学习流程执行完成 =====")
        logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总执行时间: {end_time - start_time}")
        
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n程序执行出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()