from src.tools.common_tools import CommonDatabaseTools


class OracleTools(CommonDatabaseTools):

    @staticmethod
    def compare_columns(my_structure: dict, other_structure: dict) -> tuple:
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
        col_type = col_info['type']
        nullable = 'NULL' if col_info['nullable'] == 'YES' else 'NOT NULL'
        default_val = col_info.get('default', '')

        if default_val and default_val != 'NULL':
            default_clause = f" DEFAULT {default_val}"
        else:
            default_clause = ""

        return f"ALTER TABLE {table_name} ADD {col_name} {col_type} {default_clause} {nullable}"

    @staticmethod
    def generate_modify_column_sql(table_name: str, col_name: str, col_info: dict) -> str:
        col_type = col_info['type']
        nullable = 'NULL' if col_info['nullable'] == 'YES' else 'NOT NULL'
        default_val = col_info.get('default', '')

        if default_val and default_val != 'NULL':
            default_clause = f" DEFAULT {default_val}"
        else:
            default_clause = ""

        return f"ALTER TABLE {table_name} MODIFY {col_name} {col_type} {default_clause} {nullable}"

    @staticmethod
    def format_value_for_sql(value) -> str:
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bytes):
            hex_str = value.hex()
            return f"HEXTORAW('{hex_str}')"
        else:
            return f"'{str(value)}'"

    @staticmethod
    def get_data_type_mapping(oracle_type: str) -> str:
        type_lower = oracle_type.lower()

        if 'number' in type_lower:
            if '(' in type_lower:
                precision_scale = type_lower[type_lower.index('('):type_lower.index(')') + 1]
                if ',' in precision_scale and ',0)' not in precision_scale:
                    return f"NUMBER{precision_scale}"
                else:
                    return f"NUMBER{precision_scale}"
            return 'NUMBER'
        elif 'varchar2' in type_lower:
            return oracle_type.upper()
        elif 'char' in type_lower:
            return oracle_type.upper()
        elif 'date' in type_lower:
            return 'DATE'
        elif 'timestamp' in type_lower:
            return oracle_type.upper()
        elif 'clob' in type_lower:
            return 'CLOB'
        elif 'blob' in type_lower:
            return 'BLOB'
        elif 'raw' in type_lower:
            return oracle_type.upper()
        elif 'long' in type_lower:
            return 'LONG'
        elif 'float' in type_lower:
            return 'FLOAT'
        else:
            return oracle_type.upper()
