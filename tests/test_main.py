from types import SimpleNamespace
from unittest.mock import Mock, patch

from absl import logging
from absl.logging.converter import absl_to_standard
from absl.testing import absltest, flagsaver
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from influxdb_client import Point
from line_protocol_cache.lineprotocolcache import LineProtocolCache

from govee_h5072_logger.datapoint import DataPoint
from govee_h5072_logger.flag import DEVICE_NAMES, MODELS, NICK_NAMES
from govee_h5072_logger.main import detection_callback
from govee_h5072_logger.model import Model
from govee_h5072_logger.thermometer import Thermometer


class TestMain(absltest.TestCase):
  THERMOMETERS = [Thermometer('d1', 'n1', Model.H5072), Thermometer('d2', 'n2', Model.H5105)]
  RSSI = -75
  BLE_DEVICE_NO_NAME = BLEDevice('address', None, None, RSSI)
  BLE_DEVICE_UNKNOWN_NAME = BLEDevice('address', 'name', None, RSSI)
  BLE_DEVICE = BLEDevice('address', THERMOMETERS[0].device_name, None, RSSI)
  AD_DATA = AdvertisementData('local-name', {0: b''}, dict(), [], None, RSSI, ())
  POINTS = [Point('m').tag('t', 1).field('f', 1), Point('m').tag('t', 2).field('f', 2)]

  def setUp(self):
    self.saved_flags = flagsaver.as_parsed(
        (DEVICE_NAMES, [t.device_name for t in self.THERMOMETERS]),
        (NICK_NAMES, [t.nick_name for t in self.THERMOMETERS]),
        (MODELS, [t.model.name for t in self.THERMOMETERS]),
    )
    self.saved_flags.__enter__()
    return super().setUp()

  def tearDown(self) -> None:
    self.saved_flags.__exit__(None, None, None)
    return super().tearDown()

  @patch.object(LineProtocolCache, 'put', Mock())
  def test_noDeviceName_noPoints(self):
    detection_callback(self.BLE_DEVICE_NO_NAME, self.AD_DATA)

    LineProtocolCache.put.assert_not_called()

  @patch.object(LineProtocolCache, 'put', Mock())
  def test_unknownDeviceName_noPoints(self):
    detection_callback(self.BLE_DEVICE_UNKNOWN_NAME, self.AD_DATA)

    LineProtocolCache.put.assert_not_called()

  @patch.object(LineProtocolCache, 'put', Mock())
  @patch.object(DataPoint, 'build', Mock(side_effect=ValueError('error-message')))
  def test_dataPointValueError_warns(self):
    with self.assertLogs(logger='absl', level=absl_to_standard(logging.WARNING)) as logs:
      detection_callback(self.BLE_DEVICE, self.AD_DATA)

    self.assertIn(repr(ValueError('error-message')), [record.message for record in logs.records])
    LineProtocolCache.put.assert_not_called()

  @patch.object(LineProtocolCache, 'put', Mock())
  @patch.object(DataPoint, 'build', Mock(return_value=SimpleNamespace(to_points=Mock(return_value=POINTS))))
  def test_putPoints(self):
    detection_callback(self.BLE_DEVICE, self.AD_DATA)

    LineProtocolCache.put.assert_called_once_with(self.POINTS)
