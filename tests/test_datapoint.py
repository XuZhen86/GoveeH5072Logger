import time
from decimal import Decimal
from unittest.mock import Mock, patch

from absl.testing import absltest

from govee_h5072_logger.datapoint import DataPoint
from govee_h5072_logger.model import Model
from govee_h5072_logger.thermometer import Thermometer


class TestDataPoint(absltest.TestCase):
  H5072 = Thermometer('d', '00:00:00:00:50:72', 'n', Model.H5072)
  H5105 = Thermometer('d', '00:00:00:00:51:05', 'n', Model.H5105)
  BATTERY_PERCENT = 57
  RSSI = -75

  def test_h5072_positiveTemperature(self):
    self.assertEqual(
        DataPoint.build(self.H5072, bytes.fromhex('0103aecd39'), self.RSSI),
        DataPoint(self.H5072.device_name, self.H5072.nick_name, self.H5072.model, Decimal('24.1'), Decimal('35.7'),
                  self.BATTERY_PERCENT, self.RSSI),
    )

  def test_h5072_negativeTemperature(self):
    self.assertEqual(
        DataPoint.build(self.H5072, bytes.fromhex('0183aecd39'), self.RSSI),
        DataPoint(self.H5072.device_name, self.H5072.nick_name, self.H5072.model, Decimal('-24.1'), Decimal('35.7'),
                  self.BATTERY_PERCENT, self.RSSI),
    )

  @patch.object(time, 'time_ns', Mock(return_value=69420))
  def test_h5072_toPoints(self):
    points = DataPoint.build(self.H5072, bytes.fromhex('0183aecd39'), self.RSSI).to_points()

    self.assertListEqual([p.to_line_protocol() for p in points], [
        'thermometer,device_name=d,model=H5072,nick_name=n,scale_factor=10,unit=°C temperature=-241i 69420',
        'thermometer,device_name=d,model=H5072,nick_name=n,scale_factor=10,unit=%RH humidity=357i 69420',
        'thermometer,device_name=d,model=H5072,nick_name=n,scale_factor=1,unit=% battery=57i 69420',
        'thermometer,device_name=d,model=H5072,nick_name=n,scale_factor=1,unit=dBm rssi=-75i 69420',
    ])

  def test_h5072_100Humidity(self):
    with self.assertRaises(ValueError):
      DataPoint.build(self.H5072, bytes.fromhex('01ffffff39'), self.RSSI)

  def test_h5105_positiveTemperature(self):
    self.assertEqual(
        DataPoint.build(self.H5105, bytes.fromhex('010103aecd'), self.RSSI),
        DataPoint(self.H5105.device_name, self.H5105.nick_name, self.H5105.model, Decimal('24.1'), Decimal('35.7'),
                  None, self.RSSI),
    )

  def test_h5105_negativeTemperature(self):
    self.assertEqual(
        DataPoint.build(self.H5105, bytes.fromhex('010183aecd'), self.RSSI),
        DataPoint(self.H5105.device_name, self.H5105.nick_name, self.H5105.model, Decimal('-24.1'), Decimal('35.7'),
                  None, self.RSSI),
    )

  def test_h5105_humidity100(self):
    with self.assertRaises(ValueError):
      DataPoint.build(self.H5105, bytes.fromhex('0101ffffff'), self.RSSI)

  @patch.object(time, 'time_ns', Mock(return_value=69420))
  def test_h5105_toPoints(self):
    points = DataPoint.build(self.H5105, bytes.fromhex('010183aecd'), self.RSSI).to_points()

    self.assertListEqual([p.to_line_protocol() for p in points], [
        'thermometer,device_name=d,model=H5105,nick_name=n,scale_factor=10,unit=°C temperature=-241i 69420',
        'thermometer,device_name=d,model=H5105,nick_name=n,scale_factor=10,unit=%RH humidity=357i 69420',
        'thermometer,device_name=d,model=H5105,nick_name=n,scale_factor=1,unit=dBm rssi=-75i 69420',
    ])
