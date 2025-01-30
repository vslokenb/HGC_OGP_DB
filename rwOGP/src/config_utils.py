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
        'ogp_tray_dir': '/path/to/ogp/tray/directory'
    }

async def update_credentials():
    """Update database credentials after authenticating with current ones."""
    import getpass
    import asyncpg

    # Load settings and config files with error handling
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = yaml.safe_load(f)
            config_file = settings['config_path']

        with open(config_file, 'r') as f:
            current_config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error reading configuration files: {e}")
        return False

    async def verify_credentials(user, password):
        """Helper function to verify database credentials."""
        conn = None
        try:
            conn = await asyncpg.connect(
                host=current_config['host'],
                database=current_config['database'],
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

    def update_config_file(user, password):
        """Helper function to update configuration file."""
        try:
            current_config['user'] = user
            current_config['password'] = password
            with open(config_file, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            return True
        except (IOError, yaml.YAMLError) as e:
            print(f"Error updating configuration file: {e}")
            return False

    # Verify current credentials
    if not await verify_credentials(current_config['user'], current_config['password']):
        return False

    # Get new credentials
    print("\nEnter new credentials:")
    new_user = input("New username: ").strip()
    new_password = getpass.getpass("New password: ").strip()
    confirm_password = getpass.getpass("Confirm password: ").strip()

    if new_password != confirm_password:
        print("Passwords do not match!")
        return False

    # Verify new credentials
    if not await verify_credentials(new_user, new_password):
        return False

    # Update configuration file
    if not update_config_file(new_user, new_password):
        return False

    print("Credentials updated successfully!")
    return


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
    
    # Get the system's default editor
    editor = os.environ.get('EDITOR', 'vim')  # Default to vim if no EDITOR is set
    
    # Ask user if they want to edit the configuration
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
    return None
