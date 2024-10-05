from absl import flags

from govee_h5072_logger.model import Model

DEVICE_NAMES = flags.DEFINE_multi_string(
    name='device_names',
    default=None,
    required=True,
    help='Bluetooth device names for each thermometer. E.g. "GVH5072_7705".',
)

DEVICE_MACS = flags.DEFINE_multi_string(
    name='device_macs',
    default=None,
    required=True,
    help='Bluetooth device MAC address for each thermometer. E.g. "01:23:45:67:89:AB".',
)

NICK_NAMES = flags.DEFINE_multi_string(
    name='nick_names',
    default=None,
    required=True,
    help='Nick names for each thermometer. E.g. "Garden".',
)

MODELS = flags.DEFINE_multi_enum_class(
    name='models',
    default=None,
    required=True,
    enum_class=Model,
    help='Model for each thermometer. E.g. H5076.',
)
