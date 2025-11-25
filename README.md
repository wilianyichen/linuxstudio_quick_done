# LinuxClass 自动化学习工具

## 项目简介

LinuxClass 是一个用于自动化学习 Linux Studio 平台课程的工具，旨在帮助用户高效完成课程学习任务。该工具能够自动提取课程列表、爬取课程数据并进行模拟学习，支持多种文件格式输出，为用户提供便捷的课程管理解决方案。

## 功能特点

- **自动课程提取**：从 Linux Studio 平台自动提取课程列表和相关信息
- **智能课程爬取**：自动爬取课程内容并记录学习进度
- **多种输出格式**：支持 JSON 和 CSV 格式的数据输出
- **灵活的配置选项**：通过配置文件自定义学习参数
- **完善的日志记录**：详细记录学习过程和结果
- **自动资源管理**：自动创建输出目录，保证文件组织规范

## 核心价值

- **提高学习效率**：自动化完成课程学习过程，节省时间和精力
- **数据可视化**：将课程数据导出为结构化格式，便于分析和管理
- **灵活定制**：通过配置文件轻松调整学习策略
- **跨平台兼容**：支持 Windows 等主流操作系统
- **易于扩展**：模块化设计，便于功能扩展和定制

## 环境要求

- Python 3.8+ 
- Git（用于版本控制）
- 网络连接（用于访问 Linux Studio 平台）

## 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/linuxclass-auto.git
   cd linuxclass-auto
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows：
     ```bash
     venv\Scripts\activate
     ```
   - Linux/macOS：
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

5. **配置 Playwright 浏览器驱动**
   ```bash
   playwright install
   ```

## 使用说明

### 1. 配置文件设置

编辑 `config.txt` 文件，设置相关参数：

```ini
[DEFAULT]
# 学习课程列表，多个课程用逗号分隔
COURSE_LIST = introduction,bioinfo
# 学习时间间隔（秒）
LEARN_INTERVAL = 5
# 学习模式：normal 或 fast
LEARN_MODE = normal
```

### 2. 运行程序

```bash
python main.py
```

### 3. 查看结果

程序执行完成后，在 `output` 目录中查看生成的文件：
- `completed_courses.json`：JSON 格式的已完成课程数据
- `completed_courses.csv`：CSV 格式的已完成课程数据
- `courses_data.json`：完整的课程列表数据

## 示例代码

### 基本使用

```python
# 直接运行主程序
python main.py
```

### 自定义配置

```python
# 修改 config.txt 文件中的参数
# 例如：设置学习间隔为 10 秒
LEARN_INTERVAL = 10

# 然后运行程序
python main.py
```

## 项目结构

```
linuxclass-auto/
├── config.txt           # 配置文件，用于设置学习参数
├── course_content_extractor.py  # 课程内容提取模块
├── course_scraper.py    # 课程爬取模块
├── main.py              # 主程序入口
├── output/              # 输出目录，存放生成的文件
├── requirements.txt     # 依赖包列表
└── README.md            # 项目说明文档
```

## 关键文件解释

| 文件名 | 功能描述 |
|--------|----------|
| `main.py` | 程序主入口，负责加载配置、初始化模块和执行学习流程 |
| `course_content_extractor.py` | 提取课程内容和相关信息 |
| `course_scraper.py` | 爬取课程数据并记录学习进度 |
| `config.txt` | 配置文件，用于自定义学习参数 |
| `requirements.txt` | 项目依赖包列表 |

## 贡献指南

欢迎对本项目进行贡献！以下是贡献的基本步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m 'Add new feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 提交 Pull Request

### 代码规范

- 遵循 PEP 8 代码规范
- 添加必要的注释和文档
- 确保代码可测试性
- 保持代码简洁和可读性

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 问题反馈

如果您在使用过程中遇到问题或有改进建议，欢迎通过以下方式反馈：

- **GitHub Issues**：[提交 Issue](https://github.com/your-username/linuxclass-auto/issues)
- **电子邮件**：your-email@example.com
- **项目地址**：https://github.com/your-username/linuxclass-auto

## 更新日志

### v1.0.0（2025-11-24）

- 初始版本发布
- 实现课程自动提取和爬取功能
- 支持 JSON 和 CSV 格式输出
- 完善的配置选项
- 自动创建输出目录

## 致谢

感谢所有为本项目做出贡献的开发者和用户！

## 免责声明

本工具仅用于学习和研究目的，请勿用于任何违反平台规定或法律法规的行为。使用本工具产生的一切后果由使用者自行承担。