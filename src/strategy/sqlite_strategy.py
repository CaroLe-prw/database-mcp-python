import os
import sqlite3
from typing import Any

from dbutils.pooled_db import PooledDB

from ..model.database_config import DatabaseConfig
from ..strategy.database_strategy import DatabaseStrategy
from ..tools.sqlite_tools import SQLiteTools


class SQLiteStrategy(DatabaseStrategy):

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.pool = None

    def create_pool(self) -> PooledDB:
        if not self.pool:
            self.pool = PooledDB(
                creator=sqlite3,
                database=self.config.database,
                mincached=self.config.minCached or 5,
                maxcached=self.config.maxCached or 10,
                maxconnections=self.config.maxConnections or 20,
                check_same_thread=False,
            )
        return self.pool

    def get_connection(self) -> Any:
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
                cursor.execute("""
                               SELECT name as table_name,
                                      ''   as comments
                               FROM sqlite_master
                               WHERE type = 'table'
                                 AND name NOT LIKE 'sqlite_%'
                               ORDER BY name
                               """)
                tables = cursor.fetchall()

                headers = ["TABLE_NAME", "COMMENTS"]
                return self.format_table(headers, list(tables))
        finally:
            self.close_connection(connection)

    def describe_Table(self, table_name: str) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # Query basic field information
                cursor.execute("PRAGMA table_info(?)", [table_name])
                pragma_results = cursor.fetchall()

                if not pragma_results:
                    return f"Table '{table_name}' not found"

                table_infos = []
                for col in pragma_results:
                    # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
                    column_name = col[1]
                    data_type = col[2] or 'TEXT'
                    column_type = col[2] or 'TEXT'
                    is_nullable = 'NO' if col[3] else 'YES'
                    column_default = col[4]
                    is_pk = col[5]

                    # Build basic info tuple
                    table_infos.append((
                        column_name,  # COLUMN_NAME
                        '',  # COLUMN_COMMENT (SQLite doesn't have built-in column comments)
                        data_type,  # DATA_TYPE
                        column_type,  # COLUMN_TYPE
                        column_default,  # COLUMN_DEFAULT
                        'PRI' if is_pk else '',  # COLUMN_KEY (will be updated with index info)
                        is_nullable,  # IS_NULLABLE
                        ''  # EXTRA
                    ))

                result_infos = []

                # Query index information for each field
                for table_info in table_infos:
                    cursor.execute("""
                                   SELECT DISTINCT il.name
                                   FROM sqlite_master m
                                            LEFT OUTER JOIN pragma_index_list(m.name) il ON m.name != il.name
                                            LEFT OUTER JOIN pragma_index_info(il.name) ii ON il.name = ii.name
                                   WHERE m.type = 'table'
                                     AND m.name = ?
                                     AND ii.name = ?
                                   """, [table_name, table_info[0]])  # table_info[0] is COLUMN_NAME
                    index_results = cursor.fetchall()

                    # Extract index name list
                    index_names = [row[0] for row in index_results if row[0]]

                    # Build column key info
                    info_list = list(table_info)

                    if info_list[5] == 'PRI':  # Already has primary key
                        if index_names:
                            info_list[5] += f" ({', '.join(index_names)})"
                    elif index_names:
                        info_list[5] = f"IDX ({', '.join(index_names)})"

                    result_infos.append(tuple(info_list))

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

                if sql_stripped.upper().startswith("SELECT"):
                    # SELECT query: return result set
                    if params:
                        cursor.execute(sql_stripped, params)
                    else:
                        cursor.execute(sql_stripped)

                    rows = cursor.fetchall()
                    if not rows:
                        return "No data found"

                    if cursor.description:
                        headers = [desc[0] for desc in cursor.description]
                        return self.format_table(headers, list(rows))
                    else:
                        return "Query executed successfully"
                else:
                    # DML/DDL statements: execute in transaction
                    if params:
                        cursor.execute(sql_stripped, params)
                    else:
                        cursor.execute(sql_stripped)

                    connection.commit()

                    if sql_stripped.upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                        affected_rows = cursor.rowcount
                        return self.format_update(affected_rows)
                    elif sql_stripped.upper().startswith('ALTER'):
                        return self.format_update(1)
                    else:
                        return "Statement executed successfully"
        except Exception as e:
            if connection:
                connection.rollback()
            raise Exception(f"Failed to execute SQL: {str(e)}")
        finally:
            self.close_connection(connection)

    def export_data(self, table_name: str, file_path: str = None) -> str:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # Validate table name
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    [table_name]
                )
                if not cursor.fetchone():
                    raise ValueError(f"Table '{table_name}' does not exist")

                # Get column information
                cursor.execute("PRAGMA table_info(?)", [table_name])
                columns_info = cursor.fetchall()
                column_names = [col[1] for col in columns_info]

                # Prepare export directory and file
                if not file_path:
                    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    file_path = os.path.join(script_dir, "export_data")

                os.makedirs(file_path, exist_ok=True)

                # Query data count
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]

                if count == 0:
                    return f"Table '{table_name}' has no data"

                # Split count into batches of 1000 records per file
                batch_size = 1000
                file_count = (count + batch_size - 1) // batch_size

                for i in range(file_count):
                    offset = i * batch_size
                    cursor.execute(f"""
                        SELECT * FROM "{table_name}"
                        LIMIT {batch_size} OFFSET {offset}
                    """)
                    rows = cursor.fetchall()

                    if not rows:
                        continue

                    # Assemble into insert sql
                    insert_values = []
                    for row in rows:
                        values = []
                        for value in row:
                            values.append(SQLiteTools.format_value_for_sql(value))
                        insert_values.append(f"({', '.join(values)})")

                    columns_str = ', '.join(f'"{col}"' for col in column_names)
                    insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES '
                    insert_sql += ", ".join(insert_values) + ";"

                    # Write to file
                    file_name = os.path.join(file_path, f"{table_name}_{i}.sql")
                    with open(file_name, "w", encoding='utf-8') as f:
                        f.write(insert_sql)

                return f"Exported {count} rows to {file_path}."
        finally:
            self.close_connection(connection)

    def execute_sql_file(self, file_path: str) -> str:
        connection = self.get_connection()
        connection.execute("BEGIN TRANSACTION")
        affected_rows = 0
        try:
            with connection.cursor() as cursor:
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")

                if os.path.isdir(file_path):
                    sql_content = self.read_all_files(file_path)
                    for sql in sql_content:
                        cursor.execute(sql)
                        if sql.strip().upper().startswith('ALTER'):
                            affected_rows += 1
                        else:
                            affected_rows += cursor.rowcount
                else:
                    if not file_path.endswith('.sql'):
                        raise ValueError(f"Invalid file type: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Split SQL statements (by semicolon)
                        statements = content.split(';')
                        for statement in statements:
                            sql_stripped = statement.strip()
                            # Skip empty statements and comments
                            if sql_stripped and not sql_stripped.startswith('--'):
                                cursor.execute(sql_stripped)
                                if sql_stripped.upper().startswith('ALTER'):
                                    affected_rows += 1
                                else:
                                    affected_rows += cursor.rowcount
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
                # Use base class method to generate ALTER statements
                alter_statements = self.generate_alter_statements(
                    table_name, my_structure, other_structure, SQLiteTools,
                    compare_method_name='compare_columns'
                )
                # Only generate SQL file when there are actual ALTER statements
                if alter_statements:
                    sql_file_path = SQLiteTools.save_alter_sql(
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
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table_name])
                if not cursor.fetchone():
                    raise ValueError(f"Table '{table_name}' does not exist in database '{self.config.database}'")

                # Get column information using PRAGMA
                cursor.execute("PRAGMA table_info(?)", [table_name])
                pragma_results = cursor.fetchall()

                columns = []
                for col in pragma_results:
                    # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
                    column_name = col[1]
                    data_type = col[2] or 'TEXT'
                    column_type = col[2] or 'TEXT'
                    is_nullable = 'NO' if col[3] else 'YES'
                    column_default = col[4]
                    is_pk = col[5]

                    columns.append((
                        column_name,  # column_name
                        '',  # column_comment
                        data_type,  # data_type
                        column_type,  # column_type
                        column_default,  # column_default
                        'PRI' if is_pk else '',  # column_key
                        is_nullable,  # is_nullable
                        ''  # extra
                    ))

                return SQLiteTools.parse_table_structure(columns)

        finally:
            self.close_connection(connection)
