import setuptools

setuptools.setup(
    name='govee-h5072-logger',
    version='0.1',
    author='XuZhen86',
    url='https://github.com/XuZhen86/GoveeH5072Logger',
    packages=setuptools.find_packages(),
    python_requires='==3.12.1',
    install_requires=[
        'absl-py==2.1.0',
        'bleak==0.20.2',
        'influxdb-client==1.39.0',
        'line_protocol_cache@git+https://github.com/XuZhen86/LineProtocolCache@15a676d',
    ],
    entry_points={
        'console_scripts': ['govee-h5072-logger = govee_h5072_logger.main:app_run_main'],
    },
)
