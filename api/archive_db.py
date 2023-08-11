
import psycopg2

class archive_db():

    def __execute(db_info=None, statement=""):
        """ Function wrapping the curoser execute with
            a dedicated connection for the execution."""

        db_connection = None
        try:
            with psycopg2.connect(**db_info) as db_connection:
                # Create table
                with db_connection.cursor() as db_cursor:
                    db_cursor.execute(statement)

        except OperationalError as Error:
            print(f"Error connecting to the database : {Error}")

        finally:
            if db_connection:
                db_connection.close()
                print("Closed connection.")
