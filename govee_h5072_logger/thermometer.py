from dataclasses import dataclass

from absl import flags, logging

_THERMOMETERS = flags.DEFINE_multi_string(
    name='thermometers',
    default=None,
    required=True,
    help='A list of thermometers to record.'
    ' Example:'
    ' --thermometers=GVH5072_12AB:Garage'
    ' --thermometers=GVH5072_34CD:Kitchen.',
)

SQL_CREATE_TABLE = '''
  CREATE
  OR REPLACE TABLE Thermometers (
    device_name  TINYTEXT  NOT NULL,
    nick_name    TINYTEXT  NOT NULL
  );
'''

SQL_INSERT = '''
  INSERT INTO
    Thermometers (device_name, nick_name)
  VALUES
    (%(device_name)s, %(nick_name)s);
'''


@dataclass
class Thermometer:
  device_name: str
  nick_name: str


def thermometers_from_flags() -> list[Thermometer]:
  thermometers = [Thermometer(*flag_str.split(':')) for flag_str in _THERMOMETERS.value]
  logging.info('thermometers = %s', thermometers)
  return thermometers
