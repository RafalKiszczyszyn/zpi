from abc import abstractmethod, ABC


class InterceptorBase(ABC):

    @abstractmethod
    def transform(self, content):
        pass


# Interceptor's implementations


class Interceptor(InterceptorBase):

    def transform(self, content):
        content += '-transformed'
        print(content)
        return content
