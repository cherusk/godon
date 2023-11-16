
import psycopg2
import logging

class archive_db():

    @staticmethod
    def execute(db_info=None, query=""):
        """ Function wrapping the curoser execute with
            a dedicated connection for the execution."""

        db_connection = None
        try:
            with psycopg2.connect(**db_info) as db_connection:
                # Create table
                with db_connection.cursor() as db_cursor:
                    db_cursor.execute(query)

        except psycopg2.OperationalError as Error:
            logging.error(f"Error connecting to the database : {Error}")

        finally:
            if db_connection:
                db_connection.close()
                print("Closed connection.")

class queries():

    @staticmethod
    def create_breeder_table(table_name=None):
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        setting_id bpchar NOT NULL,
        setting_full jsonb NOT NULL,
        setting_result FLOAT NOT NULL,
        PRIMARY KEY (setting_id HASH)
        );
        """

        return query

    @staticmethod
    def delete_breeder_table(table_name=None):
        query = f"""
        DROP TABLE IF EXISTS {table_name};
        """

        return query

    @staticmethod
    def create_trigger(trigger_name=None, table_name=None, procedure_name=None):
        query = f"""
        CREATE TRIGGER {trigger_name}
        AFTER INSERT ON {table_name}
        FOR EACH ROW
        EXECUTE PROCEDURE {procedure_name} ();
        """

        return query


    @staticmethod
    def delete_trigger(trigger_name=None, table_name=None):
        query = f"""
        DROP TRIGGER IF EXISTS {trigger_name}
        ON {table_name}
        """

        return query

    @staticmethod
    def create_procedure(procedure_name=None, probability=1.0, source_table_name=None, target_table_name=None):
        query = f"""
        CREATE OR REPLACE FUNCTION {procedure_name}() RETURNS TRIGGER AS $$
        DECLARE
          random_value real;
        BEGIN

          random_value = random();

          IF random_value < {probability} THEN
            INSERT INTO {target_table_name} (target_table_setting_id, target_table_setting_full, target_table_setting_result)
            SELECT source_table_setting_id, source_table_setting_full, source_table_setting_result FROM {source_table_name}
            ON CONFLICT
            DO UPDATE SET target_table_setting_result = source_table_setting_result WHERE  target_table_setting_result < source_table_setting_result;
          END IF;

        END;
        $$ LANGUAGE plpgsql;
        """

        return query

    @staticmethod
    def delete_procedure(procedure_name=None):
        query = f"""
        DROP FUNCTION IF EXISTS {procedure_name}();
        """

        return query

