import os

import som


def tuneup_sikuli(sikuli):
    sikuli.Settings.ActionLogs = False
    sikuli.Settings.InfoLogs = False
    sikuli.Settings.DebugLogs = False
    sikuli.Settings.MinSimilarity = 0.95


def create_ff():
    som.Element.set_elements_dir(
        os.path.join(os.getcwd(), "example", "elements"))
    
    ff = som.Application("firefox")
    ff.set_children(
        address_bar=som.Element("address-bar"),
        yandex=som.Element("yandex"),
        github=som.Element("github"))

    return ff


class Steps(object):

    def __init__(self):
        som.load_sikuli(tuneup_sikuli)
        self._ff = create_ff()

    def launch_firefox(self):
        self._ff.launch()

    def open_web_page(self, url):
        self._ff.address_bar.set_text(url, enter=True)

        if url.startswith("https://yandex"):
            self._ff.yandex.wait_for_visible()

        if url.startswith("https://github"):
            self._ff.github.wait_for_visible()

    def close_firefox(self):
        self._ff.close()
