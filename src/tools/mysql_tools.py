import datetime
import os
from typing import Dict, List


class MySQLTools:
    """MySQL related utility methods"""

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
        return MySQLTools._generate_column_sql(
            action="ADD COLUMN",
            table_name=table_name,
            column_name=column_name,
            column_info=column_info,
        )

    @staticmethod
    def generate_modify_column_sql(table_name: str, column_name: str, column_info: dict) -> str:
        """
        Generate MODIFY COLUMN ALTER TABLE SQL statement

        Args:
            table_name: Table name
            column_name: Column name
            column_info: Column information dictionary

        Returns:
            ALTER TABLE MODIFY COLUMN SQL statement
        """
        return MySQLTools._generate_column_sql(
            action="MODIFY COLUMN",
            table_name=table_name,
            column_name=column_name,
            column_info=column_info,
        )

    @staticmethod
    def _generate_column_sql(
            action: str,
            table_name: str,
            column_name: str,
            column_info: dict,
    ) -> str:
        """
        Unified generation of column definition SQL fragment (for ADD/MODIFY).

        Args:
            action: "ADD COLUMN" or "MODIFY COLUMN"
            table_name: Table name
            column_name: Column name
            column_info: Column information dictionary
        """
        sql = (
            f"ALTER TABLE `{table_name}` {action} "
            f"`{column_name}` {column_info['type']}"
        )

        # NULL/NOT NULL
        if column_info['nullable'] == 'NO':
            sql += " NOT NULL"
        else:
            sql += " NULL"

        # DEFAULT
        default_val = column_info.get('default')
        if default_val != 'NULL' and default_val:
            if default_val == 'CURRENT_TIMESTAMP':
                sql += f" DEFAULT {default_val}"
            else:
                sql += f" DEFAULT '{default_val}'"

        # EXTRA
        if column_info.get('extra'):
            sql += f" {column_info['extra']}"

        # COMMENT
        if column_info.get('comment'):
            sql += f" COMMENT '{column_info['comment']}'"

        return sql + ";"

    @staticmethod
    def save_alter_sql(table_name: str, sql_statements: List[str], target_db: str) -> str:
        """
        Save ALTER TABLE SQL statements to file
        
        Args:
            table_name: Table name
            sql_statements: SQL statements list
            target_db: Target database name
            
        Returns:
            Saved file path
        """
        try:
            # Use relative path from script directory, ensure creation under project root
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_dir = os.path.join(script_dir, "export_data")

            # Ensure directory exists
            os.makedirs(export_dir, exist_ok=True)

            # Generate filename (with timestamp)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"alter_{table_name}_{target_db}_{timestamp}.sql"
            file_path = os.path.join(export_dir, file_name)

            # Write SQL file
            with open(file_path, 'w', encoding='utf-8') as f:
                for sql in sql_statements:
                    f.write(sql + "\n")

            return file_path

        except Exception as e:
            raise Exception(f"Failed to save SQL file: {str(e)}")

    @staticmethod
    def parse_table_structure(columns: List[tuple]) -> Dict[str, dict]:
        """
        Parse table structure information
        
        Args:
            columns: Results from INFORMATION_SCHEMA.COLUMNS query
            
        Returns:
            Dictionary with field names as keys and field attribute dictionaries as values
        """
        structure = {}
        for col in columns:
            structure[col[0]] = {
                'type': col[1],
                'nullable': col[2],
                'key': col[3] or '',
                'default': str(col[4]) if col[4] is not None else 'NULL',
                'extra': col[5] or '',
                'comment': col[6] or ''
            }
        return structure

    @staticmethod
    def compare_columns(my_structure: dict, other_structure: dict) -> tuple:
        """
        Compare field differences between two table structures
        
        Args:
            my_structure: Structure of the first table
            other_structure: Structure of the second table
            
        Returns:
            (Fields only in first table set, Fields only in second table set, List of fields with different attributes)
        """
        my_cols = set(my_structure.keys())
        other_cols = set(other_structure.keys())

        # Fields only in first table
        only_in_mine = my_cols - other_cols

        # Fields only in second table
        only_in_other = other_cols - my_cols

        # Common fields with different attributes
        common_cols = my_cols & other_cols
        different_cols = []

        for col in common_cols:
            my_info = my_structure[col]
            other_info = other_structure[col]

            if (my_info['type'] != other_info['type'] or
                    my_info['nullable'] != other_info['nullable'] or
                    my_info.get('key', '') != other_info.get('key', '') or
                    my_info.get('default', 'NULL') != other_info.get('default', 'NULL') or
                    my_info.get('extra', '') != other_info.get('extra', '')):
                different_cols.append(col)

        return only_in_mine, only_in_other, different_cols
