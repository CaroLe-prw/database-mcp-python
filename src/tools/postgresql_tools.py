from src.tools.common_tools import CommonDatabaseTools


class PostgreSQLTools(CommonDatabaseTools):
    """PostgreSQL related utility methods"""

    @staticmethod
    def generate_add_column_sql(table_name: str, column_name: str, column_info: dict) -> str:
        """
        Generate ADD COLUMN ALTER TABLE SQL statement
        
        Args:
            table_name: Table name
            column_name: Column name
            column_info: Column information dictionary
            
        Returns:
            ALTER TABLE ADD COLUMN SQL statement
        """
        return PostgreSQLTools._generate_column_sql(
            action="ADD COLUMN",
            table_name=table_name,
            column_name=column_name,
            column_info=column_info,
        )

    @staticmethod
    def generate_modify_column_sql(table_name: str, column_name: str, column_info: dict) -> str:
        """
        Generate ALTER COLUMN SQL statements for PostgreSQL
        
        Args:
            table_name: Table name
            column_name: Column name
            column_info: Column information dictionary
            
        Returns:
            ALTER TABLE ALTER COLUMN SQL statements
        """
        sql_statements = [f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" TYPE {column_info['type']};"]

        # Type change

        # NULL/NOT NULL
        if column_info['nullable'] == 'NO':
            sql_statements.append(
                f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" SET NOT NULL;"
            )
        else:
            sql_statements.append(
                f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" DROP NOT NULL;"
            )

        # DEFAULT
        default_val = column_info.get('default')
        if default_val and default_val != 'NULL':
            if default_val in ['CURRENT_TIMESTAMP', 'now()', 'CURRENT_DATE']:
                sql_statements.append(
                    f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" SET DEFAULT {default_val};"
                )
            else:
                sql_statements.append(
                    f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" SET DEFAULT '{default_val}';"
                )
        else:
            sql_statements.append(
                f"ALTER TABLE \"{table_name}\" ALTER COLUMN \"{column_name}\" DROP DEFAULT;"
            )

        # COMMENT (PostgreSQL uses separate COMMENT ON statement)
        if column_info.get('comment'):
            sql_statements.append(
                f"COMMENT ON COLUMN \"{table_name}\".\"{column_name}\" IS '{column_info['comment']}';"
            )

        return '\n'.join(sql_statements)

    @staticmethod
    def _generate_column_sql(
            action: str,
            table_name: str,
            column_name: str,
            column_info: dict,
    ) -> str:
        """
        Unified generation of column definition SQL fragment (for ADD).
        
        Args:
            action: "ADD COLUMN"
            table_name: Table name
            column_name: Column name
            column_info: Column information dictionary
        """
        sql = (
            f"ALTER TABLE \"{table_name}\" {action} "
            f"\"{column_name}\" {column_info['type']}"
        )

        # NULL/NOT NULL
        if column_info['nullable'] == 'NO':
            sql += " NOT NULL"

        # DEFAULT
        default_val = column_info.get('default')
        if default_val and default_val != 'NULL':
            if default_val in ['CURRENT_TIMESTAMP', 'now()', 'CURRENT_DATE']:
                sql += f" DEFAULT {default_val}"
            else:
                sql += f" DEFAULT '{default_val}'"

        sql += ";"

        # COMMENT (as separate statement)
        if column_info.get('comment'):
            sql += f"\nCOMMENT ON COLUMN \"{table_name}\".\"{column_name}\" IS '{column_info['comment']}';"

        return sql

    @staticmethod
    def _normalize_structure(structure: dict) -> dict:
        """
        Normalize a table structure for PostgreSQL comparison
        
        Args:
            structure: Original table structure
            
        Returns:
            Normalized table structure
        """
        normalized = {}
        for col, info in structure.items():
            normalized[col] = {
                'type': PostgreSQLTools._normalize_type(info['type']),
                'nullable': info['nullable'],
                'key': info.get('key', ''),
                'default': PostgreSQLTools._normalize_default(info.get('default', 'NULL')),
                'extra': info.get('extra', ''),
                'comment': info.get('comment', '')
            }
        return normalized

    @staticmethod
    def compare_columns_with_type_normalization(my_structure: dict, other_structure: dict) -> tuple:
        """
        Compare field differences between two table structures with PostgreSQL type normalization
        
        Args:
            my_structure: Structure of the first table
            other_structure: Structure of the second table
            
        Returns:
            (Fields only in first table set, Fields only in second table set, List of fields with different attributes)
        """
        # Normalize both structures
        my_normalized = PostgreSQLTools._normalize_structure(my_structure)
        other_normalized = PostgreSQLTools._normalize_structure(other_structure)

        # Use parent class compare_columns with normalized structures
        return CommonDatabaseTools.compare_columns(my_normalized, other_normalized)

    @staticmethod
    def _normalize_type(type_str: str) -> str:
        """Normalize PostgreSQL type strings for comparison"""
        # Remove whitespace and convert to lowercase
        normalized = type_str.lower().strip()

        # Common type aliases
        type_aliases = {
            'int': 'integer',
            'int4': 'integer',
            'int8': 'bigint',
            'int2': 'smallint',
            'varchar': 'character varying',
            'char': 'character',
            'bool': 'boolean',
            'timestamp': 'timestamp without time zone',
            'timestamptz': 'timestamp with time zone',
        }

        for alias, canonical in type_aliases.items():
            if normalized.startswith(alias):
                normalized = normalized.replace(alias, canonical, 1)

        return normalized

    @staticmethod
    def _normalize_default(default_str: str) -> str:
        """Normalize default value strings for comparison"""
        if not default_str or default_str == 'NULL':
            return 'NULL'

        # Remove quotes and normalize common defaults
        normalized = default_str.strip("'\"")

        # PostgreSQL specific defaults
        default_aliases = {
            'now()': 'CURRENT_TIMESTAMP',
            'current_timestamp': 'CURRENT_TIMESTAMP',
            'nextval': 'SEQUENCE',  # Simplify sequence defaults
        }

        for alias, canonical in default_aliases.items():
            if alias in normalized.lower():
                return canonical

        return normalized

    @staticmethod
    def get_column_index_names(cursor, table_name: str, column_name: str) -> list:
        """
        Get the list of index names for a specific table column
        
        Args:
            cursor: Database cursor
            table_name: Table name
            column_name: Column name
            
        Returns:
            List of index names
        """
        cursor.execute(
            """
            SELECT DISTINCT i.relname AS index_name
            FROM pg_index ix
                     JOIN pg_class i ON i.oid = ix.indexrelid
                     JOIN pg_class t ON t.oid = ix.indrelid
                     JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY (ix.indkey)
            WHERE t.relname = %s
              AND a.attname = %s
            """,
            (table_name, column_name)
        )
        index_results = cursor.fetchall()
        return [row[0] for row in index_results]
