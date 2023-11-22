
import json

class queries():

    @staticmethod
    def create_meta_breeder_table(table_name=None):
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id uuid PRIMARY KEY,
        creation_tsz TIMESTAMPTZ,
        definition jsonb NOT NULL
        );
        """

        return query

    @staticmethod
    def insert_breeder_meta(table_name=None, breeder_id=None, creation_ts=None, meta_state=None):

        json_string = json.dumps(meta_state)

        query = f"""
        INSERT INTO {table_name} (creation_tsz, definition)
        VALUES('{breeder_id}', '{creation_ts}', '{json_string}');
        """

        return query

    def remove_breeder_meta(table_name=None, breeder_id=None):
        query = f"""
        DELETE FROM {table_name} WHERE id = '{breeder_id}';
        """

        return query

    def fetch_meta_data(table_name=None, breeder_id=None):
        query = f"""
        SELECT id, creation_tsz, definition FROM {table_name} WHERE id = '{breeder_id}';
        """

        return query

    def fetch_breeders_list(table_name=None):
        query = f"""
        SELECT id, definition->>'name', creation_tsz FROM {table_name};
        """

        return query
