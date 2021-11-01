from feedreader import startup, containers

if __name__ == '__main__':
    containers.wire()
    startup.startup()
