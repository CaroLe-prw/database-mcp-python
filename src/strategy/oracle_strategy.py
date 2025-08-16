import os
from typing import Any

import oracledb
from dbutils.pooled_db import PooledDB

from ..model.database_config import DatabaseConfig
from ..strategy.database_strategy import DatabaseStrategy
from ..tools.oracle_tools import OracleTools


class OracleStrategy(DatabaseStrategy):

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.pool = None

    def create_pool(self) -> PooledDB:
        if not self.pool:
            self.pool = PooledDB(
                creator=oracledb,
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                dsn=self._make_dsn(),
                mincached=self.config.minCached or 5,
                maxcached=self.config.maxCached or 10,
                maxconnections=self.config.maxConnections or 20,
            )
        return self.pool

    def _make_dsn(self):
        return oracledb.makedsn(self.config.host, self.config.port, self.config.database)

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
                               SELECT table_name,
                                      comments
                               FROM user_tab_comments
                               WHERE table_type = 'TABLE'
                               ORDER BY table_name
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
                cursor.execute("""
                               SELECT col.column_name,
                                      comm.comments    AS column_comment,
                                      col.data_type    AS data_type,
                                      col.data_type ||
                                      CASE
                                          WHEN col.data_type IN ('VARCHAR2', 'CHAR', 'RAW')
                                              THEN '(' || col.data_length || ')'
                                          WHEN col.data_type = 'NUMBER' AND col.data_precision IS NOT NULL THEN
                                              '(' || col.data_precision ||
                                              CASE
                                                  WHEN col.data_scale IS NOT NULL AND col.data_scale > 0
                                                      THEN ',' || col.data_scale
                                                  ELSE '' END || ')'
                                          ELSE ''
                                          END          AS column_type,
                                      col.data_default AS column_default,
                                      ''               AS column_key,
                                      col.nullable     AS is_nullable,
                                      ''               AS extra
                               FROM user_tab_columns col
                                        LEFT JOIN user_col_comments comm
                                                  ON comm.table_name = col.table_name AND comm.column_name = col.column_name
                               WHERE UPPER(col.table_name) = UPPER(:1)
                               ORDER BY col.column_id
                               """, [table_name])
                table_infos = cursor.fetchall()

                if not table_infos:
                    return f"Table '{table_name}' not found"

                result_infos = []

                # Query index information for each field
                for table_info in table_infos:
                    cursor.execute("""
                                   SELECT idx.index_name
                                   FROM user_ind_columns col
                                            JOIN user_indexes idx ON col.index_name = idx.index_name
                                   WHERE UPPER(col.table_name) = UPPER(:1)
                                     AND UPPER(col.column_name) = UPPER(:2)
                                     AND idx.index_type != 'LOB'
                                   """, [table_name, table_info[0]])  # table_info[0] is COLUMN_NAME
                    index_results = cursor.fetchall()

                    # Extract index name list
                    index_names = [row[0] for row in index_results]

                    # Get constraint information for this column
                    cursor.execute("""
                                   SELECT CASE
                                              WHEN con.constraint_type = 'P' THEN 'PRI'
                                              WHEN con.constraint_type = 'U' THEN 'UNI'
                                              WHEN con.constraint_type = 'R' THEN 'MUL'
                                              ELSE ''
                                              END AS key_type
                                   FROM user_cons_columns col
                                            JOIN user_constraints con ON col.constraint_name = con.constraint_name
                                   WHERE UPPER(col.table_name) = UPPER(:1)
                                     AND UPPER(col.column_name) = UPPER(:2)
                                     AND con.constraint_type IN ('P', 'U', 'R')
                                   """, [table_name, table_info[0]])
                    constraint_results = cursor.fetchall()

                    # Build column key info
                    info_list = list(table_info)
                    key_types = [row[0] for row in constraint_results if row[0]]

                    if key_types:
                        key_info = ','.join(key_types)
                        if index_names:
                            key_info += f" ({', '.join(index_names)})"
                        info_list[5] = key_info  # COLUMN_KEY field
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
                    "SELECT COUNT(*) FROM user_tables WHERE UPPER(table_name) = UPPER(:1)",
                    [table_name]
                )
                if cursor.fetchone()[0] == 0:
                    raise ValueError(f"Table '{table_name}' does not exist")

                # Get column information
                cursor.execute("""
                               SELECT column_name, data_type
                               FROM user_tab_columns
                               WHERE UPPER(table_name) = UPPER(:1)
                               ORDER BY column_id
                               """, [table_name])
                columns_info = cursor.fetchall()
                column_names = [col[0] for col in columns_info]
                column_types = {col[0]: col[1] for col in columns_info}

                # Prepare export directory and file
                if not file_path:
                    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    file_path = os.path.join(script_dir, "export_data")

                os.makedirs(file_path, exist_ok=True)

                # Query data count
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]

                if count == 0:
                    return f"Table '{table_name}' has no data"

                # Split count into batches of 1000 records per file
                batch_size = 1000
                file_count = (count + batch_size - 1) // batch_size

                for i in range(file_count):
                    offset = i * batch_size
                    cursor.execute(f"""
                        SELECT * FROM {table_name}
                        OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY
                    """)
                    rows = cursor.fetchall()

                    if not rows:
                        continue

                    # Assemble into insert sql
                    insert_values = []
                    for row in rows:
                        values = []
                        for j, value in enumerate(row):
                            values.append(OracleTools.format_value_for_sql(value))
                        insert_values.append(f"({', '.join(values)})")

                    columns_str = ', '.join(column_names)
                    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES "
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
        connection.begin()
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
                    table_name, my_structure, other_structure, OracleTools)
                # Only generate SQL file when there are actual ALTER statements
                if alter_statements:
                    sql_file_path = OracleTools.save_alter_sql(
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
                cursor.execute("""
                               SELECT col.column_name,
                                      col.data_type ||
                                      CASE
                                          WHEN col.data_type IN ('VARCHAR2', 'CHAR', 'RAW')
                                              THEN '(' || col.data_length || ')'
                                          WHEN col.data_type = 'NUMBER' AND col.data_precision IS NOT NULL THEN
                                              '(' || col.data_precision ||
                                              CASE
                                                  WHEN col.data_scale IS NOT NULL AND col.data_scale > 0
                                                      THEN ',' || col.data_scale
                                                  ELSE '' END || ')'
                                          ELSE ''
                                          END          AS column_type,
                                      col.nullable     AS is_nullable,
                                      CASE
                                          WHEN pk.constraint_type = 'P' THEN 'PRI'
                                          WHEN uk.constraint_type = 'U' THEN 'UNI'
                                          ELSE ''
                                          END          AS column_key,
                                      col.data_default AS column_default,
                                      ''               AS extra,
                                      comm.comments    AS column_comment
                               FROM user_tab_columns col
                                        LEFT JOIN user_cons_columns cc
                                                  ON cc.table_name = col.table_name AND cc.column_name = col.column_name
                                        LEFT JOIN user_constraints pk
                                                  ON pk.constraint_name = cc.constraint_name AND pk.constraint_type = 'P'
                                        LEFT JOIN user_constraints uk
                                                  ON uk.constraint_name = cc.constraint_name AND uk.constraint_type = 'U'
                                        LEFT JOIN user_col_comments comm
                                                  ON comm.table_name = col.table_name AND comm.column_name = col.column_name
                               WHERE UPPER(col.table_name) = UPPER(:1)
                               ORDER BY col.column_id
                               """, [table_name])
                columns = cursor.fetchall()

                if not columns:
                    raise ValueError(f"Table '{table_name}' does not exist in schema '{self.config.database}'")

                return OracleTools.parse_table_structure(columns)

        finally:
            self.close_connection(connection)
