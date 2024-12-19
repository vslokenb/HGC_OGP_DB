# Package for OGP + Database: rwOGP
This package is intended to be used to read and write data from the OGP to a local database. The package is divided into two parts: 
1. CLI tool for automatic upload of data from the OGP to the local database.
2. GUI to read data from the local database to the OGP

## Getting started
Set the output template of all OGP survey programs to be [OGP_template.txt](https://github.com/cmu-hgc-mac/HGC_OGP_DB/blob/main/rwOGP/templates/OGP_template.txt) file.

### Method 1: Run Python directly
Clone the repository and install the required packages:
```
git clone git@github.com:cmu-hgc-mac/HGC_OGP_DB.git
```
Run the following command to postprocess and upload the OGP survey results to the database:
```
cd HGC_OGP_DB
python rwOGP/main.py
```

### Method 2: Install as a package (Under Development)
In Python 3.6 or greater on the OGP computer: 
```
pip install git+https://github.com/cmu-hgc-mac/HGC_OGP_DB.git
```
Then run in terminal
```
uploadOGPresults
```
If run for the first time, this prompts user to enter a secure folder/directory to create a configuration file containing information about database connection and OGP survey results. Modify the configuration file to include the correct information.

Running this command after will automatically postprocess and upload the OGP survey results to the database.

## Troubleshooting
### Missing entries
1. Check if OGP survey program is properly named. Spaces are very likely to cause parsing issues and therefore should be avoided. 
Correct Example: CMU_OGP_module_survey_2024

## How to use:
This GUI contains two tabs: 'View Plots' and 'Upload Files'.
- View plots shows plots data from the OGP. (TBD: Change limit on number of files)
- Upload Files lets the user upload .XLS output files containing OGP meaurements to the local db.
  - The **watch directory** _must contain_ the following subdirectories for the GUI to work:
    - baseplates
    - hexaboards
    - protomodules
    - modules
  - The OGP inspection files _must be configured to write to these locations_ by default type.
    - The .XLS files must be saved with the ID of the component and will be used as the part ID in the db.

![OGP_GUI](https://github.com/murthysindhu/HGC_DB_postgres/assets/58646122/dbeddf4c-2dc8-4da7-8f26-f916d1c69b74)

## Developer's Notes:
### Template change
- If the template is changed, how data is parsed from the OGP output files will also need to be modified accordingly in `src/param.py`.
- The meta data needs to follow the format: 
  ```
  LastModified: {ProjectLastModified}		
  Runtime: {RunDateTime}
  ```
  Otherwise [ttp](https://ttp.readthedocs.io/en/latest/) package will have trouble parsing the data.
  

## Using pgAdmin4 to view tables (Instructions to follow)
Install [postgreSQL-15 with pgAdmin4](https://www.pgadmin.org/download/) on your computers. Make sure you add ```psql``` to your path.


