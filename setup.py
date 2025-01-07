from setuptools import setup, find_packages

setup(
    name="sql-builder",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pandas>=2.0.0',
        'openpyxl>=3.0.0',
        'sqlparse',
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A SQL builder tool",
    keywords="sql, builder, gui",
    python_requires='>=3.8',
) 