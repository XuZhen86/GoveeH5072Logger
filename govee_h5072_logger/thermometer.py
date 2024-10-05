from dataclasses import dataclass
from typing import Any

from absl import flags

from govee_h5072_logger.flag import DEVICE_MACS, DEVICE_NAMES, MODELS, NICK_NAMES
from govee_h5072_logger.model import Model


@dataclass(frozen=True)
class Thermometer:
  device_name: str
  device_mac: str
  nick_name: str
  model: Model


# Mapping from device_name to Thermometer for easier indexing.
_THERMOMETERS: dict[str, Thermometer] = dict()


def _parse_thermometers(flag: dict[str, Any]) -> bool:
  if len(DEVICE_NAMES.value) == 0:
    raise flags.ValidationError('')

  if len(DEVICE_NAMES.value) != len(set(DEVICE_NAMES.value)):
    raise flags.ValidationError('Device names contain duplications.')
  if len(DEVICE_MACS.value) != len(set(DEVICE_MACS.value)):
    raise flags.ValidationError('Device MACs contain duplications.')

  try:
    for item in zip(DEVICE_NAMES.value, DEVICE_MACS.value, NICK_NAMES.value, MODELS.value, strict=True):
      _THERMOMETERS[item[1]] = Thermometer(*item)
  except ValueError as e:
    raise flags.ValidationError('Flags must have the same length.') from e

  return True


flags.register_multi_flags_validator((DEVICE_NAMES, DEVICE_MACS, NICK_NAMES, MODELS), _parse_thermometers)


def get_thermometer(device_mac: str) -> Thermometer:
  try:
    return _THERMOMETERS[device_mac]
  except KeyError as e:
    raise ValueError('Unexpected thermometer device mac.') from e
