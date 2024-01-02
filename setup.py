from setuptools import setup, find_packages

setup(
    name='postgres_da_ai_agent',
    version='0.1.0',
    description='A package for Postgres Data Analytics with AI agent support',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        # Add your package dependencies here
        # 'numpy',
        # 'pandas',
        # 'sqlalchemy',
        # 'psycopg2-binary',
        # 'streamlit',
        # 'sympy', # if you are using sympy in your project
        # Add other dependencies as needed
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            # If you have any scripts you want to be installed with your package, add them here
            # 'script-name = module.path:function_name',
        ],
    },
    include_package_data=True,
    zip_safe=False
)
