import os, yaml
from os.path import join as pjoin

SETTINGS_FILE = pjoin(os.path.expanduser('~'), ".my-cli-tool", "settings.yaml")

def get_config_location():
    """Get the configuration file location based on user preference."""
    print("Do you want to create the config file at a custom location? (y/n)")
    choice = input().strip().lower()

    home_dir = os.path.expanduser('~')

    if choice == 'y':
        print("Please enter the directory where you want to create the config file:")
        custom_path = os.path.expanduser(input().strip())
        if os.path.isdir(custom_path):
            return pjoin(custom_path, "rwOGP_DBconfig.yaml")
    else:
        config_dir = pjoin(home_dir, '.config')
        os.makedirs(config_dir, exist_ok=True)
        return pjoin(config_dir, 'rwOGP_DBconfig.yaml')

def get_default_config():
    """Return the default configuration dictionary."""
    return {
        'host': 'localhost',
        'database': 'hgcdb',
        'user': 'ogp_user',
        'password': 'hgcalpass',
        'inst_code': 'CM',
        'institution_name': 'Carnegie Mellon University',
        'ogp_survey_dir': '/path/to/ogp/survey/directory',
        'ogp_parsed_dir': '/path/to/ogp/parsed/directory',
        'ogp_tray_dir': '/path/to/ogp/tray/directory',
        'ogp_image_dir': '/path/to/ogp/image/directory',
    }

async def update_directorys():
    """Update directory paths in the configuration file.
    
    Updates the following directory configurations:
    - ogp_survey_dir: Directory containing OGP survey files
    - ogp_parsed_dir: Directory for parsed OGP data
    - ogp_tray_dir: Directory for tray information
    - ogp_image_dir: Directory for OGP images
    """
    try:
        # Load current configuration
        with open(SETTINGS_FILE, 'r') as f:
            settings = yaml.safe_load(f)
            config_file = settings['config_path']
        with open(config_file, 'r') as f:
            current_config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error reading configuration files: {e}")
        return False

    # Directory configurations to update
    dir_configs = {
        'ogp_survey_dir': 'OGP survey files',
        'ogp_parsed_dir': 'parsed OGP data',
        'ogp_tray_dir': 'tray information',
        'ogp_image_dir': 'OGP images'
    }

    def validate_directory(dir_path):
        """Validate and create directory if user confirms."""
        dir_path = os.path.expanduser(dir_path)
        dir_path = os.path.abspath(dir_path)
        
        if not os.path.exists(dir_path):
            print(f"\nDirectory does not exist: {dir_path}")
            create = input("Would you like to create it? (y/n): ").strip().lower()
            if create == 'y':
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"Created directory: {dir_path}")
                except OSError as e:
                    print(f"Error creating directory: {e}")
                    return None
            else:
                return None
        
        if not os.access(dir_path, os.W_OK):
            print(f"Warning: No write permission for directory: {dir_path}")
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return None
        
        return dir_path

    missing_dirs = []
    print("\nCurrent directory configurations:")
    for key, desc in dir_configs.items():
        if key not in current_config:
            missing_dirs.append(key)
        else:
            print(f"{desc}: {current_config[key]}")
    if missing_dirs:
        print("\nWARNING: The following required directories were missing from config and have been added with default values:")
        for key in missing_dirs:
            print(f"\nSetting up {dir_configs[key]} directory")
            max_attempts = 3 
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                new_path = input(f"Enter path for {dir_configs[key]}: ").strip()

                if not new_path:
                    print("Path cannot be empty. Please enter a valid path.")
                    continue

                validated_path = validate_directory(new_path)
                if validated_path:
                    current_config[key] = validated_path
                    print(f"Successfully set {dir_configs[key]} to: {validated_path}")
                    break # break out of while loop if success
                
                if attempts < max_attempts:
                    retry = input("Would you like to try another path? (y/n): ").strip().lower()
                    if retry != 'y':
                        current_config[key] = '/path/to/ogp/' + key.replace('ogp_', '').replace('_dir', '')
                        print(f"Using default path: {current_config[key]}")
                        print("You can update this later using the directory update menu.")
                        break
            if attempts == max_attempts:
                print("Max attempts reached. Skipping directory setup.")
                current_config[key] = '/path/to/ogp/' + key.replace('ogp_', '').replace('_dir', '')
                print(f"Using default path: {current_config[key]}")
                print("This does not guarantee that the path is valid. Please update this later using the directory update menu.")
                break

    print("\nWhich directory would you like to update?")
    print("1. OGP survey directory")
    print("2. Parsed data directory")
    print("3. Tray information directory")
    print("4. Image directory")
    print("5. All directories")
    print("6. Cancel")

    choice = input("Enter your choice (1-6): ").strip()

    if choice == '6':
        print("Operation cancelled.")
        return False

    def update_single_directory(key, desc):
        """Update a single directory configuration."""
        print(f"\nUpdating {desc} directory")
        new_path = input(f"Enter new path [{current_config[key]}]: ").strip()
        
        if not new_path:  # Keep existing path
            return True
            
        validated_path = validate_directory(new_path)
        if validated_path:
            current_config[key] = validated_path
            return True
        return False

    success = True
    if choice == '5':  # Update all directories
        for key, desc in dir_configs.items():
            if not update_single_directory(key, desc):
                success = False
                break
    elif choice in ['1', '2', '3', '4']:
        # Map choice to directory key
        key = list(dir_configs.keys())[int(choice) - 1]
        success = update_single_directory(key, dir_configs[key])
    else:
        print("Invalid choice!")
        return False

    if success:
        try:
            with open(config_file, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            print("\nDirectory configuration updated successfully!")
            return True
        except (IOError, yaml.YAMLError) as e:
            print(f"Error updating configuration file: {e}")
            return False
    
    return False

async def update_credentials():
    """Update database credentials and/or database connection details after authenticating with current ones."""
    import getpass
    import asyncpg

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = yaml.safe_load(f)
            config_file = settings['config_path']
        with open(config_file, 'r') as f:
            current_config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error reading configuration files: {e}")
        return False

    async def verify_credentials(host, database, user, password):
        """Helper function to verify database credentials."""
        conn = None
        print(f"Connecting to database {database} at {host} using provided credentials ...")
        try:
            conn = await asyncpg.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
        finally:
            if conn is not None:
                await conn.close()

    def update_config_file(host, database, user, password):
        """Helper function to update configuration file."""
        try:
            current_config['host'] = host
            current_config['database'] = database
            current_config['user'] = user
            current_config['password'] = password
            with open(config_file, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            return True
        except (IOError, yaml.YAMLError) as e:
            print(f"Error updating configuration file: {e}")
            return False

    if not await verify_credentials(
        current_config['host'],
        current_config['database'],
        current_config['user'],
        current_config['password']
    ):
        return False

    print("\nWhat would you like to update?")
    print("1. Database credentials only")
    print("2. Database, user, and password")
    print("3. Host, database, user, and password")
    choice = input("Enter your choice (1/2/3): ").strip()

    new_host = current_config['host']
    new_database = current_config['database']
    
    if choice == '3':
        print("\nEnter new database connection details:")
        new_host = input(f"New host [{current_config['host']}]: ").strip()
        if not new_host:
            new_host = current_config['host']
        
        new_database = input(f"New database name [{current_config['database']}]: ").strip()
        if not new_database:
            new_database = current_config['database']
    elif choice == '2':
        new_database = input(f"New database name [{current_config['database']}]: ").strip()
        if not new_database:
            new_database = current_config['database']
    elif choice != '1':
        print("Invalid choice!")
        return False

    print("\nEnter new credentials:")
    new_user = input("New username: ").strip()
    new_password = getpass.getpass("New password: ").strip()
    confirm_password = getpass.getpass("Confirm password: ").strip()

    if new_password != confirm_password:
        print("Passwords do not match!")
        return False

    if not await verify_credentials(new_host, new_database, new_user, new_password):
        return False

    if not update_config_file(new_host, new_database, new_user, new_password):
        return False

    print("Configuration updated successfully!")
    return True

def create_settings_file(config_file):
    """Create settings file with config and inventory paths."""
    home_dir = os.path.expanduser('~')
    settings_dir = pjoin(home_dir, '.my-cli-tool')
    os.makedirs(settings_dir, exist_ok=True)
    
    inventory_path = pjoin(settings_dir, 'inventory.json')
    settings = {
        'config_path': config_file,
        'inventory_path': inventory_path
    }
    with open(SETTINGS_FILE, 'w') as f:
        yaml.dump(settings, f)

def create_default_config():
    """Create a default YAML configuration file and a SETTINGS file, then open it for editing."""
    config_file = get_config_location()
    
    print("Creating default configuration file...")
    with open(config_file, 'w') as f:
        yaml.dump(get_default_config(), f, default_flow_style=False)

    print(f"Configuration file created at {config_file}")
    
    editor = os.environ.get('EDITOR', 'vim')  # Default to vim if no EDITOR is set
    
    print("\nWould you like to edit the configuration file now? (y/n)")
    if input().strip().lower() == 'y':
        try:
            os.system(f'{editor} {config_file}')
            print("\nConfiguration file has been updated.")
        except Exception as e:
            print(f"\nError opening editor: {e}")
            print("Please update the configuration file manually!")
    else:
        print("\nPlease update the configuration file with the correct database connection information!")

    create_settings_file(config_file)

def load_config():
    """Load the configuration file from the default location."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return yaml.safe_load(f)
    return None
