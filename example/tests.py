import os
import sys
sys.path.append(os.path.join(os.environ["CLASSPATH"], "Lib"))  # path to load sikuli
sys.path.append(".")  # path to load example modules

import unittest

import steps

# Steps instance will be here. It needs to create it after unittest initialization
# because sikuli import breaks jython unittest module, dunno why.
S = None


class MyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global S
        S = steps.Steps()

    def setUp(self):
        S.launch_firefox()
    
    def tearDown(self):
        S.close_firefox()

    def test_open_yandex(self):
        S.open_web_page("https://yandex.ru")
    
    def test_open_github(self):
        S.open_web_page("https://github.com")


if __name__ == '__main__':
    unittest.main()
