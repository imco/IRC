from setuptools import find_packages, setup

NAME = 'compranet'
DESCRIPTION = 'Análisis de las contrataciones del gobierno (Compranet)'
URL = 'https://github.com/opintel/como-identificar-focos-rojos-en-contrataciones-publicas'
EMAIL = 'raul.peralta@opi.la'
AUTHOR = 'Raul Peralta'

REQUIRED = [
    'pandas', 'numpy', 'dask',
    'matplotlib', 'seaborn', 'distributed',
    'joblib', 'scikit-learn'
]

setup(
    name=NAME,
    version='0.0.1',
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    package_dir={'': 'src'},
    install_requires=REQUIRED,
    include_package_data=True,
    license='GPL-3.0',
)
