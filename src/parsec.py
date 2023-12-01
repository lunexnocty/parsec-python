
from typing import Self, Type, NamedTuple, Callable, Iterable
from typing import cast, overload
from functools import reduce

from src.utils import const

class Okay[T](NamedTuple):
    value: T
    rest: str

class Fail(NamedTuple):
    message: list[str]

type Result[T] = Okay[T] | Fail

type Skiped = None

class Parser[T]:
    def __init__(self, _fn: Callable[[str], Result[T]]) -> None:
        self.parse = _fn
    
    def __call__(self, _input: str):
        return self.parse(_input)

    @classmethod
    def okay(cls, _val: T):
        return cls(lambda src: Okay(_val, src))

    @classmethod
    def fail(cls):
        return cls(const(Fail([])))

    def bind[T1](
        self: 'Parser[T]',
        _fn: Callable[[T], 'Parser[T1]']
    ):
        @Parser
        def parse(_input: str) -> Result[T1]:
            match self(_input):
                case Okay(value=val, rest=rest): return _fn(val)(rest)
                case Fail(message=err): return Fail(err)
        return parse
        
    def map[T1](self: 'Parser[T]', _fn: Callable[[T], T1]):
        return self.bind(lambda x: Parser.okay(_fn(x)))
    
    def apply[T1](
        self: 'Parser[Callable[[T], T1]]',
        _p: 'Parser[T]',
    ):
        return self.bind(_p.map)

    def alter_[T1](
        self,
        _p: 'Parser[T1]'
    ):
        @Parser
        def parse(_input: str) -> Result[T | T1]:
            match self(_input):
                case Okay(value=val, rest=rest): return Okay(val, rest)
                case Fail(message=e1):
                    match _p(_input):
                        case Okay(value=val, rest=rest): return Okay(val, rest)
                        case Fail(message=e2): return Fail(e1 + e2)
        return parse

    def count(self, _n: int) -> 'Parser[list[T]]':
        if _n == 0: return Parser.okay([])
        return self.bind(lambda x: self.count(_n - 1).bind(lambda xs: Parser.okay([x, *xs])))
    
    def where(self, _cond: Callable[[T], bool]):
        return self.bind(lambda x: Parser.okay(x) if _cond(x) else Parser.fail())

    def some(self):
        return self.bind(lambda x: self.many().bind(lambda xs: Parser.okay([x, *xs])))

    def many(self):
        @Parser
        def parse(_input: str) -> Result[list[T]]:
            results: list[T] = []
            src = _input
            while True:
                match self(src):
                    case Okay(value=val, rest=rest):
                        results.append(val)
                        src = rest
                    case Fail(): return Okay(results, src)
        return parse            

    @overload
    def str(self: 'Parser[list[str]]') -> 'Parser[str]': ...

    @overload
    def str(self: 'Parser[tuple[str, ...]]') -> 'Parser[str]': ...

    def str(self: 'Parser') -> 'Parser[str]':
        def _fn1(val: Iterable[str]) -> str:
            return ''.join(val)
        return self.map(_fn1)
    
    def skip(self) -> 'Parser[Skiped]':
        return self.map(const(None))
    
    def at[*Ts](self: 'Parser[tuple[*Ts]]', _index: int):
        def _fn1(val: tuple[*Ts]):
            assert 0 <= _index < len(val), f'{_index=}, {val=}'
            return val[_index]
        return self.map(_fn1)
    
    def as_type[T1](self, tp: Type[T1]):
        return cast(Parser[tp], self)
    
    def maybe(self):
        return self.alter_(Parser.okay(None))
    
    def range(self, _ranges: Iterable[T]):
        return self.where(lambda v: v in _ranges)

    def eq(self, _val: T):
        return self.where(lambda v: v == _val)    
    
    def neq(self, _val: T):
        return self.where(lambda v: v != _val)
    
    def sep_by[T1](self, _sep: 'Parser[T1]'):
        remains = hseq(_sep, self).at(1).many().as_type(list[T])
        return pair(self, remains).map(lambda val: [val[0], *val[1]])

    def ignore[T1](self, _p: 'Parser[T1]'):
        return cast(Self, hseq(_p.many(), self).at(1))
    
    def chainl1(self, _op: 'Parser[Callable[[T], Callable[[T], T]]]'):
        def rest(x: T) -> Parser[T]:
            return _op.bind(lambda op: self.bind(lambda y: rest(op(x)(y)))).alter_(Parser.okay(x))
        return self.bind(lambda x: rest(x))
    
    def chainr1(self, _op: 'Parser[Callable[[T], Callable[[T], T]]]'):
        scan = self.bind(lambda x: rest(x))
        def rest(x: T) -> Parser[T]:
            return _op.bind(lambda op: scan.bind(lambda y: op(x)(y)))
        return scan


def alter[T1, T2](_p1: Parser[T1], _p2: Parser[T2]):
    return _p1.alter_(_p2)

def pair[T1, T2](_p1: Parser[T1], _p2: Parser[T2]):
    return _p1.bind(lambda v1: _p2.bind(lambda v2: Parser.okay((v1, v2))))

def sel[T](*_plist: Parser[T]):
    return reduce(alter, _plist)

def seq[T](*_plist: Parser[T]):
    @Parser
    def parse(_input: str) -> Result[list[T]]:
        results: list[T] = []
        src = _input
        for p in _plist:
            match p(src):
                case Okay(value=val, rest=rest):
                    results.append(val)
                    src = rest
                case Fail(message=err):
                    return Fail(err)
        return Okay(results, src)
    return parse

@overload
def hsel[T1, T2](
    _p1: Parser[T1], _p2: Parser[T2]
) -> Parser[T1 | T2]: ...
    
@overload
def hsel[T1, T2, T3](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3]
) -> Parser[T1 | T2 | T3]: ...
    
@overload
def hsel[T1, T2, T3, T4](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4]
) -> Parser[T1 | T2 | T3 | T4]: ...
    
@overload
def hsel[T1, T2, T3, T4, T5](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5]
) -> Parser[T1 | T2 | T3 | T4 | T5]: ...
    
@overload
def hsel[T1, T2, T3, T4, T5, T6](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6]
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6]: ...
    
@overload
def hsel[T1, T2, T3, T4, T5, T6, T7](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7]
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6 | T7]: ...
    
@overload
def hsel[T1, T2, T3, T4, T5, T6, T7, T8](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7], _p8: Parser[T8]
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8]: ...
    
@overload
def hsel[T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7], _p8: Parser[T8],
    _p9: Parser[T9]
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9]: ...

def hsel[T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3] | None = None,
    _p4: Parser[T4] | None = None,
    _p5: Parser[T5] | None = None,
    _p6: Parser[T6] | None = None,
    _p7: Parser[T7] | None = None,
    _p8: Parser[T8] | None = None,
    _p9: Parser[T9] | None = None
):
    plist: list[Parser] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9)))
    return sel(*plist)

@overload
def hseq[T1, T2](
    _p1: Parser[T1], _p2: Parser[T2]
) -> Parser[tuple[T1, T2]]: ...
    
@overload
def hseq[T1, T2, T3](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3]
) -> Parser[tuple[T1, T2, T3]]: ...
    
@overload
def hseq[T1, T2, T3, T4](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4]
) -> Parser[tuple[T1, T2, T3, T4]]: ...
    
@overload
def hseq[T1, T2, T3, T4, T5](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5]
) -> Parser[tuple[T1, T2, T3, T4, T5]]: ...
    
@overload
def hseq[T1, T2, T3, T4, T5, T6](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6]
) -> Parser[tuple[T1, T2, T3, T4, T5, T6]]: ...

@overload
def hseq[T1, T2, T3, T4, T5, T6, T7](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7]
) -> Parser[tuple[T1, T2, T3, T4, T5, T6, T7]]: ...
    
@overload
def hseq[T1, T2, T3, T4, T5, T6, T7, T8](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7], _p8: Parser[T8]
) -> Parser[tuple[T1, T2, T3, T4, T5, T6, T7, T8]]: ...
    
@overload
def hseq[T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3], _p4: Parser[T4],
    _p5: Parser[T5], _p6: Parser[T6],
    _p7: Parser[T7], _p8: Parser[T8],
    _p9: Parser[T9]
) -> Parser[tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...

def hseq[T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[T1], _p2: Parser[T2],
    _p3: Parser[T3] | None = None,
    _p4: Parser[T4] | None = None,
    _p5: Parser[T5] | None = None,
    _p6: Parser[T6] | None = None,
    _p7: Parser[T7] | None = None,
    _p8: Parser[T8] | None = None,
    _p9: Parser[T9] | None = None
):
    plist: list[Parser] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9)))
    return seq(*plist).map(tuple)