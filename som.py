"""
-------------------
Sikuli Object Model
-------------------
"""

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import functools
import java.lang.System as system
import os
import os.path as path
import re
import signal
import shlex
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
    """Loads sikuli and provides callback to set up it.

    Args:
        cb (func): Callback function which passes sikuli module.
    """
    import sikuli
    global SI
    SI = sikuli
    cb and cb(SI)


class Tree(object):
    """Tree"""

    def set_children(self, **children):
        """Sets instance children.

        Args:
            **children: Sequence of child names and child instances. A child
                should have method `clone`.
        
        Raises:
            KeyError: If child name is equal to existing instance property name.
        """
        for name, child in children.iteritems():
            if hasattr(self, name):
                raise KeyError(
                    "Element '{}' already has property '{}'".format(self._name,
                                                                    name))
            setattr(self, name, child.clone(parent=self))


class Application(Tree):
    """Binary application"""

    def __init__(self, cmd):
        """Creates instance of application.

        Args:
            cmd (str): Name or path (with arguments if needs) to application.
        """
        self._cmd = shlex.split(cmd)
        self._p = None
        self._is_win = system.getProperty('os.name').lower() == "windows"
        self.is_visible = SI.SCREEN  # Hack to not break elements hierarchy.

    def launch(self):
        """Launches application. Will be skipped if it is already launched."""
        if self._p:
            return

        self._p = subprocess.Popen(self._cmd)

    def close(self):
        """Closes application. Will be skipped if it is already closed."""
        if not self._p:
            return

        if (self._is_win):
            subprocess.check_call(
                "taskkill /pid {} /T /F".format(self._p.pid), shell=True)
        else:
            os.kill(self._p.pid, signal.SIGTERM)
        self._p = None


def wait_for(predicate, timeout, polling=0.1):
    """Waits for predicate will return truly value.

    Args:
        predicate (func): Function which is result is expected to be truly.
        timeout (num): Time to wait for result, sec.
        polling (num): Time to poll for result, sec.

    Returns:
        obj|bool: Result of predicate if it is truly or false.
    """
    limit = time.time() + timeout
    while (limit > time.time()):
        result = predicate()
        if (result):
            return result
        time.sleep(polling)
    return False


def wait_for_visible(func):
    """Decorator to wait for element visibility before to make some action."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwgs):
        self.wait_for_visible()
        return func(self, *args, **kwgs)

    return wrapper


def make_pattern(image_path):
    """Creates sikuli pattern to interact with image.

    Args:
        image_path (str): Path to image.

    Returns:
        Pattern: Sikuli pattern object with coordinates offset if it was
            retrieved from file name.
    """
    result = SI.Pattern(image_path)

    filename = path.basename(image_path)
    match = re.search(r"(-?\d+)_(-?\d+)", filename)
    if match:
        x, y = match.groups()
        result = result.targetOffset(int(x), int(y))

    return result


class Element(Tree):
    """Application element"""

    ELEMENTS_DIR = None
    TIMEOUT = 10

    @classmethod
    def set_elements_dir(cls, dir):
        """Sets elements images folder.

        Args:
            dir (str): Path to folder with elements images.
        """
        cls.ELEMENTS_DIR = dir

    @classmethod
    def set_timeout(cls, timeout):
        """Sets element waiting timeout.

        Args:
            timeout (num): Time to wait for element, sec.
        """
        cls.TIMEOUT = timeout

    def __init__(self, name, parent=None):
        """Creates element instance.

        Args:
            name (str): Name of element. Should match folder name inside
                elements images folder.
            parent (Element): Parent (container) of element.
        """
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
        """Clones current element.
        
        Args:
            name (str): Name of new element.
            parent (Element): Parent of new element.

        Returns:
            Element: New element.
        """
        name = name or self._name
        parent = parent or self.parent
        return self.__class__(name, parent)

    @property
    def parent(self):
        """Gets element parent.
        
        Raises:
            LookupError: If parent was destroyed.

        Returns:
            obj|None: Parent object or none.
        """
        if not self._parent:
            return self._parent
        _parent = self._parent()
        if _parent:
            return _parent
        else:
            raise LookupError("Parent was destroyed")

    @property
    def click_image(self):
        """Gets image to click.

        Raises:
            LookupError: If image to click isn't specified.

        Returns:
            Pattern: Image to click.
        """
        if not self._click_image:
            raise LookupError("Image to click isn't specified")
        return self._click_image

    @wait_for_visible
    def click(self):
        """Clicks element."""
        self._region.click(self.click_image)

    @property
    def select_image(self):
        """Gets image to select element.

        Raises:
            LookupError: If image to select isn't specified.

        Returns:
            Pattern: Image to select element.
        """
        if not self._select_image
            raise LookupError("Image to select isn't specified")
        return self._select_image

    @wait_for_visible
    def select(self):
        """Selects element. Will be skipped if element is selected already."""
        if not self.is_selected:
            self._region.click(self.select_image)

    @wait_for_visible
    def unselect(self):
        """Unselects element. Will be skipped if element isn't selected yet."""
        if self.is_selected:
            self._region.click(self.select_image)

    @property
    def text_image(self):
        """Gets image to type text.

        Raises:
            LookupError: If image to type text isn't specified.

        Returns:
            Pattern: Image to type text.
        """
        if not self._text_image
            raise LookupError("Image to type text isn't specified")
        return self._text_image

    @wait_for_visible
    def set_text(self, text):
        """Types text to element."""
        self._region.type(self._text_image, text)

    @wait_for_visible
    def get_text(self):
        """Gets text from element.

        Returns:
            str: Retrieved text.
        """
        return self._region.text()

    @wait_for_visible
    def screenshot(self, dir=None, filename=None):
        """Make screenshot of element.

        Args:
            dir (str): Path to folder to save screenshot. Current work directory
                is default.
            filename (str): Name of screeshot file. UUID.png is default.

        Returns:
            str: Path to saved image.
        """
        dir = dir or os.getcwd()
        filename = filename or str(uuid.uuid4())
        if not filename.endswith(".png"):
            filename += ".png"
        return self._region.getScreen().capture(self, dir, filename)

    @property
    @wait_for_visible
    def is_selected(self):
        """Defines is element selected.

        Returns:
            obj|None: Matched object or none.
        """
        return self._region.exists(self.select_image.filename, 0)

    @property
    def is_visible(self):
        """Defines is element visible.

        Returns:
            obj|None: Matched object or none.
        """
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
        """Waits for element will be visible.

        Args:
            timeout (num): Time to wait for element will be visible, sec.

        Raises:
            LookupError: If element is not visible after timeout.

        Returns:
            obj: Matched object.
        """
        timeout = timeout or self.TIMEOUT

        if wait_for(lambda: self.is_visible, timeout, polling=0.5):
            return self._region

        raise LookupError(
            "Element '{}' is not visible after {}s".format(self._name,
                                                           timeout))

    def wait_for_invisible(self, timeout=None):
        """Waits for element will not be visible.

        Args:
            timeout (num): Time to wait for element will not be visible, sec.

        Raises:
            LookupError: If element is still visible after timeout.
        """
        timeout = timeout or self.TIMEOUT

        if wait_for(lambda: not self.is_visible, timeout, polling=0.5):
            return None

        raise LookupError(
            "Element '{}' is visible after {}s".format(self._name,
                                                       timeout))
