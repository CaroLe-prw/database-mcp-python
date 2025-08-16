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
- ✅ PostgreSQL
- ✅ Oracle
- ✅ SQLite
- 🔄 SQL Server（计划中）

## 依赖要求

### 必需依赖

- **Python 3.7+**
- **MySQL/MariaDB**: `mysql-connector-python`（自动安装）
- **PostgreSQL**: `psycopg2-binary`（自动安装）
- **Oracle**: `oracledb>=2.0.0`（自动安装）- Oracle 瘦客户端，无需安装 Oracle Client
- **SQLite**: Python 内置支持，无需额外依赖
- **连接池**: `DBUtils`（自动安装）

### 数据库驱动说明

- **Oracle**: 使用新的 `oracledb` 驱动的瘦模式，无需安装 Oracle Client
- **SQLite**: 使用 Python 内置的 `sqlite3` 模块，支持连接池
- **MySQL/PostgreSQL**: 标准驱动，功能完整

## 安装

### 方式一：使用 uv（推荐）

[uv](https://docs.astral.sh/uv/) 是用 Rust 编写的快速 Python 包安装器和解析器。

```bash
# 首先安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或在 Windows 上
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 使用 uvx 直接运行（无需安装）
uvx database-mcp-server

# 或者全局安装
uv tool install database-mcp-server
```

### 方式二：使用 pip

```bash
# 使用 pip 安装
pip install database-mcp-server
```

### 方式三：开发环境安装

```bash
# 克隆仓库
git clone https://github.com/your-username/database-mcp-python.git
cd database-mcp-python

# 使用 uv 安装
uv sync
uv run python -m src

# 或使用 pip 安装
pip install -e .
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

  # PostgreSQL 数据库
  postgres_db:
    type: postgresql  # 使用 'postgresql'
    host: localhost
    port: 5432
    user: postgres
    password: postgres_password
    database: my_database  # PostgreSQL 实际数据库名
    # 可选：连接池配置
    minCached: 5
    maxCached: 10
    maxConnections: 20

  # Oracle 数据库
  oracle_db:
    type: oracle
    host: localhost
    port: 1521
    user: system
    password: oracle_password
    database: xe  # Oracle 数据库名
    # 可选：连接池配置
    minCached: 2
    maxCached: 8
    maxConnections: 15

  # SQLite 数据库
  sqlite_db:
    type: sqlite
    database: /path/to/database.db  # SQLite 数据库文件路径
    # 可选：连接池配置
    minCached: 1
    maxCached: 10
    maxConnections: 100

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

#### 方式一：使用配置文件（推荐，支持多数据源）

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

#### 方式二：使用环境变量（单数据源，向后兼容）

```json
{
  "mcpServers": {
    "database": {
      "command": "uvx",
      "args": [
        "database-mcp-server"
      ],
      "env": {
        "db_type": "mysql",
        "host": "localhost",
        "port": "3306",
        "user": "root",
        "password": "password",
        "database": "my_database"
      }
    }
  }
}
```

注意：如果同时存在 `DATABASE_CONFIG_FILE` 和数据库连接环境变量，优先使用配置文件。

### Cursor 配置

编辑 Cursor 配置文件：

**Windows**: `%APPDATA%\Cursor\User\globalStorage\cursor-ai\settings.json`
**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/cursor-ai/settings.json`

#### 方式一：使用配置文件（推荐，支持多数据源）

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

#### 方式二：使用环境变量（单数据源，向后兼容）

```json
{
  "mcpServers": {
    "database": {
      "command": "uvx",
      "args": [
        "database-mcp-server"
      ],
      "env": {
        "db_type": "oracle",
        "host": "localhost",
        "port": "1521",
        "user": "system",
        "password": "password",
        "database": "xe"
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
├── README.md                        # 多语言导航主页
├── docs/                            # 文档目录
│   ├── README_en.md                 # 完整英文文档
│   └── README_zh.md                 # 完整中文文档
├── src/                             # 源代码目录
│   ├── __init__.py                  # MCP 服务主入口
│   ├── factory/                     # 工厂模式实现
│   │   ├── __init__.py
│   │   ├── config_loader.py         # 带缓存的配置加载器
│   │   ├── database_factory.py      # 数据库策略工厂
│   │   └── datasource_manager.py    # 多数据源管理器
│   ├── strategy/                    # 策略模式实现
│   │   ├── __init__.py
│   │   ├── database_strategy.py     # 抽象数据库策略基类
│   │   ├── mysql_strategy.py        # MySQL 策略实现
│   │   ├── oracle_strategy.py       # Oracle 策略实现
│   │   ├── postgresql_strategy.py   # PostgreSQL 策略实现
│   │   └── sqlite_strategy.py       # SQLite 策略实现
│   ├── model/                       # 数据模型定义
│   │   ├── __init__.py
│   │   └── database_config.py       # 数据库配置模型
│   └── tools/                       # 工具类和辅助函数
│       ├── common_tools.py          # 通用数据库工具方法
│       ├── mysql_tools.py           # MySQL SQL 生成工具方法
│       ├── oracle_tools.py          # Oracle SQL 生成工具方法
│       ├── postgresql_tools.py      # PostgreSQL SQL 生成工具方法
│       └── sqlite_tools.py          # SQLite SQL 生成工具方法
├── test/                            # 测试目录
│   └── test_datasource.py           # 综合测试脚本
├── database-config.example.yaml    # 配置文件示例
├── pyproject.toml                   # Python 项目配置
├── uv.lock                          # UV 包管理器锁定文件
├── package.json                     # Node.js 配置（可选）
├── package-lock.json                # Node.js 依赖锁定（可选）
├── CLAUDE.md                        # Claude 项目说明
└── LICENSE                          # MIT 许可证文件
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

### 使用 uv（推荐）

```bash
# 克隆仓库
git clone https://github.com/your-username/database-mcp-python.git
cd database-mcp-python

# 使用 uv 安装依赖
uv sync

# 运行测试
uv run python test/test_datasource.py

# 或运行 MCP 服务器
uv run python -m src
```

### 使用 pip（传统方式）

```bash
# 克隆仓库
git clone https://github.com/your-username/database-mcp-python.git
cd database-mcp-python

# 安装依赖
pip install -e .

# 运行测试
python test/test_datasource.py
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

### v1.0.3

- ✅ **SQLite 数据库支持**：完整的 SQLite 数据库支持实现
- ✅ **增强文档**：添加全面的英文方法文档
- ✅ **代码质量改进**：为 Oracle 添加缺失的 parse_table_structure 方法
- ✅ **配置更新**：为所有配置方式添加 SQLite 配置示例
- ✅ **连接池管理**：SQLite 专用连接池，支持 check_same_thread=False

### v1.0.2

- ✅ **Oracle 数据库支持**：完整的 Oracle 数据库支持实现，使用 oracledb 驱动
- ✅ **增强配置**：为所有配置方式添加 Oracle 配置示例
- ✅ **连接池管理**：Oracle 专用连接池优化
- ✅ **SQL 生成**：Oracle ALTER TABLE 语句生成支持
- ✅ **数据导出/导入**：Oracle 兼容的数据导出和 SQL 文件执行

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