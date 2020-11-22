from unittest.mock import Mock

from PyQt5.QtCore import QThreadPool

from src.Model.Worker import Worker


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


def test_worker_result_signal(qtbot):
    """
    Testing return value of worker's called function through result signal.
    """
    func_to_test = Mock(return_value=5)
    func_result = Mock()

    w = Worker(func_to_test, "test", 3)
    w.signals.result.connect(func_result)

    threadpool = QThreadPool()
    with qtbot.waitSignal(w.signals.finished) as blocker:
        threadpool.start(w)

    func_to_test.assert_called_with("test", 3)
    func_result.assert_called_with(5)


def test_worker_error_signal(qtbot):
    """
    Testing return value of worker's called function through result signal.
    """
    func_to_test = Mock(side_effect=ValueError())
    func_error = Mock()

    w = Worker(func_to_test, "test", 3)
    w.signals.error.connect(func_error)

    threadpool = QThreadPool()
    with qtbot.waitSignal(w.signals.finished) as blocker:
        threadpool.start(w)

    func_to_test.assert_called_with("test", 3)
    assert isinstance(func_error.call_args.args[0][1], ValueError)
