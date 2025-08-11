from src.tools.common_tools import CommonDatabaseTools


class MySQLTools(CommonDatabaseTools):
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
