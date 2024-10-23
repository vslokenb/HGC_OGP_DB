from setuptools import setup, find_packages

setup(
    name="read-write-ogp",
    version="0.1.0",                   
    packages=find_packages(where="read-write-ogp/src"),  # Required: Specify the package directory
    package_dir={"": "read-write-ogp/src"},
    install_requires=[                 # List of dependencies
        "pwinput>=1.0.0",
        "numpy>=1.20.0",
        "pandas>=2.0.0",
        "asyncpg>=0.24.0",
    ],
    entry_points={                      # Optional: Entry points for command-line scripts
        "console_scripts": [
            "uploadOGPresults=main:main_func",
        ],
    },
    author="CMU HGCal MAC",
    description="A short description of your package",
    long_description=open("README.md").read(),  # Optional: long description from README
    long_description_content_type="text/markdown",  # README format (Markdown)
    url="https://github.com/cmu-hgc-mac/HGC_OGP_DB",  # GitHub repository URL
    classifiers=[                       # Optional: Package classification for PyPI
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent ",
    ],
    python_requires='>=3.6',            # Minimum Python version requirement
)
