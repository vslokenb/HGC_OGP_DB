import os, yaml

def create_default_config(file_path):
    """Create a default YAML configuration file."""
    default_config = {
        'host': 'localhost',
        'database': 'hgcdb',
        'user': 'ogp_user',
        'password': 'hgcalpass',
        'inst_code': 'CM',
        'institution_name': 'Carnegie Mellon University'
    }
    with open(file_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)