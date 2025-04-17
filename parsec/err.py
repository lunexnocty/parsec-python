
class ParseErr:
    def __init__(self, children: list['ParseErr'] | None = None):
        self.chindren = children or []

    def add(self, err: 'ParseErr'):
        self.chindren.append(err)
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        attrs = {k: v for k, v in self.__dict__.items() if v}
        return f'{cls_name}({", ".join(f"{k}={v}" for k, v in attrs.items())})'

class Expected[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value



class UnExpected[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value



class InvalidValue[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value

class EOSErr(ParseErr):
    def __init__(self):
        super().__init__()