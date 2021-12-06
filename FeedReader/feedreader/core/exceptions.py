class NotASubclass(TypeError):

    def __init__(self, parameter, _type: type):
        super().__init__(f"'{type(parameter)}' must be a subclass of {_type.__name__}")


class NotAnInstance(TypeError):

    def __init__(self, parameter, _type: type):
        super().__init__(f"'{type(parameter)}' must be an instance of {_type.__name__}")


class NoAClass(TypeError):

    def __init__(self, parameter):
        super().__init__(f"'{type(parameter)}' is not a class")


class InvalidParameter(Exception):

    def __init__(self, parameter, message):
        super().__init__(f"'{parameter}' {message}")


class MissingParameter(Exception):

    def __init__(self, parameter, *missing_parameter_names):
        super().__init__(f"'{parameter}' must take {missing_parameter_names} parameters")
