# Database MCP Server - 中文文档

[![English](https://img.shields.io/badge/English-Documentation-blue)](./README_en.md) | [![Home](https://img.shields.io/badge/Home-Navigate-green)](../README.md)

一个强大的数据库 MCP（模型上下文协议）服务器，支持多数据源管理和高级 SQL 操作，包括表结构对比和同步功能。

## 功能特性

- ✅ **多数据源支持**：同时连接和管理多个数据库
- ✅ **灵活配置**：支持 YAML/JSON 配置文件和环境变量
- ✅ **向后兼容**：保持原有单数据源配置方式
- ✅ **动态数据源切换**：动态切换默认数据源
- ✅ **批量操作**：在多个数据源上执行操作
- ✅ **表结构对比**：比较不同数据源之间的表结构差异
- ✅ **SQL 生成**：生成 ALTER TABLE 语句用于架构同步
- ✅ **数据导出/导入**：支持表数据导出和 SQL 文件执行
- ✅ **连接池管理**：高效的数据库连接管理

## 支持的数据库

- ✅ MySQL / MariaDB
- 🔄 PostgreSQL（计划中）
- 🔄 Oracle（计划中）
- 🔄 SQL Server（计划中）

## 安装

```bash
# 使用 pip 安装
pip install database-mcp-server

# 或使用 uv
uvx database-mcp-server
```

## 配置方式

### 方式一：多数据源配置（推荐）

创建 `database-config.yaml` 文件：

```yaml
# 数据源配置
datasources:
  # 主数据库
  main_db:
    type: mysql
    host: 192.168.1.10
    port: 3306
    user: root
    password: your_password
    database: production_db
    # 可选：连接池配置
    minCached: 1
    maxCached: 10
    maxConnections: 100

  # 分析数据库
  analytics_db:
    type: mysql
    host: 192.168.1.20
    port: 3306
    user: analyst
    password: analyst_password
    database: analytics_db

  # 测试数据库
  test_db:
    type: mysql
    host: localhost
    port: 3306
    user: test_user
    password: test_password
    database: test_db

# 默认数据源
default: main_db
```

### 方式二：单数据源配置（向后兼容）

创建 `.env` 文件：

```bash
db_type="mysql"
host="localhost"
port="3306"
user="root"
password="password"
database="my_database"
```

### 方式三：自定义配置文件路径

在 `.env` 中设置：

```bash
DATABASE_CONFIG_FILE="./config/my-database-config.yaml"
```

## MCP 工具函数

### 数据源管理

- `list_dataSources()` - 列出所有配置的数据源及其连接详情
- `switch_datasource(name)` - 切换默认数据源
- `get_current_datasource()` - 获取当前默认数据源信息

### 数据库操作

- `list_tables(datasource=None)` - 列出数据库中的所有表
- `describe_table(table_name, datasource=None)` - 显示表结构及详细字段信息
- `execute_sql(sql, datasource=None, params=None)` - 执行 SQL 语句，支持参数化查询
- `export_data(table_name, datasource=None, file_path=None)` - 将表数据导出为 INSERT SQL 语句
- `execute_sql_file(file_path, datasource=None)` - 执行 SQL 文件或 SQL 文件目录

### 高级功能

- `compare_table_structure(table_name, source1, source2, generate_sql=False)` - 比较数据源间的表结构并可选择生成 ALTER TABLE 语句

## 使用示例

### Claude Desktop 配置

编辑 Claude Desktop 配置文件：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "database": {
      "command": "uvx",
      "args": [
        "database-mcp-server"
      ],
      "env": {
        "DATABASE_CONFIG_FILE": "C:/path/to/database-config.yaml"
      }
    }
  }
}
```

### 基本操作

1. **列出所有数据源**
```
使用 list_dataSources 工具
```

2. **切换数据源**
```
使用 switch_datasource 工具，参数 name="analytics_db"
```

3. **在特定数据源执行 SQL**
```
使用 execute_sql 工具，参数：
- sql: "SELECT * FROM users LIMIT 10"
- datasource: "test_db"
```

4. **导出和导入表数据**
```
从源数据源导出：
使用 export_data 工具，参数：
- table_name: "users"
- datasource: "main_db"

导入到目标数据源：
使用 execute_sql_file 工具，参数：
- file_path: "./export_data/users.sql"
- datasource: "analytics_db"
```

### 高级表结构管理

1. **比较表结构**
```
使用 compare_table_structure 工具，参数：
- table_name: "users"
- source1: "main_db"
- source2: "test_db"
- generate_sql: false
```

2. **生成 ALTER TABLE 语句**
```
使用 compare_table_structure 工具，参数：
- table_name: "users"
- source1: "main_db"
- source2: "test_db"
- generate_sql: true
```

执行后会：
- 比较两个数据源之间的表结构
- 生成用于从 source1 同步到 source2 的 ALTER TABLE SQL 语句
- 将 SQL 语句保存到 export_data 目录的时间戳文件中
- 返回包含统计信息的详细对比报告

## 配置优先级

1. 如果存在 `database-config.yaml`（或通过 `DATABASE_CONFIG_FILE` 指定的文件），使用该配置
2. 如果不存在配置文件但 `.env` 中有数据库配置，使用 `.env`（单数据源模式）
3. 两者都没有时抛出配置错误

## 项目结构

```
database-mcp-python/
├── src/
│   ├── __init__.py                  # MCP 服务主入口
│   ├── factory/
│   │   ├── config_loader.py         # 带缓存的配置加载器
│   │   ├── database_factory.py      # 数据库策略工厂
│   │   └── datasource_manager.py    # 多数据源管理器
│   ├── strategy/
│   │   ├── database_strategy.py     # 抽象数据库策略基类
│   │   └── mysql_strategy.py        # MySQL 策略实现
│   ├── model/
│   │   └── database_config.py       # 数据库配置模型
│   └── tools/
│       └── mysql_tools.py           # MySQL SQL 生成工具方法
├── database-config.example.yaml    # 配置文件示例
├── .env.example                     # 环境变量示例
├── pyproject.toml                   # 项目配置
├── test_datasource.py               # 测试脚本
└── README.md                        # 英文说明文档
```

## 关键功能详述

### 表结构对比

`compare_table_structure` 工具提供跨不同数据源的表结构全面对比：

- **字段分析**：识别每个数据源独有的字段
- **属性比较**：比较数据类型、是否可空、键值、默认值和额外属性
- **SQL 生成**：可选择生成用于同步的 ALTER TABLE 语句
- **详细报告**：提供统计信息和格式化的比较结果

### 连接池管理

可配置的高效数据库连接管理：

- `minCached`：最小缓存连接数
- `maxCached`：最大缓存连接数
- `maxConnections`：最大总连接数

### 错误处理

应用程序全面的错误处理机制：

- 控制台输出支持 Unicode 字符
- 错误时事务回滚
- 提供详细的上下文错误消息

## 开发

```bash
# 克隆仓库
git clone https://github.com/your-username/database-mcp-python.git
cd database-mcp-python

# 安装依赖
pip install -e .

# 运行测试
python test_datasource.py
```

## 测试

项目包含一个全面的测试脚本（`test_datasource.py`），演示了：

- 多数据源配置
- 表结构对比
- SQL 生成功能
- 错误处理场景

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.1

- 增强表结构对比功能
- 添加 ALTER TABLE SQL 生成
- 改进错误处理和 Unicode 支持
- 添加 MySQL 工具类用于 SQL 操作
- 完整的代码国际化为英文
- 增强文档和代码注释

### v1.0.0

- 多数据源支持
- YAML/JSON 配置文件支持
- 数据源管理工具
- 保持向后兼容
- 基本 SQL 操作功能