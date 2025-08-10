# Database MCP Server

## 📋 Documentation Languages | 文档语言

[![English](https://img.shields.io/badge/English-Documentation-blue?style=for-the-badge)](./docs/README_en.md)
[![中文](https://img.shields.io/badge/中文-文档-red?style=for-the-badge)](./docs/README_zh.md)

---

## 🚀 Quick Start | 快速开始

A powerful database MCP (Model Context Protocol) server with multi-data source management and advanced SQL operations including table structure comparison and synchronization capabilities.

一个强大的数据库 MCP（模型上下文协议）服务器，支持多数据源管理和高级 SQL 操作，包括表结构对比和同步功能。

## 🎨 Key Features | 主要特性

- ✅ **Multi-Data Source Support** | **多数据源支持**
- ✅ **Table Structure Comparison** | **表结构对比**
- ✅ **SQL Generation** | **SQL 生成**
- ✅ **Data Export/Import** | **数据导出/导入**
- ✅ **Connection Pooling** | **连接池管理**

## 📚 Full Documentation | 完整文档

Please choose your preferred language for detailed documentation:

请选择您偶爱的语言查看详细文档：

### 🌍 Language Options | 语言选项

| Language | Documentation | Description |
|----------|---------------|-------------|
| 🇺🇸 English | [README_en.md](./docs/README_en.md) | Complete English documentation with installation, configuration, and usage examples |
| 🇨🇳 中文 | [README_zh.md](./docs/README_zh.md) | 完整的中文文档，包括安装、配置和使用示例 |

---

## ⚡ Quick Installation | 快速安装

```bash
# Using uv (recommended) | 使用 uv（推荐）
uvx database-mcp-server

# Or install uv first | 或者先安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
uv tool install database-mcp-server

# Traditional pip installation | 传统 pip 安装
pip install database-mcp-server
```

## 📁 Project Structure | 项目结构

```
database-mcp-python/
├── README.md                        # This file | 本文件 (多语言导航)
├── docs/                            # Documentation | 文档目录
│   ├── README_en.md                 # English documentation | 英文文档
│   └── README_zh.md                 # Chinese documentation | 中文文档
├── src/                             # Source code | 源代码
│   ├── __init__.py                  # MCP service entry | MCP 服务入口
│   ├── factory/                     # Factory pattern | 工厂模式
│   ├── strategy/                    # Strategy pattern | 策略模式
│   ├── model/                       # Data models | 数据模型
│   └── tools/                       # Utility tools | 工具类
├── test/                            # Test directory | 测试目录
│   └── test_datasource.py           # Testing script | 测试脚本
├── database-config.example.yaml     # Config example | 配置示例
├── pyproject.toml                   # Project config | 项目配置
├── uv.lock                          # UV lock file | UV 锁定文件
├── CLAUDE.md                        # Project notes | 项目说明
└── LICENSE                          # MIT License | MIT 许可证
```

## 🔗 Quick Links | 快速链接

- [📖 English Documentation](./docs/README_en.md) - Complete setup and usage guide
- [📖 中文文档](./docs/README_zh.md) - 完整安装和使用指南
- [💾 Installation Guide](./docs/README_en.md#installation) - How to install and configure
- [🔧 Configuration](./docs/README_en.md#configuration) - Setup your data sources
- [📚 Usage Examples](./docs/README_en.md#usage-examples) - Learn with examples
- [🔄 Table Comparison](./docs/README_en.md#advanced-table-structure-management) - Advanced features

---

### 📄 License | 许可证

MIT License

### 🤝 Contributing | 贡献

Issues and Pull Requests are welcome! | 欢迎提交 Issue 和 Pull Request！

