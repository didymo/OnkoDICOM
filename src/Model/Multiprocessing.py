import multiprocessing
import time
import sys

# def worker():
#     name = multiprocessing.current_process().name
#     print(name, 'Starting')
#     time.sleep(1)
#     print(name, 'Exiting')
#     return
#
# def my_service():
#     name = multiprocessing.current_process().name
#     print(name, 'Starting')
#     time.sleep(10)
#     print(name, 'Exiting')
#     return
#
#
# if __name__ == '__main__':
#     service = multiprocessing.Process(name='my_service', target=my_service)
#     worker_1 = multiprocessing.Process(name='worker 1', target=worker)
#     worker_2 = multiprocessing.Process(target=worker)
#
#     worker_1.start()
#     worker_2.start()
#     service.start()



def daemon():
    p = multiprocessing.current_process()
    print('Starting:', p.name, p.pid)
    sys.stdout.flush()
    time.sleep(2)
    print("Exiting:", p.name, p.pid)
    sys.stdout.flush()

def non_daemon():
    p = multiprocessing.current_process()
    print('Starting:', p.name, p.pid)
    sys.stdout.flush()
    print("Exiting:", p.name, p.pid)
    sys.stdout.flush()

if __name__ == '__main__':
    d = multiprocessing.Process(name='daemon', target=daemon)
    d.daemon = True

    n = multiprocessing.Process(name='non-daemon', target=non_daemon)
    n.daemon = False

    d.start()
    time.sleep(1)
    n.start()

    d.join()
    n.join()
