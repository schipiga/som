import sys
sys.path.append("/home/user/vega/apps/sikuli/sikulix.jar/Lib")
sys.path.append(".")

import unittest

import steps


S = None


class MyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global S
        S = steps.Steps()

    def setUp(self):
        S.launch_firefox()
        self.addCleanup(S.close_firefox)

    def test_open_yandex(self):
        S.open_web_page("https://yandex.ru")
    
    def test_open_github(self):
        S.open_web_page("https://github.com")


if __name__ == '__main__':
    unittest.main()
