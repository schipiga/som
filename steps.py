import os

import som


class Steps(object):

    def __init__(self):

        def setup(sikuli):
            sikuli.Settings.ActionLogs = False
            sikuli.Settings.InfoLogs = False
            sikuli.Settings.DebugLogs = False
            sikuli.Settings.MinSimilarity = 0.95

        som.load_sikuli(setup)
        som.Element.set_elements_dir(os.path.join(os.getcwd(), "elements"))
        self._app = som.Application("firefox")
        self._app.set_children(
            address_bar=som.Element("address-bar"),
            yandex=som.Element("yandex"),
            github=som.Element("github"))

    def launch_firefox(self):
        self._app.launch()

    def open_web_page(self, url, check=True):
        self._app.address_bar.set_text(url, enter=True)
        if check:
            if url.startswith("https://yandex"):
                self._app.yandex.wait_for_visible()
            elif url.startswith("https://github"):
                self._app.github.wait_for_visible()
            else:
                raise Exception("Uncheckable url '{}'".format(url))

    def close_firefox(self):
        self._app.close()
