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

def get_query_write_link(comp_params, db_dict) -> tuple[str, str, str, list]:
    """Get the query to write to the database and link the component to the mother table.
    
    Parameters:
    - comp_params (dict): Dictionary containing the parameters of the component.
    - db_dict (dict): Dictionary containing the data to upload.
    
    Returns: 
    - pre_query (str): Pre-query to check if component exists in mother table.
    - query (str): Formatted query string.
    - column_values (list): List of values to upload."""

    column_names = list(db_dict.keys())
    column_values = [db_dict[key] for key in column_names]

    prefix = comp_params['prefix']
    mother_table = comp_params['mother_table']
    table_name = f"{prefix}_inspect"
    number_name = f"{prefix}_no"
    comp_name = f"{prefix}_name"

    comp_name_val = column_values[column_names.index(comp_name)]
    
    if not comp_name in column_names:
        print("!" * 90)
        print("Component ID not provided in the data.")
        raise ValueError(f"Column names must contain {comp_name}.")
    else:
        comp_name_index = f"${column_names.index(comp_name) + 1}"

    # Pre-query to check if component exists in mother table
    pre_query = f"""
    SELECT CASE 
        WHEN EXISTS (
            SELECT 1 FROM {mother_table} 
            WHERE {comp_name} = $1
        ) THEN TRUE
        ELSE FALSE
    END
    """

    placeholders = [f"${i + 1}" for i in range(len(column_names))]
    placeholder_str = ', '.join(placeholders)

    query = f"""INSERT INTO {table_name} ({number_name}, {', '.join(column_names)})
    SELECT {mother_table}.{number_name}, {placeholder_str}
    FROM {mother_table}
    WHERE {mother_table}.{prefix}_name = {comp_name_index};"""

    return pre_query, comp_name_val, query, column_values

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

    async def upload_PostgreSQL(self, comp_params, db_upload_data):
        """Upload data to the database.
        
        Parameters:
        - table_name (str): Name of the table to upload data to.
        - db_upload_data (dict): Dictionary containing the data to upload."""
        conn = await asyncpg.connect(**self._connect_params)
        
        print('Connection successful. \n')
        table_name = comp_params['db_table_name']

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

    async def link_and_update_table(self, comp_type, db_upload_data) -> bool:
        """Link the component to the mother table and update the database."""
        conn = await asyncpg.connect(**self._connect_params)
        try:
            prequery, name, query, values = get_query_write_link(comp_type, db_upload_data)
            print("Executing pre-query...")
            status = await conn.fetchval(prequery, name)
            if not status:
                print(f"Component {name} not found in the mother table.")
                return False
            else:
                await conn.execute(query, *values)
                print(f'Data for {comp_type} successfully uploaded and linked to the mother table!')
                return True
        except Exception as e:
            print("!" * 90)
            print(f"Error encountered when linking {comp_type} to the mother table.")
            print(e)
            return False
        
    async def GrabSensorOffsets(self, name: str) -> list:
        """Grab the sensor offsets from the database.
        
        Parameters:
        - name (str): Name of the prototype module.
        
        Returns:
        - list: List of tuples containing (x_offset, y_offset, angle_offset) for matching modules."""
        try:
            conn = await asyncpg.connect(**self._connect_params)
            query = """SELECT proto_name, x_offset_mu, y_offset_mu, ang_offset_deg 
                      FROM proto_inspect 
                      WHERE proto_name = $1;"""
            rows = await conn.fetch(query, name.replace('M', 'P'))
            
            matching_offsets = [(row['x_offset_mu'], row['y_offset_mu'], row['ang_offset_deg']) 
                              for row in rows]
            
            return matching_offsets
            
        except Exception as e:
            print("!" * 90)
            print("Error encountered when grabbing sensor offsets from database.")
            print(e)
            return []
        finally:
            if conn:
                await conn.close()
