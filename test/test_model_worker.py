from time import sleep
from unittest.mock import Mock, patch

from PyQt5.QtCore import QThreadPool

from src.Model.Worker import Worker


def test_worker_progress_callback():
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3, progress_callback=True)
    threadpool = QThreadPool()
    threadpool.start(w)
    sleep(2)    # give necessary time for the new thread to spawn

    assert w.fn == func_to_test
    assert w.kwargs['progress_callback'] is not None
    func_to_test.assert_called_with("test", 3, progress_callback=w.kwargs['progress_callback'])


def test_worker_progress_callback_false():
    threadpool = QThreadPool()
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3, progress_callback=False)
    threadpool.start(w)
    sleep(2)    # give necessary time for the new thread to spawn

    assert w.fn == func_to_test
    assert 'progress_callback' not in w.kwargs
    func_to_test.assert_called_with("test", 3)


def test_worker_no_progress_callback():
    threadpool = QThreadPool()
    func_to_test = Mock()
    w = Worker(func_to_test, "test", 3)
    threadpool.start(w)
    sleep(2)    # give necessary time for the new thread to spawn

    assert w.fn == func_to_test
    assert 'progress_callback' not in w.kwargs
    func_to_test.assert_called_with("test", 3)
