"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

"""
This is the main module of the plugin manager component.
"""
import logging
import json
import datetime
import yaml
import uuid
import os
import time
from mongoengine import DoesNotExist

import model
import interface



logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("son-fgkeeper")
LOG.setLevel(logging.INFO)
logging.getLogger("messaging").setLevel(logging.INFO)


class Fgkeeper(object):
    """
    This is the core of SONATA's plugin manager component.
    All plugins that want to interact with the system have to register
    themselves to it by doing a registration call.
    """

    def __init__(self):
        # initialize plugin DB model
        model.initialize()

        # start up management interface
        interface.start(self)

        while True:
            time.sleep(5)





def main():
    Fgkeeper()

if __name__ == '__main__':
    main()
