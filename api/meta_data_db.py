
class queries():

    @classmethod
    def create_meta_breeder_table(table_name=None):
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        creation_tsz TIMESTAMPZ,
        definition jsonb NOT NULL
        );
        """

        return query

    @classmethod
    def insert_breeder_meta(table_name=None, creation_ts=None, meta_state=None):
        query = f"""
        INSERT INTO {table_name} (creation_tsz, definition)
        VALUES({creation_ts}, {meta_state});
        """

        return query
