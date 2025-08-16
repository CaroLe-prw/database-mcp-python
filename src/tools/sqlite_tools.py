from src.tools.common_tools import CommonDatabaseTools


class SQLiteTools(CommonDatabaseTools):

    @staticmethod
    def compare_columns(my_structure: dict, other_structure: dict) -> tuple:
        """
        Compare column structures between two table schemas.
        
        Args:
            my_structure: Dictionary containing current table structure
            other_structure: Dictionary containing target table structure
            
        Returns:
            Tuple containing (columns_only_in_mine, columns_only_in_other, different_columns)
        """
        my_cols = set(my_structure.keys())
        other_cols = set(other_structure.keys())

        only_in_mine = my_cols - other_cols
        only_in_other = other_cols - my_cols

        common_cols = my_cols & other_cols
        different_cols = []

        for col in common_cols:
            my_info = my_structure[col]
            other_info = other_structure[col]

            if (my_info['type'] != other_info['type'] or
                    my_info['nullable'] != other_info['nullable'] or
                    my_info.get('default', 'NULL') != other_info.get('default', 'NULL')):
                different_cols.append(col)

        return only_in_mine, only_in_other, different_cols

    @staticmethod
    def generate_add_column_sql(table_name: str, col_name: str, col_info: dict) -> str:
        """
        Generate SQL statement to add a new column to SQLite table.
        
        Args:
            table_name: Name of the table
            col_name: Name of the column to add
            col_info: Dictionary containing column information (type, nullable, default)
            
        Returns:
            ALTER TABLE SQL statement string
        """
        col_type = col_info['type']
        nullable = '' if col_info['nullable'] == 'YES' else 'NOT NULL'
        default_val = col_info.get('default', '')

        if default_val and default_val != 'NULL':
            default_clause = f" DEFAULT {default_val}"
        else:
            default_clause = ""

        return f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_clause} {nullable}".strip()

    @staticmethod
    def generate_modify_column_sql(table_name: str, col_name: str, col_info: dict) -> str:
        """
        Generate SQL comment for column modification (SQLite doesn't support ALTER COLUMN).
        
        Args:
            table_name: Name of the table
            col_name: Name of the column to modify
            col_info: Dictionary containing column information (type, nullable, default)
            
        Returns:
            Comment string explaining manual table recreation requirement
        """
        # SQLite doesn't support ALTER COLUMN directly
        # This would require table recreation in real scenarios
        col_type = col_info['type']
        nullable = '' if col_info['nullable'] == 'YES' else 'NOT NULL'
        default_val = col_info.get('default', '')

        if default_val and default_val != 'NULL':
            default_clause = f" DEFAULT {default_val}"
        else:
            default_clause = ""

        return f"-- SQLite does not support ALTER COLUMN. Manual table recreation required for: {col_name} {col_type}{default_clause} {nullable}".strip()

    @staticmethod
    def format_value_for_sql(value) -> str:
        """
        Format a Python value for use in SQLite SQL statements.
        
        Args:
            value: Python value to format (None, str, int, float, bytes, etc.)
            
        Returns:
            Formatted string suitable for SQL insertion
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bytes):
            # SQLite BLOB handling
            hex_str = value.hex()
            return f"X'{hex_str}'"
        else:
            return f"'{str(value)}'"

    @staticmethod
    def get_data_type_mapping(sqlite_type: str) -> str:
        """
        Map SQLite data types to standardized type names.
        
        Args:
            sqlite_type: Raw SQLite data type string
            
        Returns:
            Standardized data type name (INTEGER, TEXT, BLOB, REAL, NUMERIC)
        """
        type_lower = sqlite_type.lower()

        if 'int' in type_lower:
            return 'INTEGER'
        elif 'char' in type_lower or 'clob' in type_lower or 'text' in type_lower:
            return 'TEXT'
        elif 'blob' in type_lower:
            return 'BLOB'
        elif 'real' in type_lower or 'floa' in type_lower or 'doub' in type_lower:
            return 'REAL'
        elif 'numeric' in type_lower or 'decimal' in type_lower:
            return 'NUMERIC'
        else:
            return sqlite_type.upper()

    @staticmethod
    def parse_table_structure(columns: list) -> dict:
        """
        Parse SQLite table structure information into standardized format.
        
        Args:
            columns: List of tuples from SQLite system tables query containing:
                    (column_name, column_comment, data_type, column_type, 
                     column_default, column_key, is_nullable, extra)
            
        Returns:
            Dictionary with column names as keys and column attribute dictionaries as values.
            Each column dict contains: type, nullable, key, default, extra, comment
        """
        structure = {}
        for col in columns:
            # SQLite query returns: column_name, column_comment, data_type, column_type, column_default, column_key, is_nullable, extra
            structure[col[0]] = {
                'type': SQLiteTools.get_data_type_mapping(col[3] or col[2]),  # Use column_type or fallback to data_type
                'nullable': col[6],
                'key': col[5] or '',
                'default': str(col[4]).strip() if col[4] is not None else 'NULL',
                'extra': col[7] or '',
                'comment': col[1] or ''
            }
        return structure