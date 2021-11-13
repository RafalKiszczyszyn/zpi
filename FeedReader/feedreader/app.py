from feedreader import containers

if __name__ == '__main__':
    containers.wire()

    from feedreader.app import startup
    startup.startup()
