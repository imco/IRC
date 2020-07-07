from setuptools import find_packages, setup

NAME = 'compranet'
DESCRIPTION = 'Análisis de las contrataciones del gobierno (Compranet)'
URL = 'https://github.com/opintel/como-identificar-focos-rojos-en-contrataciones-publicas'
EMAIL = 'raul.peralta@opi.la'
AUTHOR = 'Raul Peralta'

REQUIRED = [
    'dask',
    'distributed',
    'feather-format',
    'joblib',
    'matplotlib',
    'numpy',
    'pandas',
    'pytest',
    'python-snappy',
    'scikit-learn',
    'seaborn',
    'snappy'
]

setup(
    name=NAME,
    version='0.0.1',
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    package_dir={'': 'src'},
    packages=['features', 'utils'],
    install_requires=REQUIRED,
    include_package_data=True,
    license='GPL-3.0',
)
