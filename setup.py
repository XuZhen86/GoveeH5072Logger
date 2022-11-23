import setuptools

setuptools.setup(
    name='govee-h5072-logger',
    version='0.1',
    author='XuZhen86',
    url='https://github.com/XuZhen86/GoveeH5072Logger',
    packages=setuptools.find_packages(),
    python_requires='>=3.11',
    install_requires=[
        'absl-py>=1.3.0',
        'bleak>=0.19.5',
        'pymysql>=1.0.2',
    ],
    entry_points={
        'console_scripts': ['govee-h5072-logger = src.main:app_run_govee_h5072_logger',],
    },
)
