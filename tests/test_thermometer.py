from absl.flags import IllegalFlagValueError
from absl.testing import absltest, flagsaver

from govee_h5072_logger.flag import DEVICE_NAMES, MODELS, NICK_NAMES
from govee_h5072_logger.model import Model
from govee_h5072_logger.thermometer import Thermometer, get_thermometer


class TestThermometer(absltest.TestCase):
  THERMOMETERS = [Thermometer('d1', 'n1', Model.H5072), Thermometer('d2', 'n2', Model.H5105)]

  def test_duplicatedDeviceNames(self):
    with self.assertRaises(IllegalFlagValueError):
      with flagsaver.as_parsed((DEVICE_NAMES, [self.THERMOMETERS[0].device_name] * len(self.THERMOMETERS)),
                               (NICK_NAMES, [t.nick_name for t in self.THERMOMETERS]),
                               (MODELS, [t.model.name for t in self.THERMOMETERS])):
        pass

  def test_flagsDifferentLength(self):
    with self.assertRaises(IllegalFlagValueError):
      with flagsaver.as_parsed((DEVICE_NAMES, [t.device_name for t in self.THERMOMETERS]),
                               (NICK_NAMES, [t.nick_name for t in self.THERMOMETERS[:-1]]),
                               (MODELS, [t.model.name for t in self.THERMOMETERS])):
        pass

  @flagsaver.as_parsed((DEVICE_NAMES, [t.device_name for t in THERMOMETERS]),
                       (NICK_NAMES, [t.nick_name for t in THERMOMETERS]),
                       (MODELS, [t.model.name for t in THERMOMETERS]))
  def test_flagsSameLength(self):
    for t in self.THERMOMETERS:
      self.assertEqual(get_thermometer(t.device_name), t)
