import os
import sys
import tempfile
import time

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebKitWidgets import QWebView

from django.core.files import File
from django_q.tasks import async_task

from .models import Resource, ResourceImage


class FetchScreenshotTimeout(Exception):
    """exception occurring when fetch screenshot operation fails due to taking too long"""


class Screenshot(QWebView):
    # ref: https://stackoverflow.com/a/12031316, ...

    MAX_WIDTH = 2 * 584
    MAX_HEIGHT = 3 * 584
    MAX_LOAD_TIME = 15 * 1000  # in milliseconds

    def __init__(self):
        self.app = QApplication(sys.argv)
        QWebView.__init__(self)
        self._loaded = False
        self.loadFinished.connect(self._loadFinished)

    def capture(self, url, output_file):
        print("loading %s ..." % url)
        self.load(QUrl(url))
        self.wait_load()
        # set to webpage size
        frame = self.page().mainFrame()
        size = frame.contentsSize()
        if size.width() < self.MAX_WIDTH:
            size.setWidth(self.MAX_WIDTH)
        self.page().setViewportSize(size)
        # render image
        size = frame.contentsSize()
        if size.width() > self.MAX_WIDTH:
            size.setWidth(self.MAX_WIDTH)
        if size.height() > self.MAX_HEIGHT:
            size.setHeight(self.MAX_HEIGHT)
        image = QImage(size, QImage.Format_ARGB32)
        painter = QPainter(image)
        frame.render(painter)
        painter.end()
        print("saving %s ..." % output_file)
        image.save(output_file)

    def wait_load(self, delay=0.01):
        # process app events until page loaded
        start_time = time.process_time()
        while not self._loaded:
            self.app.processEvents()
            time.sleep(delay)
            if (time.process_time() - start_time) > self.MAX_LOAD_TIME:
                raise FetchScreenshotTimeout("loading took too long: %s" % self.url())
        self._loaded = False

    def _loadFinished(self, result):
        self._loaded = True


class FetchScreenshotResult:
    def __init__(self, id, fn, exception):
        self.resource_id = id
        self.result_fn = fn
        self.exception = exception


def _abort_needed(resource):
    return not (resource.link and resource.screenshot_status in ["", "PENDING"])


def _fetch_screenshot(resource):
    if _abort_needed(resource):
        print("screenshot fetching aborted (early): %d" % resource.id)

    if resource.image:
        resource.screenshot_status = "DONE"
        resource.save()
        print("screenshot already present: %s" % resource.id)
        return FetchScreenshotResult(None, None, None)

    result_dir = tempfile.mkdtemp(prefix="oe_week-resource-screenshot-")
    result_fn = os.path.join(result_dir, "%s.png" % resource.uuid)

    try:
        s = Screenshot()
        s.capture(resource.link, result_fn)
        result = FetchScreenshotResult(resource.id, result_fn, None)
    except FetchScreenshotTimeout as ex:
        print("failed to fetch screenshot: %s" % ex)
        resource.screenshot_status = "PENDING"
        resource.save()

        try:
            os.remove(result_fn)
        except FileNotFoundError:
            pass
        try:
            os.rmdir(result_dir)
        except FileNotFoundError:
            pass

        result = FetchScreenshotResult(None, None, ex)

    return result


def fetch_screenshot_async(resource):
    async_task(
        _fetch_screenshot,
        resource,
        hook="web.screenshot_utils.process_fetch_screenshot_result",
    )


def process_fetch_screenshot_result(task):
    if task.result.exception is not None:
        # error while fetching
        return
    if task.result.resource_id is None:
        # screenshot was already present
        return

    resource_id = task.result.resource_id
    resource = Resource.objects.get(pk=resource_id)
    if _abort_needed(resource):
        print("screenshot fetching aborted (late): %d" % resource_id)
        return

    result_fn = task.result.result_fn
    print("screenshot fetched: %s" % result_fn)

    resource_image = ResourceImage()
    resource_image.image.save(
        "screenshot_{}.png".format(resource.pk), File(open(result_fn, "rb"))
    )
    resource_image.save()

    resource.image = resource_image
    resource.screenshot_status = "DONE"
    resource.save()

    result_dir = os.path.dirname(result_fn)
    os.remove(result_fn)
    os.rmdir(result_dir)
