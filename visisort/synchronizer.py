import threading
import sys

class Synchronizer(object):
    def __init__(self):
        self.synchronizees = set()
        self.lock = threading.Lock()
        self.in_sync = set()
        self.condition = threading.Condition(self.lock)

    def add(self, synchronizee):
##        print "{0!r}: adding {1!r}".format(self, synchronizee);sys.stdout.flush()
        self.lock.acquire()
        self.synchronizees.add(synchronizee)
        self.in_sync.add(synchronizee)
        self.lock.release()

    def done(self, synchronizee):
##        print "{0!r}: removing {1!r}".format(self, synchronizee);sys.stdout.flush()
        self.lock.acquire()
        self.synchronizees.discard(synchronizee)
        self.in_sync.discard(synchronizee)
        self.lock.release()

    def sync(self, synchronizee):
##        print "{0!r}: synchronizing {1!r}".format(self, synchronizee);sys.stdout.flush()
        self.condition.acquire()
        try:
            self.in_sync.discard(synchronizee)
##            print "{0!r}: in_sync = {1!r}".format(hash(self), repr(self.in_sync));sys.stdout.flush()
            if len(self.in_sync) == 0:
                self.synchronized()
                self.in_sync.update(self.synchronizees)
                self.condition.notifyAll()
            else:
                self.condition.wait()
        finally:
            self.condition.release()

    def synchronized(self):
        pass
