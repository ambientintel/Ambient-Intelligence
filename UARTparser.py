import serial
import time
import math
import datetime
import json_fix # import this anytime before the JSON.dumps gets called
import json
import numpy
json.fallback_table[numpy.ndarray] = lambda array: array.tolist()

# Logger
import logging
log = logging.getLogger(__name__)

# Local Imports
from parseFrame import *
from demo_defines import *