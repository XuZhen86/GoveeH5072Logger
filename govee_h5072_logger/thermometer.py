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


@dataclass
class Thermometer:
  device_name: str
  nick_name: str


def thermometers_from_flags() -> dict[str, Thermometer]:
  thermometer_list = [Thermometer(*flag_str.split(':')) for flag_str in _THERMOMETERS.value]
  thermometers = {t.device_name: t for t in thermometer_list}
  logging.info('thermometers = %s', thermometers)
  return thermometers
