from wordnet.service import startup
from wordnet.nlp.containers import wire as wire_nlp
from wordnet.service.containers import wire as wire_service


def main():
    wire_nlp()
    wire_service()
    startup.startup()


if __name__ == '__main__':
    main()
