import datetime
import decimal
import math
import os

import pymysql
from dbutils.pooled_db import PooledDB

from src.model import DatabaseConfig
from src.strategy.database_strategy import DatabaseStrategy
from src.tools.mysql_tools import MySQLTools


class MySQLStrategy(DatabaseStrategy):

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.pool = None

    def create_pool(self) -> PooledDB:
        if not self.pool:
            self.pool = PooledDB(
                creator=pymysql,
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                mincached=self.config.minCached or 5,
                maxcached=self.config.maxCached or 10,
                maxconnections=self.config.maxConnections or 20,
            )
        return self.pool

    def get_connection(self) -> pymysql.connections.Connection:
        if not self.pool:
            self.create_pool()
        return self.pool.connection()

    def close_connection(self, connection: object) -> None:
        if connection:
            connection.close()

    def list_tables(self) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # Query all table names and comments from current database
                cursor.execute(
                    """
                    SELECT TABLE_NAME, TABLE_COMMENT
                    FROM information_schema.tables
                    WHERE TABLE_SCHEMA = %s
                    """,
                    (self.config.database,),
                )
            tables = cursor.fetchall()

            # Set headers and format output
            headers = ["TABLE_NAME", "TABLE_COMMENT"]
            return self.format_table(headers, list(tables))
        finally:
            self.close_connection(connection)

    def describe_Table(self, table_name: str) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # Query basic field information of the table
                cursor.execute(
                    """
                    SELECT COLUMN_NAME,
                           COLUMN_COMMENT,
                           DATA_TYPE,
                           COLUMN_TYPE,
                           COLUMN_DEFAULT,
                           COLUMN_KEY,
                           IS_NULLABLE,
                           EXTRA
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = %s;
                    """,
                    (
                        self.config.database,
                        table_name,
                    ),
                )
                table_infos = cursor.fetchall()

                result_infos = []

                # Query index information for each field
                for table_info in table_infos:
                    cursor.execute(
                        """
                        SELECT INDEX_NAME
                        FROM INFORMATION_SCHEMA.STATISTICS
                        WHERE TABLE_SCHEMA = %s
                          AND TABLE_NAME = %s
                          AND COLUMN_NAME = %s
                        """,
                        (
                            self.config.database,
                            table_name,
                            table_info[0],  # COLUMN_NAME
                        ),
                    )
                    index_results = cursor.fetchall()

                    # Extract index name list
                    index_names = [row[0] for row in index_results]

                    # If there are indexes, add index names to KEY column
                    if index_names:
                        info_list = list(table_info)
                        if info_list[5]:  # COLUMN_KEY field
                            info_list[5] = f"{info_list[5]} ({', '.join(index_names)})"
                        result_infos.append(tuple(info_list))
                    else:
                        result_infos.append(table_info)

                # Set headers
                headers = [
                    "COLUMN_NAME",  # Field name
                    "COLUMN_COMMENT",  # Field comment
                    "DATA_TYPE",  # Data type
                    "COLUMN_TYPE",  # Complete type definition
                    "COLUMN_DEFAULT",  # Default value
                    "COLUMN_KEY",  # Key type (with index info)
                    "IS_NULLABLE",  # Is nullable
                    "EXTRA",  # Extra attributes
                ]
            return self.format_table(headers, result_infos)
        finally:
            self.close_connection(connection)

    def execute_sql(self, sql: str, params: tuple = None) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql_stripped = sql.strip()

                # Distinguish SELECT queries from other statements
                if sql_stripped.upper().startswith("SELECT"):
                    # SELECT query: return result set
                    cursor.execute(sql_stripped, params)
                    column_names = [desc[0] for desc in cursor.description]
                    result = cursor.fetchall()
                    return self.format_table(column_names, list(result))
                else:
                    # DML/DDL statements: execute in transaction
                    connection.begin()
                    affected_rows = cursor.execute(sql_stripped, params)
                    connection.commit()
                    return self.format_update(affected_rows)
        finally:
            self.close_connection(connection)

    def export_data(self, table_name: str, file_path: str = None) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                if not table_name.replace('_', '').replace('-', '').isalnum():
                    raise ValueError(f"Invalid table name: {table_name}")

                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM `{table_name}`
                    """
                )
                count = cursor.fetchone()[0]
                if count < 0:
                    return f"Table '{table_name}' has no data."

                if not file_path:
                    # Use relative path from script directory, ensure creation under project root
                    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    file_path = os.path.join(script_dir, "export_data")

                # Ensure directory exists
                os.makedirs(file_path, exist_ok=True)

                # Split count into batches of 1000 records per file
                batch_size = 1000
                file_count = math.ceil(count / batch_size)

                for i in range(file_count):
                    start = i * batch_size
                    end = min((i + 1) * batch_size, count)
                    cursor.execute(
                        f"""
                        SELECT *
                        FROM `{table_name}`
                        LIMIT {start}, {end - start}
                        """
                    )
                    rows = cursor.fetchall()

                    if not rows:
                        continue

                    headers = [desc[0] for desc in cursor.description]

                    # Assemble into insert sql
                    insert_values = []
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, str):
                                # Escape single quotes and add quotes
                                escaped_val = val.replace("'", "''")
                                values.append(f"'{escaped_val}'")
                            elif isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
                                # Date time types need quotes
                                values.append(f"'{val}'")
                            elif isinstance(val, bytes):
                                # Convert binary data to hexadecimal
                                hex_val = val.hex()
                                values.append(f"0x{hex_val}")
                            elif isinstance(val, bool):
                                # Convert boolean values to 1 or 0
                                values.append("1" if val else "0")
                            elif isinstance(val, (int, float, decimal.Decimal)):
                                # Convert numeric types directly to string
                                values.append(str(val))
                            else:
                                # Handle other types as strings
                                escaped_val = str(val).replace("'", "''")
                                values.append(f"'{escaped_val}'")
                        insert_values.append(f"({', '.join(values)})")

                    insert_sql = f"INSERT INTO `{table_name}` (`{'`, `'.join(headers)}`) VALUES "
                    insert_sql += ", ".join(insert_values) + ";"

                    # Write to file, ensure correct path
                    file_name = os.path.join(file_path, f"{table_name}_{i}.sql")
                    with open(file_name, "w", encoding='utf-8') as f:
                        f.write(insert_sql)

                return f"Exported {count} rows to {file_path}."
        finally:
            self.close_connection(connection)

    def execute_sql_file(self, file_path: str) -> str:
        connection = self.get_connection()
        connection.begin()
        affected_rows = 0
        try:
            with connection.cursor() as cursor:
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                if os.path.isdir(file_path):
                    sql_content = self.read_all_files(file_path)
                    for sql in sql_content:
                        result = cursor.execute(sql)
                        # ALTER TABLE statements return 0, but we count as successful execution
                        if sql.strip().upper().startswith('ALTER TABLE'):
                            affected_rows += 1
                        elif result:
                            affected_rows += result
                else:
                    if not file_path.endswith('.sql'):
                        raise ValueError(f"Invalid file type: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Split SQL statements (by semicolon)
                        statements = content.split(';')
                        for statement in statements:
                            sql_stripped = statement.strip()
                            # Skip empty statements
                            if sql_stripped:
                                result = cursor.execute(sql_stripped)
                                # ALTER TABLE statements return 0, but we count as successful execution
                                if sql_stripped.upper().startswith('ALTER TABLE'):
                                    affected_rows += 1
                                elif result:
                                    affected_rows += result
            connection.commit()
            return self.format_update(affected_rows)
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            self.close_connection(connection)

    def compare_table_with(self, table_name: str, other_strategy: 'DatabaseStrategy',
                           generate_sql: bool = False) -> str:
        try:
            # Get table structures from both data sources
            my_structure = self.get_table_structure(table_name)
            other_structure = other_strategy.get_table_structure(table_name)

            # Generate ALTER TABLE SQL statements (only when needed)
            sql_file_path = None
            if generate_sql:
                # Compare field differences
                only_in_mine, only_in_other, different_cols = MySQLTools.compare_columns(my_structure, other_structure)
                alter_statements = []

                # Only generate ADD and MODIFY column SQL for target database (source2)
                # Add columns that only exist in source1 to source2
                for col in sorted(only_in_mine):
                    col_info = my_structure[col]
                    sql = MySQLTools.generate_add_column_sql(table_name, col, col_info)
                    alter_statements.append(sql)

                # Modify columns with different attributes
                for col in sorted(different_cols):
                    my_info = my_structure[col]
                    sql = MySQLTools.generate_modify_column_sql(table_name, col, my_info)
                    alter_statements.append(sql)

                # Only generate SQL file when there are actual ALTER statements
                if alter_statements:
                    sql_file_path = MySQLTools.save_alter_sql(
                        table_name, alter_statements, other_strategy.config.database
                    )

            # Use base class formatting method
            return self.format_comparison_result(table_name, my_structure, other_structure,
                                                 other_strategy, sql_file_path)

        except Exception as e:
            return f"Table structure comparison failed: {str(e)}"

    def get_table_structure(self, table_name: str) -> dict:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COLUMN_NAME,
                           COLUMN_TYPE,
                           IS_NULLABLE,
                           COLUMN_KEY,
                           COLUMN_DEFAULT,
                           EXTRA,
                           COLUMN_COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                    """,
                    (self.config.database, table_name)
                )

                columns = cursor.fetchall()

                if not columns:
                    raise ValueError(f"Table '{table_name}' does not exist in database '{self.config.database}'")

                return MySQLTools.parse_table_structure(columns)

        finally:
            self.close_connection(connection)
