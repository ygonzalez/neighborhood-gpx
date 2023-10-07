from setuptools import setup, find_packages

setup(
    name="your_project_name",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "geopandas"=="0.14.0",
        "networkx>=2.4",
        "matplotlib>=3.2.1",
        "numpy>=1.18.5",
        "notebook",
    ],
    dependency_links=[
        "git+https://github.com/gboeing/osmnx.git@main#egg=osmnx"
    ],
    extras_require={
        ":sys_platform == 'darwin'": ["appnope"],
    },
)
