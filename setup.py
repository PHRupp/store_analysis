from setuptools import setup, find_packages

setup(
    name="store_analysis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "openpyxl",
        "SQLAlchemy",
    ],
    python_requires=">=3.8",
)
