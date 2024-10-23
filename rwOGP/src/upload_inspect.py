import sys, yaml, asyncpg
sys.path.append('../')
## comptable = {'baseplate':{'prefix': 'bp', 'pkprefix': 'bp'},'hexaboard':{'prefix': 'hxb', 'pkprefix': 'hxb'},'protomodule':{'prefix': 'proto', 'pkprefix': 'proto'},'module':{'prefix': 'module', 'pkprefix': 'module'}}

comptable = {'baseplate':{'prefix': 'bp'},'hexaboard':{'prefix': 'hxb'},'protomodule':{'prefix': 'proto'},'module':{'prefix': 'module'}}

def get_query_read(component_type, part_name = None, comptable=comptable):
    """Get the query to read from the database."""
    if part_name is None:
        query = f"""SELECT {comptable[component_type]['prefix']}_name FROM {comptable[component_type]['prefix']}_inspect ORDER BY {comptable[component_type]['prefix']}_row_no DESC LIMIT 10;"""
    else:
        query = f"""SELECT hexplot FROM {comptable[component_type]['prefix']}_inspect WHERE {comptable[component_type]['prefix']}_name = '{part_name}'"""
    return query

def get_query_write(table_name, column_names):
    """Get the query to write to the database."""
    pre_query = f""" INSERT INTO {table_name} ({', '.join(column_names)}) VALUES """
    data_placeholder = ', '.join(['${}'.format(i) for i in range(1, len(column_names)+1)])
    query = f"""{pre_query} {'({})'.format(data_placeholder)}"""
    return query

class DBClient():
    """Client to interact with the PostgreSQL database."""
    def __init__(self, yamlconfig):
        """Initialize the database client.
        
        Parameters:
        - yamlconfig (str): Path to the yaml configuration file, containing database connection information."""
        with open(yamlconfig, 'r') as f:
            config = yaml.safe_load(f)
        self.host = config['host']
        self.database = config['database']
        self.user = config['user']
        self.password = config['password']

    async def fetch_PostgreSQL(self, query):
        conn = await asyncpg.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )
        value = await conn.fetch(query)
        await conn.close()
        return value

    async def request_PostgreSQL(self, component_type, bp_name = None):
        result = await self.fetch_PostgreSQL(get_query_read(component_type, bp_name ))
        return result

    async def upload_PostgreSQL(self, table_name, db_upload_data):
        """Upload data to the database.
        
        Parameters:
        - table_name (str): Name of the table to upload data to.
        - db_upload_data (dict): Dictionary containing the data to upload."""
        conn = await asyncpg.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)
        
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
        table_exists = await conn.fetchval(table_exists_query, schema_name, table_name)  ### Returns True/False
        if table_exists:
            query = get_query_write(table_name, db_upload_data.keys())
            await conn.execute(query, *db_upload_data.values())
            print(f'Executing query: {query}')
            print(f'Data successfully uploaded to the {table_name}!')
        else:
            print(f'Table {table_name} does not exist in the database.')
        await conn.close()

    @staticmethod
    async def GrabSensorOffsets(name):
        """Grab the sensor offsets from the database."""
        try:
            conn = await asyncpg.connect(
                host='gut.physics.ucsb.edu',
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
