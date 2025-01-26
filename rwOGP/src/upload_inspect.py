import sys, asyncpg
sys.path.append('../')

from src.param import comptable

def get_query_read(component_type, part_name = None, comptable=comptable, limit=15) -> str:
    """Get the query to read from the database.

    Returns:
    - query (str): Formatted query string.
    """
    if part_name is None:
        query = f"""SELECT {comptable[component_type]['prefix']}_name FROM {comptable[component_type]['prefix']}_inspect ORDER BY {comptable[component_type]['prefix']}_row_no DESC LIMIT {limit};"""
    else:
        query = f"""SELECT hexplot FROM {comptable[component_type]['prefix']}_inspect WHERE {comptable[component_type]['prefix']}_name = '{part_name}'"""
    return query

def get_query_write(table_name, column_names) -> str:
    """Get the query to write to the database.
    
    Returns:
    - query (str): Formatted query string."""
    pre_query = f""" INSERT INTO {table_name} ({', '.join(column_names)}) VALUES """
    data_placeholder = ', '.join(['${}'.format(i) for i in range(1, len(column_names)+1)])
    query = f"""{pre_query} {'({})'.format(data_placeholder)}"""
    return query

def get_query_write_link(component_type, column_names):
    """Get the query to write to the database.
    
    Parameters:
    - component_type (str): Type of component.
    - column_names (list): List of column names to upload the data into."""
    prefix = comptable[component_type]['prefix']
    table_name = f"{prefix}_inspect"
    mother_table = component_type.lower()
    number_name = f"{prefix}_no"
    comp_name = f"{prefix}_name"

    if not comp_name in column_names:
        print(f"Error encountered when uploading info for {component_type}.")
        raise ValueError(f"Column names must contain {comp_name}.")
    else:
        comp_name_index = f"${column_names.index(comp_name) + 1}"

    placeholders = [f"${i + 1}" for i in range(len(column_names))]
    placeholder_str = ', '.join(placeholders)

    pre_query = f"""INSERT INTO {table_name} ({number_name}, {', '.join(column_names)})
    SELECT {mother_table}.{number_name}, {placeholder_str}
    FROM {mother_table}
    WHERE {mother_table}.{prefix}_name = {comp_name_index};"""

    return pre_query

class DBClient():
    """Client to interact with the PostgreSQL database."""
    def __init__(self, config):
        """Initialize the database client.
        
        Parameters:
        - config: a loaded yaml configuration object."""
        self.host = config['host']
        self.database = config['database']
        self.user = config['user']
        self.password = config['password']

        self._connect_params = {
            'host': self.host,
            'database': self.database,
            'user': self.user,
            'password': self.password}

    async def fetch_PostgreSQL(self, query):
        conn = await asyncpg.connect(**self._connect_params)
        value = await conn.fetch(query)
        await conn.close()
        return value

    async def request_PostgreSQL(self, component_type, bp_name = None):
        """Request data from the database."""
        result = await self.fetch_PostgreSQL(get_query_read(component_type, bp_name ))
        return result

    async def upload_PostgreSQL(self, table_name, db_upload_data):
        """Upload data to the database.
        
        Parameters:
        - table_name (str): Name of the table to upload data to.
        - db_upload_data (dict): Dictionary containing the data to upload."""
        conn = await asyncpg.connect(**self._connect_params)
        
        print('Connection successful. \n')

        schema_name = 'public'
        table_exists_query = """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = $1 
            AND table_name = $2
        );
        """
        print(f"Attempting to upload to Table {table_name}...")
        table_exists = await conn.fetchval(table_exists_query, schema_name, table_name)  ### Returns True/False
        if table_exists:
            query = get_query_write(table_name, db_upload_data.keys())
            await conn.execute(query, *db_upload_data.values())
            print(f'Data successfully uploaded to the {table_name}!')
        else:
            print(f'Table {table_name} does not exist in the database.')
            print("Please create the table before uploading data or double check the table name.")
        await conn.close()

    async def link_and_update_table(self, comp_type, db_upload_data):
        """Link the component to the mother table and update the database."""
        conn = await asyncpg.connect(**self._connect_params)
        try:
            query = get_query_write_link(comp_type, db_upload_data.keys())
            print(f'Executing query: {query}')
            await conn.execute(query, *db_upload_data.values())
            print(f'Data successfully uploaded and linked to the mother table!')
        except:
            print(f"Error encountered when linking {comp_type} to the mother table.")
        
    @staticmethod
    async def GrabSensorOffsets(name):
        """Grab the sensor offsets from the database."""
        try:
            conn = await asyncpg.connect(
                database='hgcdb',
                user='postgres',
                password='hepuser',
                port=5432
            )
            query = "SELECT proto_name, x_offset_mu, y_offset_mu, ang_offset_deg FROM proto_inspect"
            rows = await conn.fetch(query)
            #print(rows)
            matching_offsets = []
            for pmodule in rows:
                if pmodule['proto_name'] == name.replace('M','P'):
                    xoffsets, yoffsets, angoffsets = pmodule['x_offset_mu'], pmodule['y_offset_mu'], pmodule['ang_offset_deg']
                    matching_offsets.append((xoffsets, yoffsets, angoffsets))

            return matching_offsets
        except asyncpg.PostgresError as e:
            print(f"Error connecting to the database: {e}")
            return None
        finally:
            await conn.close()
