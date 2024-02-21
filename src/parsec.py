from typing import Any, Type, NamedTuple, Callable, Iterable, Sequence, Self
from typing import cast, overload
from abc import ABC, abstractmethod
from functools import reduce

from src.utils import const, fst, snd

class State[I](ABC):
    @abstractmethod
    def update(self, val: I) -> Self:
        raise NotImplementedError()

class Input[I]:
    def __init__(self, _in: Sequence[I], _st: State[I], _cursor = 0):
        self.data = _in
        self.cursor = _cursor
        self.state = _st
    
    def get(self) -> tuple[I | None, 'Input[I]']:
        if self.cursor >= len(self.data): return None, self
        val = self.data[self.cursor]
        return val, Input(self.data, self.state.update(val),  self.cursor + 1)

class Okay[I, T](NamedTuple):
    value: T
    rest: Input[I]

class Fail(NamedTuple):
    message: list[str]

type Result[I, T] = Okay[I, T] | Fail

class Parser[I, T]:
    def __init__(self, _fn: Callable[[Input[I]], Result[I, T]]) -> None:
        self.parse = _fn
    
    def __call__(self, _in: Input[I]):
        return self.parse(_in)

    @classmethod
    def okay(cls, _val: T):
        return cls(lambda src: Okay(_val, src))

    @classmethod
    def fail(cls, _err: list[str] = []):
        return cls(const(Fail(_err)))

    def bind[T1](
        self: 'Parser[I, T]',
        _fn: Callable[[T], 'Parser[I, T1]']
    ) -> 'Parser[I, T1]':
        @Parser
        def parse(_in: Input[I]) -> Result[I, T1]:
            match self(_in):
                case Okay(value=val, rest=rest): return _fn(val)(rest)
                case Fail(message=err): return Fail(err)
        return parse
        
    def map[T1](self: 'Parser[I, T]', _fn: Callable[[T], T1]) -> 'Parser[I, T1]':
        return self.bind(lambda x: Parser.okay(_fn(x)))
    
    def error(self, _fn: Callable[[list[str]], list[str]]):
        @Parser
        def parse(_in: Input[I]) -> Result[I, T]:
            match self(_in):
                case Okay(value=val, rest=rest): return Okay(val, rest)
                case Fail(message=err): return Fail(_fn(err))
        return parse
    
    def apply[T1](
        self: 'Parser[I, Callable[[T], T1]]',
        _p: 'Parser[I, T]',
    ) -> 'Parser[I, T1]':
        return self.bind(_p.map)

    def alter_[T1](
        self,
        _p: 'Parser[I, T1]'
    ) -> 'Parser[I, T | T1]':
        @Parser
        def parse(_in: Input[I]) -> Result[I, T | T1]:
            match self(_in):
                case Okay(value=val, rest=rest): return Okay(val, rest)
                case Fail(message=e1):
                    match _p(_in):
                        case Okay(value=val, rest=rest): return Okay(val, rest)
                        case Fail(message=e2): return Fail(e1 + e2)
        return parse

    def repeat(self, _n: int) -> 'Parser[I, list[T]]':
        if _n == 0: return Parser.okay([])
        return self.bind(lambda x: self.repeat(_n - 1).bind(lambda xs: Parser.okay([x, *xs])))
    
    def where(self, _cond: Callable[[T], bool], _err: str = 'InvalidValue'):
        return self.bind(lambda x: Parser.okay(x) if _cond(x) else Parser.fail([f'got `{x}` but {_err}']))

    def some(self):
        return self.bind(lambda x: self.many().bind(lambda xs: Parser.okay([x, *xs])))

    def many(self):
        @Parser
        def parse(_in: Input[I]) -> Result[I, list[T]]:
            results: list[T] = []
            cur_in = _in
            while True:
                match self(cur_in):
                    case Okay(value=val, rest=rest):
                        results.append(val)
                        cur_in = rest
                    case Fail(): return Okay(results, cur_in)
        return parse            

    @overload
    def str(self: 'Parser[I, list[str]]') -> 'Parser[I, str]': ...

    @overload
    def str(self: 'Parser[I, tuple[str, ...]]') -> 'Parser[I, str]': ...

    def str(self: 'Parser') -> 'Parser[I, str]':
        def _fn1(val: Iterable[str]) -> str:
            return ''.join(val)
        return self.map(_fn1)
    
    @overload
    def at[T1, T2](
        self: 'Parser[I, tuple[T1, T2]]',
        _index: int
    ) -> 'Parser[I, T1 | T2]': ...
    @overload
    def at[T1, T2, T3](
        self: 'Parser[I, tuple[T1, T2, T3]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3]': ...
    @overload
    def at[T1, T2, T3, T4](
        self: 'Parser[I, tuple[T1, T2, T3, T4]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4]': ...
    @overload
    def at[T1, T2, T3, T4, T5](
        self: 'Parser[I, tuple[T1, T2, T3, T4, T5]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4 | T5]': ...
    @overload
    def at[T1, T2, T3, T4, T5, T6](
        self: 'Parser[I, tuple[T1, T2, T3, T4, T5, T6]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4 | T5 | T6]': ...
    @overload
    def at[T1, T2, T3, T4, T5, T6, T7](
        self: 'Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7]': ...
    @overload
    def at[T1, T2, T3, T4, T5, T6, T7, T8](
        self: 'Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8]': ...
    @overload
    def at[T1, T2, T3, T4, T5, T6, T7, T8, T9](
        self: 'Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9]]',
        _index: int
    ) -> 'Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9]': ...

    def at(self: 'Parser[I, tuple]', _index: int) -> 'Parser[I, Any]':
        def _fn1(val: tuple):
            assert 0 <= _index < len(val), f'{_index=}, {val=}'
            return val[_index]
        return self.map(_fn1)
    
    def as_type[T1](self, tp: Type[T1]) -> 'Parser[I, T1]':
        return cast(Parser[I, tp], self)
    
    def maybe(self):
        return self.alter_(Parser.okay(None))
    
    def range(self, _ranges: Iterable[T]):
        return self.where(lambda v: v in _ranges, f'expected value in range `{list(_ranges)}`')

    def eq(self, _val: T):
        return self.where(lambda v: v == _val, f'expected `{_val}`')    
    
    def neq(self, _val: T):
        return self.where(lambda v: v != _val, f'not expected `{_val}`')
   
    def prefix(self, _p: 'Parser[I, Any]'):
        return pair(_p, self).map(snd)
    
    def suffix(self, _p: 'Parser[I, Any]'):
        return pair(self, _p).map(fst)

    def between(self, _left: 'Parser[I, Any]', _right: 'Parser[I, Any]'):
        return self.prefix(_left).suffix(_right)

    def ltrim(self, _p: 'Parser[I, Any]'):
        return self.prefix(_p.many())

    def rtrim(self, _p: 'Parser[I, Any]'):
        return self.suffix(_p.many())

    def trim(self, _p: 'Parser[I, Any]'):
        return self.ltrim(_p).rtrim(_p)

    def default[T1](self, _val: T1) -> 'Parser[I, T | T1]':
        return self.alter_(Parser.okay(_val))
     
    def sep_by(self, _sep: 'Parser[I, Any]'):
        remains = self.prefix(_sep).many()
        return self.bind(lambda x: remains.bind(lambda xs: Parser.okay([x, *xs])))

    def chainl1(self, _op: 'Parser[I, Callable[[T], Callable[[T], T]]]'):
        def rest(x: T) -> Parser[I, T]:
            return _op.bind(lambda op: self.bind(lambda y: rest(op(x)(y)))).alter_(Parser.okay(x))
        return self.bind(lambda x: rest(x))
    
    def chainr1(self, _op: 'Parser[I, Callable[[T], Callable[[T], T]]]'):
        scan = self.bind(lambda x: rest(x))
        def rest(x: T) -> Parser[I, T]:
            return _op.bind(lambda op: scan.bind(lambda y: rest(op(x)(y))))
        return scan


def alter[I, T1, T2](_p1: Parser[I, T1], _p2: Parser[I, T2]) -> Parser[I, T1 | T2]:
    return _p1.alter_(_p2)

def pair[I, T1, T2](_p1: Parser[I, T1], _p2: Parser[I, T2]) -> Parser[I, tuple[T1, T2]]:
    return _p1.bind(lambda v1: _p2.bind(lambda v2: Parser.okay((v1, v2))))

def sel[I, T](*_plist: Parser[I, T]) -> Parser[I, T]:
    return reduce(alter, _plist)

def seq[I, T](*_plist: Parser[I, T]) -> Parser[I, list[T]]:
    @Parser
    def parse(_in: Input[I]) -> Result[I, list[T]]:
        results: list[T] = []
        cur_in = _in
        for p in _plist:
            match p(cur_in):
                case Okay(value=val, rest=rest):
                    results.append(val)
                    cur_in = rest
                case Fail(message=err):
                    return Fail(err)
        return Okay(results, cur_in)
    return parse

@overload
def hsel[I, T1, T2](
    _p1: Parser[I, T1], _p2: Parser[I, T2]
) -> Parser[I, T1 | T2]: ...
    
@overload
def hsel[I, T1, T2, T3](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3]
) -> Parser[I, T1 | T2 | T3]: ...
    
@overload
def hsel[I, T1, T2, T3, T4](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4]
) -> Parser[I, T1 | T2 | T3 | T4]: ...
    
@overload
def hsel[I, T1, T2, T3, T4, T5](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5]
) -> Parser[I, T1 | T2 | T3 | T4 | T5]: ...
    
@overload
def hsel[I, T1, T2, T3, T4, T5, T6](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6]
) -> Parser[I, T1 | T2 | T3 | T4 | T5 | T6]: ...
    
@overload
def hsel[I, T1, T2, T3, T4, T5, T6, T7](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7]
) -> Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7]: ...
    
@overload
def hsel[I, T1, T2, T3, T4, T5, T6, T7, T8](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7], _p8: Parser[I, T8]
) -> Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8]: ...
    
@overload
def hsel[I, T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7], _p8: Parser[I, T8],
    _p9: Parser[I, T9]
) -> Parser[I, T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9]: ...

def hsel[I](
    _p1: Parser[I, Any], _p2: Parser[I, Any],
    _p3: Parser[I, Any] | None = None,
    _p4: Parser[I, Any] | None = None,
    _p5: Parser[I, Any] | None = None,
    _p6: Parser[I, Any] | None = None,
    _p7: Parser[I, Any] | None = None,
    _p8: Parser[I, Any] | None = None,
    _p9: Parser[I, Any] | None = None,
    *_ps: Parser[I, Any]
) -> Parser[I, Any]:
    plist: list[Parser[I, Any]] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps)))
    return sel(*plist)

@overload
def hseq[I, T1, T2](
    _p1: Parser[I, T1], _p2: Parser[I, T2]
) -> Parser[I, tuple[T1, T2]]: ...
    
@overload
def hseq[I, T1, T2, T3](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3]
) -> Parser[I, tuple[T1, T2, T3]]: ...
    
@overload
def hseq[I, T1, T2, T3, T4](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4]
) -> Parser[I, tuple[T1, T2, T3, T4]]: ...
    
@overload
def hseq[I, T1, T2, T3, T4, T5](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5]
) -> Parser[I, tuple[T1, T2, T3, T4, T5]]: ...
    
@overload
def hseq[I, T1, T2, T3, T4, T5, T6](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6]
) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6]]: ...

@overload
def hseq[I, T1, T2, T3, T4, T5, T6, T7](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7]
) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7]]: ...
    
@overload
def hseq[I, T1, T2, T3, T4, T5, T6, T7, T8](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7], _p8: Parser[I, T8]
) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8]]: ...
    
@overload
def hseq[I, T1, T2, T3, T4, T5, T6, T7, T8, T9](
    _p1: Parser[I, T1], _p2: Parser[I, T2],
    _p3: Parser[I, T3], _p4: Parser[I, T4],
    _p5: Parser[I, T5], _p6: Parser[I, T6],
    _p7: Parser[I, T7], _p8: Parser[I, T8],
    _p9: Parser[I, T9]
) -> Parser[I, tuple[T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...

def hseq[I](
    _p1: Parser[I, Any], _p2: Parser[I, Any],
    _p3: Parser[I, Any] | None = None,
    _p4: Parser[I, Any] | None = None,
    _p5: Parser[I, Any] | None = None,
    _p6: Parser[I, Any] | None = None,
    _p7: Parser[I, Any] | None = None,
    _p8: Parser[I, Any] | None = None,
    _p9: Parser[I, Any] | None = None,
    *_ps: Parser[I, Any]
):
    plist: list[Parser[I, Any]] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps)))
    return seq(*plist).map(tuple)