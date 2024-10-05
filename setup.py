import setuptools

setuptools.setup(
    name='govee-h5072-logger',
    version='0.1',
    author='XuZhen86',
    url='https://github.com/XuZhen86/GoveeH5072Logger',
    packages=setuptools.find_packages(),
    python_requires='>=3.12,<3.13',
    install_requires=[
        'absl-py>=2.1.0,<2.2',
        'bleak>=0.22.2,<0.23',
        'dbus-fast>=2.24.3,<2.25',
        'influxdb-client==1.39.0',
        'line_protocol_cache@git+https://github.com/XuZhen86/LineProtocolCache@c92e513',
    ],
    entry_points={
        'console_scripts': ['govee-h5072-logger = govee_h5072_logger.main:app_run_main'],
    },
)
