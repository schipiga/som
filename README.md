- [Annotation](#annotation)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [How to specify control points](#how-to-specify-control-points)
- [Classes and methods](classes-and-methods)

## Annotation

This jython tiny library wraps low-level [sikuli](http://sikulix.com/) methods and provides high-level API to manage elements of tested application.

[Sikuli](http://sikulix.com/) (current version is [1.1.2](https://launchpad.net/sikuli/sikulix/1.1.2)) is cross-platform testing tool based on image recognition and written with [java](https://java.com/).
For [python](https://www.python.org/) developers it can be used via [jython](http://www.jython.org/).

## Quick start

As quick start you can try to launch [example](https://github.com/schipiga/som/tree/master/example):

- Install firefox (it will be the tested application).
- Install jython. Current actual version is [2.7.1](http://fwierzbicki.blogspot.com.ee/2017/07/jython-271-final-released.html) but on old operating systems it may not work. So then try older versions.
- Download sikuli [installer](https://launchpad.net/sikuli/sikulix/1.1.2). And launch it to install sikuli. After installation you should have file `sikulix.jar` or `sikulix-api.jar` (depending on specified options during installation).
- Specify java CLASSPATH: `export CLASSPATH=/path/to/sikulix.jar`
- Launch tests: `jython example/tests.py -v`
- If it will be ok you will see how it opens `https://github.com` and `https://yandex.ru` in Firefox. Or see how it was on my PC: https://youtu.be/cSWbNXf-AYI.

## How it works

SOM uses control points of application element (small screenshots).
It builds element visibility area according to screenshots coordinates and uses this area for element management.
It allows to nest elements inside other elements and search element inside area of its parent (container).

## How to specify element points

Firstly create folder where elements screenshots will be. Then inside it for each element create a folder with control name. Then elements screenshots will be saved to separated folders.

There are several types of control points:

- **For visibility** - these screenshots will be used to define visibility status of element. Just save some `png` screenshots with random names to element folder. And then specify folder name when create element:

    ```python
    som.Element.set_elements_dir("/path/to/application/elements/folder")
    address_bar = som.Element("address-bar")
    ```

    If you want to nest one element to another just make next:

    ```python
    window = som.Element("window")
    window.set_children(address_bar=address_bar)
    ```

- **For click** - this screenshot defines area which will be used for click and double click. And it requires special file name `click.png`. By default SOM (as sikuli) clicks to image center. And if you need to add click offset from center you should specify it in file name. For example, `click_10_5.png` provides offset `10px` by `X` and `5px` by `Y` from image center, or `click_-5_-10.png` provides offset `-5px` by `X` and `-10px` by `Y` from center.

- **For select/unselect** - will be used to select / unselect check box or radio button. By default it's enough to provide `select.png` (coordinates offset rules the same as above). But also you can provide `unselect.png` which may be used to define visibility of element.

- **For text typing** - this screenshot defines area which will be used for text typing. Its filename should be `text.png`.

## Classes and methods

- [`load_sikuli`](https://github.com/schipiga/som/blob/master/som.py#L48) - function to import sikuli inside tests set up and passes callback to tune up sikuli. I found strange problem when sikuli is imported in module header it breaks unittest module. That's why it needs to import sikuli only after unittest initialization.

- [`Application`](https://github.com/schipiga/som/blob/master/som.py#L83) - class to launch application via [subprocess](https://docs.python.org/2/library/subprocess.html) module. Has methods:

    - `launch` - launch application.
    - `close` - close application.
    - `set_children` - set children-elements of application.

- [`Element`](https://github.com/schipiga/som/blob/master/som.py#L170) - application element. Has methods:

    - `set_elements_dir` _(static)_ - set elements images folders.
    - `set_timeout` _(static)_ - set timeout to wait element (`10 sec` by default).
    - `click` - click element.
    - `double_click` - click element double.
    - `select` - select element (check box or radio button).
    - `unselect` - unselect element.
    - `set_text` - type text in element.
    - `get_text` - retrieve text from element area (based on OCR).
    - `screenshot` - make element area screenshot.
    - `is_selected` - property to define whether element is selected or no.
    - `is_visible` - property to define whether element is visible or no.
    - `wait_for_visible` - wait for element will be visible.
    - `wait_for_invisible` - wait for element will be invisible.
