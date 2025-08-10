# Database MCP Server - English Documentation

[![中文](https://img.shields.io/badge/中文-文档-red)](./README_zh.md) | [![Home](https://img.shields.io/badge/Home-Navigate-green)](../README.md)

A powerful database MCP (Model Context Protocol) server with multi-data source management and advanced SQL operations including table structure comparison and synchronization capabilities.

## Features

- ✅ **Multi-Data Source Support**: Connect and manage multiple databases simultaneously
- ✅ **Flexible Configuration**: Support for YAML/JSON configuration files and environment variables
- ✅ **Backward Compatibility**: Maintains original single data source configuration
- ✅ **Dynamic Data Source Switching**: Switch default data source dynamically
- ✅ **Batch Operations**: Execute operations across multiple data sources
- ✅ **Table Structure Comparison**: Compare table structures between different data sources
- ✅ **SQL Generation**: Generate ALTER TABLE statements for schema synchronization
- ✅ **Data Export/Import**: Support table data export and SQL file execution
- ✅ **Connection Pooling**: Efficient database connection management

## Supported Databases

- ✅ MySQL / MariaDB
- 🔄 PostgreSQL (planned)
- 🔄 Oracle (planned)
- 🔄 SQL Server (planned)

## Installation

```bash
# Install using pip
pip install database-mcp-server

# Or using uv
uvx database-mcp-server
```

## Configuration

### Method 1: Multi-Data Source Configuration (Recommended)

Create `database-config.yaml` file:

```yaml
# Data source configuration
datasources:
  # Main database
  main_db:
    type: mysql
    host: 192.168.1.10
    port: 3306
    user: root
    password: your_password
    database: production_db
    # Optional: connection pool settings
    minCached: 1
    maxCached: 10
    maxConnections: 100

  # Analytics database
  analytics_db:
    type: mysql
    host: 192.168.1.20
    port: 3306
    user: analyst
    password: analyst_password
    database: analytics_db

  # Test database
  test_db:
    type: mysql
    host: localhost
    port: 3306
    user: test_user
    password: test_password
    database: test_db

# Default data source
default: main_db
```

### Method 2: Single Data Source Configuration (Backward Compatible)

Create `.env` file:

```bash
db_type="mysql"
host="localhost"
port="3306"
user="root"
password="password"
database="my_database"
```

### Method 3: Custom Configuration File Path

Set in `.env`:

```bash
DATABASE_CONFIG_FILE="./config/my-database-config.yaml"
```

## MCP Tools

### Data Source Management

- `list_dataSources()` - List all configured data sources with connection details
- `switch_datasource(name)` - Switch default data source
- `get_current_datasource()` - Get current default data source information

### Database Operations

- `list_tables(datasource=None)` - List all tables in database
- `describe_table(table_name, datasource=None)` - Display table structure with detailed column information
- `execute_sql(sql, datasource=None, params=None)` - Execute SQL statements with optional parameters
- `export_data(table_name, datasource=None, file_path=None)` - Export table data as INSERT SQL statements
- `execute_sql_file(file_path, datasource=None)` - Execute SQL file or directory of SQL files

### Advanced Features

- `compare_table_structure(table_name, source1, source2, generate_sql=False)` - Compare table structures between data sources and optionally generate ALTER TABLE statements

## Usage Examples

### Claude Desktop Configuration

Edit Claude Desktop configuration file:

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

### Basic Operations

1. **List All Data Sources**
```
Use list_dataSources tool
```

2. **Switch Data Source**
```
Use switch_datasource tool with parameter name="analytics_db"
```

3. **Execute SQL on Specific Data Source**
```
Use execute_sql tool with parameters:
- sql: "SELECT * FROM users LIMIT 10"
- datasource: "test_db"
```

4. **Export and Import Table Data**
```
Export from source:
Use export_data tool with parameters:
- table_name: "users"
- datasource: "main_db"

Import to target:
Use execute_sql_file tool with parameters:
- file_path: "./export_data/users.sql"
- datasource: "analytics_db"
```

### Advanced Table Structure Management

1. **Compare Table Structures**
```
Use compare_table_structure tool with parameters:
- table_name: "users"
- source1: "main_db"
- source2: "test_db"
- generate_sql: false
```

2. **Generate ALTER TABLE Statements**
```
Use compare_table_structure tool with parameters:
- table_name: "users"
- source1: "main_db"
- source2: "test_db"
- generate_sql: true
```

This will:
- Compare table structures between the two data sources
- Generate ALTER TABLE SQL statements to synchronize from source1 to source2
- Save SQL statements to timestamped files in the export_data directory
- Return detailed comparison report with statistics

## Configuration Priority

1. If `database-config.yaml` exists (or file specified via `DATABASE_CONFIG_FILE`), use that configuration
2. If no configuration file exists but `.env` has database settings, use `.env` (single data source mode)
3. If neither exists, throw configuration error

## Project Structure

```
database-mcp-python/
├── src/
│   ├── __init__.py                  # MCP service main entry point
│   ├── factory/
│   │   ├── config_loader.py         # Configuration loader with caching
│   │   ├── database_factory.py      # Database strategy factory
│   │   └── datasource_manager.py    # Multi-data source manager
│   ├── strategy/
│   │   ├── database_strategy.py     # Abstract database strategy base class
│   │   └── mysql_strategy.py        # MySQL strategy implementation
│   ├── model/
│   │   └── database_config.py       # Database configuration model
│   └── tools/
│       └── mysql_tools.py           # MySQL utility methods for SQL generation
├── database-config.example.yaml    # Configuration file example
├── .env.example                     # Environment variables example
├── pyproject.toml                   # Project configuration
├── test_datasource.py               # Testing script
└── README.md                        # Multi-language navigation
```

## Key Features in Detail

### Table Structure Comparison

The `compare_table_structure` tool provides comprehensive comparison between table structures across different data sources:

- **Column Analysis**: Identifies columns unique to each data source
- **Attribute Comparison**: Compares data types, nullability, keys, defaults, and extra attributes
- **SQL Generation**: Optionally generates ALTER TABLE statements for synchronization
- **Detailed Reporting**: Provides statistics and formatted comparison results

### Connection Pooling

Efficient database connection management with configurable pooling:

- `minCached`: Minimum cached connections
- `maxCached`: Maximum cached connections  
- `maxConnections`: Maximum total connections

### Error Handling

Robust error handling throughout the application:

- Unicode character support for console output
- Transaction rollback on errors
- Detailed error messages with context

## Development

```bash
# Clone repository
git clone https://github.com/your-username/database-mcp-python.git
cd database-mcp-python

# Install dependencies
pip install -e .

# Run tests
python test_datasource.py
```

## Testing

The project includes a comprehensive testing script (`test_datasource.py`) that demonstrates:

- Multi-data source configuration
- Table structure comparison
- SQL generation capabilities
- Error handling scenarios

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Changelog

### v1.0.1

- Enhanced table structure comparison functionality
- Added ALTER TABLE SQL generation
- Improved error handling and Unicode support
- Added MySQL utility tools for SQL operations
- Complete code internationalization to English
- Enhanced documentation and code comments

### v1.0.0

- Multi-data source support
- YAML/JSON configuration file support
- Data source management tools
- Backward compatibility maintained
- Basic SQL operations functionality