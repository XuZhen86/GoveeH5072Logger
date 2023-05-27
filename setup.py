import setuptools

setuptools.setup(
    name='govee-h5072-logger',
    version='0.1',
    author='XuZhen86',
    url='https://github.com/XuZhen86/GoveeH5072Logger',
    packages=setuptools.find_packages(),
    python_requires='==3.11.3',
    install_requires=[
        'absl-py==1.4.0',
        'bleak==0.20.2',
        'influxdb-client==1.36.1',
        'line_protocol_cache@git+https://github.com/XuZhen86/LineProtocolCache@a7965f30589af8c318ff7654d307ca9ec7d9f40f',
    ],
    entry_points={
        'console_scripts': [
            'govee-h5072-logger-collect-records = govee_h5072_logger.collectrecords:main',
        ],
    },
)
