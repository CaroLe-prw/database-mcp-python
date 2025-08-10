from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.factory.datasource_manager import get_manager

load_dotenv()

# Initialize MCP service
mcp = FastMCP("database-mcp")

# Get global data source manager
manager = get_manager()


@mcp.tool(description="List all configured data sources with their connection details and status")
def list_dataSources() -> str:
    """List all configured data sources with their connection information"""
    try:
        sources = manager.list_data_sources()
        if not sources:
            return "No data sources configured"

        result = []
        for name, info in sources.items():
            default_mark = " [Default]" if info['is_default'] else ""
            result.append(
                f"• {name}{default_mark}\n"
                f"  Type: {info['type']}\n"
                f"  Address: {info['host']}:{info['port']}\n"
                f"  Database: {info['database']}\n"
                f"  User: {info['user']}"
            )

        return "\n\n".join(result)
    except Exception as e:
        return f"Failed to list data sources: {str(e)}"


@mcp.tool(
    description="Switch the default data source to the specified one. Parameters: name (str) - The name of the data source to switch to")
def switch_datasource(name: str) -> str:
    """Switch the default data source
    
    Args:
        name: Name of the data source to set as default
    """
    try:
        return manager.set_default(name)
    except Exception as e:
        return f"Failed to switch data source: {str(e)}"


@mcp.tool(
    description="Get information about the current default data source including type, host, port, database and user")
def get_current_datasource() -> str:
    """Get the current default data source information"""
    try:
        current = manager.get_current_datasource()
        info = manager.get_datasource_info(current)
        return (
            f"Current default data source: {current}\n"
            f"Type: {info['type']}\n"
            f"Address: {info['host']}:{info['port']}\n"
            f"Database: {info['database']}\n"
            f"User: {info['user']}"
        )
    except Exception as e:
        return f"Failed to get current data source: {str(e)}"


@mcp.tool(
    description="List all tables in the specified database. Parameters: datasource (Optional[str]) - Name of the data source to query, uses default if not specified")
def list_tables(datasource: Optional[str] = None) -> str:
    """List all tables in the database
    
    Args:
        datasource: Optional data source name, uses default if None
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.list_tables()
    except Exception as e:
        return f"Failed to list tables: {str(e)}"


@mcp.tool(
    description="Describe the structure and columns of a specific table. Parameters: table_name (str) - Name of the table to describe; datasource (Optional[str]) - Name of the data source, uses default if not specified")
def describe_table(table_name: str, datasource: Optional[str] = None) -> str:
    """Show the schema and column information for a given table
    
    Args:
        table_name: Name of the table to describe
        datasource: Optional data source name, uses default if None
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.describe_Table(table_name)
    except Exception as e:
        return f"Failed to describe table: {str(e)}"


@mcp.tool(
    description="Execute a SQL statement and return formatted results. Parameters: sql (str) - The SQL query to execute; datasource (Optional[str]) - Name of the data source, uses default if not specified; params (Optional[tuple]) - Parameters for parameterized queries")
def execute_sql(
        sql: str,
        datasource: Optional[str] = None,
        params: Optional[tuple] = None
) -> str:
    """Execute SQL statement and return results
    
    Args:
        sql: SQL query to execute
        datasource: Optional data source name, uses default if None
        params: Optional parameters for parameterized queries
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.execute_sql(sql, params)
    except Exception as e:
        return f"Failed to execute SQL: {str(e)}"


@mcp.tool(
    description="Export table data to SQL file format. Parameters: table_name (str) - Name of the table to export; datasource (Optional[str]) - Name of the data source, uses default if not specified; file_path (Optional[str]) - Path to save the SQL file, uses default export_data/ directory if not specified")
def export_data(
        table_name: str,
        datasource: Optional[str] = None,
        file_path: Optional[str] = None
) -> str:
    """Export table data to SQL file
    
    Args:
        table_name: Name of the table to export
        datasource: Optional data source name, uses default if None
        file_path: Optional file path, defaults to export_data/ directory
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.export_data(table_name, file_path)
    except Exception as e:
        return f"Failed to export data: {str(e)}"


@mcp.tool(
    description="Execute SQL statements from a file or directory of SQL files. Parameters: file_path (str) - Path to a .sql file or directory containing .sql files; datasource (Optional[str]) - Name of the data source, uses default if not specified")
def execute_sql_file(
        file_path: str,
        datasource: Optional[str] = None
) -> str:
    """Execute SQL from file(s) - supports single .sql file or directory
    
    Args:
        file_path: Path to .sql file or directory with .sql files
        datasource: Optional data source name, uses default if None
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.execute_sql_file(file_path)
    except Exception as e:
        return f"Failed to execute SQL file: {str(e)}"


@mcp.tool(
    description="Compare table structure between two data sources and optionally generate ALTER TABLE SQL. Parameters: table_name (str) - Name of the table to compare; source1 (str) - First data source name; source2 (str) - Second data source name; generate_sql (Optional[bool]) - Whether to generate ALTER TABLE SQL statements (default: False)")
def compare_table_structure(
        table_name: str,
        source1: str,
        source2: str,
        generate_sql: Optional[bool] = False
) -> str:
    """Compare the structure of a table between two data sources
    
    Args:
        table_name: Name of the table to compare
        source1: First data source name
        source2: Second data source name
        generate_sql: Whether to generate ALTER TABLE SQL statements
    
    Returns:
        Detailed comparison report showing differences in table structure
    """
    try:
        # Get strategy objects for both data sources
        strategy1 = manager.get_data_source(source1)
        strategy2 = manager.get_data_source(source2)

        # Use MySQLStrategy's compare_table_with method
        if hasattr(strategy1, 'compare_table_with'):
            return strategy1.compare_table_with(table_name, strategy2, generate_sql)
        else:
            return f"Data source {source1} does not support table structure comparison"

    except Exception as e:
        return f"Table structure comparison failed: {str(e)}"


def main():
    """MCP Service Main Entry Point"""
    try:
        print("\n" + "=" * 50)
        print("Starting Database MCP Service...")
        print("=" * 50)

        # Data source manager will print configuration info during initialization
        sources = manager.list_data_sources()

        if not sources:
            print("Warning: No data sources configured")
        else:
            print(f"Successfully loaded {len(sources)} data sources")
            current = manager.get_current_datasource()
            print(f"Current default data source: {current}")

        print("=" * 50)
        print("Service started successfully, waiting for connections...\n")

        # Run MCP service
        mcp.run(transport='stdio')

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nPlease check configuration files or environment variable settings")
        raise


if __name__ == "__main__":
    main()
