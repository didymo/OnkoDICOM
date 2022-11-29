import sys
from unittest import mock
from unittest.mock import Mock
import pytest

import pytest
from PySide6.QtCore import QThreadPool

from src.Model.Worker import Worker

class FakeClass:
    def func_result(self, result):
        pass

    def func_error(self, error):
        pass


# qtbot is a pytest fixture used to test PyQt5. Part of the pytest-qt plugin.
def test_worker_progress_callback(qtbot):
    """
    Testing for the progress_callback parameter being present in the called function when progress_callback=True
    """
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3, progress_callback=True)
    
    # This starts the Worker in the threadpool and then blocks the test from progressing until the finished signal is
    # emitted. qtbot is a pytest fixture used to test PyQt5.
    threadpool = QThreadPool()
    with qtbot.waitSignal(w.signals.finished) as blocker:
        threadpool.start(w)

    assert w.fn == func_to_test
    assert w.kwargs['progress_callback'] is not None
    func_to_test.assert_called_with("test", 3, progress_callback=w.kwargs['progress_callback'])


def test_worker_progress_callback_false(qtbot):
    """
    Testing for the progress_callback parameter not being present in the called function when progress_callback=False
    """
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3, progress_callback=False)

    threadpool = QThreadPool()
    with qtbot.waitSignal(w.signals.finished) as blocker:
        threadpool.start(w)

    assert w.fn == func_to_test
    assert 'progress_callback' not in w.kwargs
    func_to_test.assert_called_with("test", 3)


def test_worker_no_progress_callback(qtbot):
    """
    Testing for the progress_callback parameter not being present in the called function when no progress_callback
    """
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3)

    threadpool = QThreadPool()
    with qtbot.waitSignal(w.signals.finished) as blocker:
        threadpool.start(w)

    assert w.fn == func_to_test
    assert 'progress_callback' not in w.kwargs
    func_to_test.assert_called_with("test", 3)


def test_worker_result_signal(qtbot, monkeypatch):
    """
    Testing return value of worker's called function through result signal.
    """
    thing = FakeClass()
    thing.func_to_test = Mock(return_value=5, unsafe=True)
    w = Worker(thing.func_to_test, "test", 3)

    with mock.patch.object(FakeClass, 'func_result', wraps=thing.func_result) as mock_func_result:
        w.signals.result.connect(thing.func_result)
        threadpool = QThreadPool()
        with qtbot.waitSignal(w.signals.finished) as blocker:
            threadpool.start(w)

        thing.func_to_test.assert_called_with("test", 3)
        mock_func_result.assert_called_with(5)


@pytest.mark.skip(reason="This test works perfectly in a local environment and fails every time in CI")
@pytest.mark.qt_no_exception_capture
def test_worker_error_signal(qtbot):
    """
    Testing exception value of worker's called function through error signal.
    """

    thing = FakeClass()
    thing.func_to_test = Mock(side_effect=ValueError("Some Error"))

    w = Worker(thing.func_to_test, "test", 3)
    
    # from https://github.com/pytest-dev/pytest-qt/blob/master/tests/test_exceptions.py
    # PyQt 5.5+ will crash if there's no custom exception handler installed
    # wrapping storage of original excepthook and putting it back in case this would linger.
    old_excepthook = sys.excepthook
    sys.excepthook = lambda *args: None
    
    with mock.patch.object(FakeClass, 'func_error', wraps=thing.func_error):
        w.signals.error.connect(thing.func_error)
        threadpool = QThreadPool()
        with qtbot.waitSignal(w.signals.finished) as blocker:
            threadpool.start(w)

        kall = thing.func_error.call_args
        args, kwargs = kall

        thing.func_to_test.assert_called_with("test", 3)
        assert isinstance(args[0][1], ValueError)
    sys.excepthook = old_excepthook
