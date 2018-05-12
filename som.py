import functools
import java.lang.System as system
import os
import os.path as path
import re
import signal
import subprocess
import sys
import time
import uuid
import weakref


__all__ = [
    "Application",
    "Element",
    "load_sikuli",
]


SI = None


def load_sikuli(cb=None):
    import sikuli
    global SI
    SI = sikuli
    cb and cb(SI)


class Tree(object):

    def set_children(self, **children):
        for name, child in children.iteritems():
            if hasattr(self, name):
                raise KeyError(
                    "Element '{}' already has property '{}'".format(self._name,
                                                                    name))
            setattr(self, name, child.clone(parent=self))


class Application(Tree):

    def __init__(self, cmd):
        self._cmd = cmd
        self._p = None
        self._is_win = system.getProperty('os.name').lower() == "windows"

    def launch(self):
        self._p = subprocess.Popen(self._cmd)

    def close(self):
        if (self._is_win):
            subprocess.check_call(
                "taskkill /pid {} /T /F".format(self._p.pid), shell=True)
        else:
            os.kill(self._p.pid, signal.SIGTERM)


def wait_for(predicate, timeout, polling=0.1):
    limit = time.time() + timeout
    while (limit > time.time()):
        result = predicate()
        if (result):
            return result
        time.sleep(polling)
    return False


def wait_for_visible(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwgs):
        self.wait_for_visible()
        return func(self, *args, **kwgs)

    return wrapper


def make_pattern(image_path, prefix):
    result = SI.Pattern(image_path)

    filename = path.basename(image_path)
    match = re.search(r"(-?\d+)_(-?\d+)", filename)
    if match:
        x, y = match.groups()
        result = result.targetOffset(int(x), int(y))

    return result


class Element(Tree):

    ELEMENTS_DIR = None
    TIMEOUT = 10

    @classmethod
    def set_elements_dir(cls, dir):
        cls.ELEMENTS_DIR = dir

    @classmethod
    def set_timeout(cls, timeout):
        cls.TIMEOUT = timeout

    def __init__(self, name, parent=None):
        self._name = name
        self._region = None
        self._images = []
        self._click_image = None
        self._text_image = None
        self._select_image = None
        self._unselect_image = None

        element_dir = path.join(self.ELEMENTS_DIR, name)
        for filename in os.listdir(element_dir):

            if not filename.endswith(".png"):
                continue

            image_path = path.join(element_dir, filename)

            if filename.startswith("click"):
                self._click_image = make_pattern(image_path)

            if filename.startswith("text"):
                self._text_image = make_pattern(image_path)

            if filename.startswith("select"):
                self._select_image = make_pattern(image_path)
                continue

            if filename.startswith("unselect"):
                self._unselect_image = make_pattern(image_path)
                continue

            self._images.append(image_path)

        self._parent = weakref.ref(parent) if parent else None

    def clone(self, name=None, parent=None):
        name = name or self._name
        parent = parent or self.parent
        return self.__class__(name, parent)

    @property
    def parent(self):
        if not self._parent:
            return self._parent
        _parent = self._parent()
        if _parent:
            return _parent
        else:
            raise LookupError("Parent was destroyed")

    @wait_for_visible
    def click(self):
        self._region.click(self._click_image)

    @wait_for_visible
    def select(self):
        self._region.click(self._select_image)

    @wait_for_visible
    def unselect(self):
        self._region.click(self._select_image)

    @wait_for_visible
    def set_text(self, text):
        self._region.type(self._text_image, text)

    @wait_for_visible
    def get_text(self):
        return self._region.text()

    @wait_for_visible
    def capture_screen(self, dir=None, filename=None):
        dir = dir or os.getcwd()
        filename = filename or str(uuid.uuid4())
        if not filename.endswith(".png"):
            filename += ".png"
        return self._region.getScreen().capture(self, dir, filename)

    @property
    @wait_for_visible
    def is_selected(self):
        return self._region.exists(self._select_image.filename, 0)

    @property
    def is_visible(self):
        if self.parent:
            parent_region = self.parent.is_visible
            if not parent_region:
                self._region = None
                return None
        else:
            parent_region = SI.SCREEN

        def is_visible(images):
            location = {"x": sys.maxint,
                        "y": sys.maxint,
                        "r": -sys.maxint,
                        "b": -sys.maxint}

            if not images:
                self._region = None
                return None

            for image_path in images:
                image_match = parent_region.exists(image_path, 0)

                if not image_match:
                    self._region = None
                    return None

                if image_match.x < location["x"]:
                    location["x"] = image_match.x

                if image_match.y < location["y"]:
                    location["y"] = image_match.y

                if (image_match.x + image_match.w) > location["r"]:
                    location["r"] = image_match.x + image_match.w

                if (image_match.y + image_match.h) > location["b"]:
                    location["b"] = image_match.y + image_match.h

            location["w"] = location["r"] - location["x"]
            location["h"] = location["b"] - location["y"]

            self._region = SI.Region(location["x"], location["y"],
                                     location["w"], location["h"])
            return self._region

        dirs = [self._images]
        if self._select_image:
            dirs.append([self._select_image.filename])
        if self._unselect_image:
            dirs.append([self._unselect_image.filename])

        if (len(dirs) == 1 and not self._images):
            raise LookupError(
                "Can't define element '{}'".format(self._name) +
                " visibility because no element images are provided")

        result = None
        for images in dirs:
            result = is_visible(images)
            if result:
                break
        return result

    def wait_for_visible(self, timeout=None):
        timeout = timeout or self.TIMEOUT

        if wait_for(lambda: self.is_visible, timeout, polling=0.5):
            return self._region

        raise LookupError(
            "Element '{}' is not visible after {}s".format(self._name,
                                                           timeout))

    def wait_for_invisible(self, timeout=None):
        timeout = timeout or self.TIMEOUT

        if wait_for(lambda: not self.is_visible, timeout, polling=0.5):
            return None

        raise LookupError(
            "Element '{}' is visible after {}s".format(self._name,
                                                       timeout))
