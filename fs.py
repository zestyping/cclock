import os


class FileSystem:
    def __init__(self, root):
        # self.root is absolute and always starts with '/' unless it is empty
        self.root = ('/' + root.lstrip('/')).rstrip('/')

    def resolve(self, relpath):
        return self.root + '/' + relpath.strip('/')

    def open(self, relpath, mode='rb'):
        path = self.resolve(relpath)
        makeparent(path)
        return open(path, mode)

    def write(self, relpath, content):
        with self.open(relpath, 'wb') as file:
            file.write(content)

    def append(self, relpath, content):
        with self.open(relpath, 'ab') as file:
            file.write(content)

    def rename(self, relpath, newrelpath):
        path = self.resolve(relpath)
        newpath = self.resolve(newrelpath)
        os.rename(path, newpath)

    def destroy(self, relpath):
        """Removes a file or directory and all its descendants."""
        destroy(self.resolve(relpath))

    def isdir(self, relpath):
        return isdir(self.resolve(relpath))

    def isfile(self, relpath):
        return isfile(self.resolve(relpath))


def isdir(path):
    return mode(path) & 0x4000


def isfile(path):
    return mode(path) & 0x8000


def mode(path):
    try:
        return os.stat(path)[0]
    except:
        return 0


def makeparent(path):
    parts = path.strip('/').split('/')
    path = ''
    for part in parts[:-1]:
        path += '/' + part
        if isfile(path):
            os.remove(path)
        if not isdir(path):
            os.mkdir(path)


def destroy(path):
    if isfile(path):
        os.remove(path)
    if isdir(path):
        for file in os.listdir(path):
            destroy(path + '/' + file)
        os.rmdir(path)
