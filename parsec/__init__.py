from abc import ABC, abstractmethod
from typing import Callable, Any, cast, overload
from collections.abc import Iterable
from functools import reduce
from dataclasses import dataclass
from parsec.err import ParseErr, ValueError, Excepted, EOSError

class IState[I](ABC):
    @abstractmethod
    def update(self, item: I) -> 'IState[I]':
        raise NotImplementedError
    
    @abstractmethod
    def format(self) -> str:
        raise NotImplementedError

class IStream[I](ABC):

    @abstractmethod
    def tell(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def read(self, n: int = 1) -> list[I]:
        raise NotImplementedError

    @abstractmethod
    def peek(self, n: int = 1) -> list[I]:
        raise NotImplementedError

    @abstractmethod
    def seek(self, offset: int) -> 'IStream[I]':
        raise NotImplementedError

    @abstractmethod
    def eos(self) -> bool:
        raise NotImplementedError

@dataclass
class Context[I]:
    stream: IStream[I]
    state: IState[I]
    def backtrack(self, consumed: int, state: IState[I]):
        return Context(self.stream.seek(-consumed), state)

    def update(self, value: I):
        return Context(self.stream, self.state.update(value))

@dataclass
class Okay[R]:
    value: R

@dataclass
class Fail:
    error: list[ParseErr]
    def merge(self, other: list[ParseErr]) -> list[ParseErr]:
        return self.error + [err for err in other if err not in self.error]

@dataclass
class Result[I, R]:
    context: Context[I]
    outcome: Okay[R] | Fail
    consumed: int

    @classmethod
    def okay(cls, ctx: Context[I], value: R, consumed: int):
        return cls(ctx, Okay(value), consumed)
    
    @classmethod
    def fail(cls, ctx: Context[I], error: list[ParseErr], consumed: int):
        return cls(ctx, Fail(error), consumed)
    
    def merge(self, error: list[ParseErr], consumed: int) -> 'Result[I, R]':
        match self.outcome:
            case Okay() as okay:
                return Result.okay(self.context, okay.value, self.consumed + consumed)
            case Fail() as fail:
                return Result.fail(self.context, fail.merge(error), self.consumed + consumed)


class Parser[I, R]:
    def __init__(self,fn: Callable[[Context[I]], Result[I, R]]):
        self._fn = fn
    
    def run[T](self, ctx: Context[I]) -> Result[I, R]:
        return self._fn(ctx)

    @classmethod
    def okay(cls, value: R) -> 'Parser[I, R]':
        return cls(lambda ctx: Result.okay(ctx, value, 0))
    
    @classmethod
    def fail(cls, error: ParseErr) -> 'Parser[I, R]':
        return cls(lambda ctx: Result.fail(ctx, [error], 0))

    def bind[S](self, fn: Callable[[R], 'Parser[I, S]']) -> 'Parser[I, S]':
        def parse(ctx: Context[I]) -> Result[I, S]:
            ret = self.run(ctx)
            match ret.outcome:
                case Okay() as okay:
                    ret_ = fn(okay.value).run(ret.context)
                    return Result(ret_.context, ret_.outcome, ret.consumed + ret_.consumed)
                case Fail() as fail:
                    return Result.fail(ret.context, fail.error, ret.consumed)
        return Parser(parse)

    def map[S](self, fn: Callable[[R], S]) -> 'Parser[I, S]':
        return self.bind(lambda v: Parser.okay(fn(v)))
    
    def apply[S](self, parser: 'Parser[I, Callable[[R], S]]') -> 'Parser[I, S]':
        return parser.bind(self.map)
    
    def alter(self, parser: 'Parser[I, R]', backtrace: bool = True) -> 'Parser[I, R]':
        def parse(ctx: Context[I]):
            ret = self.run(ctx)
            match ret.outcome:
                case Okay() as okay:
                    return Result.okay(ret.context, okay.value, ret.consumed)
                case Fail() as fail:
                    if backtrace:
                        ctx = ret.context.backtrack(ret.consumed, ctx.state)
                        consumed = 0
                    else:
                        ctx = ret.context
                        consumed = ret.consumed
                    return parser.run(ctx).merge(fail.error, consumed)
        return Parser(parse)
    
    def pair[S](self, parser: 'Parser[I, S]') -> 'Parser[I, tuple[R, S]]':
        return self.bind(lambda x: parser.bind(lambda y: Parser.okay((x, y))))

    def or_else[S](self, parser: 'Parser[I, S]') -> 'Parser[I, R | S]':
        p1 = self.as_type((type[R | S]))
        p2 = parser.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.alter(p2))

    def maybe(self) -> 'Parser[I, R | None]':
        return self.default(None)
    
    def default[U](self, value: U) -> 'Parser[I, R | U]':
        return self.or_else(Parser.okay(value))

    def prefix(self, parser: 'Parser[I, Any]') -> 'Parser[I, R]':
        return parser.pair(self).map(lambda x: x[1])
    
    def suffix(self, parser: 'Parser[I, Any]') -> 'Parser[I, R]':
        return self.pair(parser).map(lambda x: x[0])
    
    def between(self, left: 'Parser[I, Any]', right: 'Parser[I, Any]') -> 'Parser[I, R]':
        return self.prefix(left).suffix(right)
    
    def ltrim(self, parser: 'Parser[I, Any]') -> 'Parser[I, R]':
        return self.prefix(parser.many())
    
    def rtrim(self, parser: 'Parser[I, Any]') -> 'Parser[I, R]':
        return self.suffix(parser.many())

    def trim(self, parser: 'Parser[I, Any]') -> 'Parser[I, R]':
        return self.ltrim(parser).rtrim(parser)
    
    def sep_by(self, sep: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        remains = self.prefix(sep).many()
        return self.bind(lambda x: remains.bind(lambda xs: Parser.okay([x, *xs])))
    
    def end_by(self, sep: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        return self.suffix(sep).many()
    
    def many_till(self, end: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        @Parser[I, list[R]]
        def parse(ctx: Context[I]) -> Result[I, list[R]]:
            return end.map(lambda _: []).alter(parse.apply(self.map(lambda x: lambda xs: [x, *xs]))).run(ctx)
        return parse

    def repeat(self, n: int) -> 'Parser[I, list[R]]':
        if n == 0:
            return Parser.okay([])
        return self.bind(lambda x: self.repeat(n - 1).bind(lambda xs: Parser.okay([x, *xs])))

    def where(self, fn: Callable[[R], bool]) -> 'Parser[I, R]':
        return self.bind(lambda v: Parser.okay(v) if fn(v) else Parser.fail(ValueError(v)))
    
    def eq(self, value: R) -> 'Parser[I, R]':
        return self.where(lambda v: v == value).label(f'{value}')
    
    def neq(self, value: R) -> 'Parser[I, R]':
        return self.where(lambda v: v != value)
    
    def range(self, ranges: Iterable[R]) -> 'Parser[I, R]':
        return self.where(lambda v: v in ranges)
    
    def some(self) -> 'Parser[I, list[R]]':
        return self.bind(lambda x: self.many().map(lambda xs: [x, *xs]))
    
    def many(self) -> 'Parser[I, list[R]]':
        return self.some().alter(Parser.okay([]))

    def chainl1(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]') -> 'Parser[I, R]':
        def rest(x: R):
            return op.bind(lambda f: self.bind(lambda y: rest(f(x)(y)))).alter(Parser.okay(x))
        return self.bind(lambda x: rest(x))
    
    def chainr1(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]') -> 'Parser[I, R]':        
        scan = self.bind(lambda x: rest(x))
        def rest(x: R):
            return op.bind(lambda f: scan.bind(lambda y: Parser.okay(f(x)(y)))).alter(Parser.okay(x))
        return scan

    def chainl(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]', initial: R) -> 'Parser[I, R]':
        return self.chainl1(op).alter(Parser.okay(initial))

    def chainr(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]', initial: R) -> 'Parser[I, R]':
        return self.chainr1(op).alter(Parser.okay(initial))
    
    def as_type[S](self, tp: type[S]) -> 'Parser[I, S]':
        return cast(Parser[I, S], self)
    
    def label(self, text: str) -> 'Parser[I, R]':
        @Parser
        def parse(ctx: Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            match ret.outcome:
                case Okay() as okay:
                    return Result.okay(ret.context, okay.value, ret.consumed)
                case Fail() as fail:
                    return Result.fail(ret.context, fail.merge([Excepted(text)]), ret.consumed)
        return parse

@Parser
def item[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result.fail(ctx, [EOSError()], 0)
    return Result.okay(ctx.update(ctx.stream.peek().pop()), ctx.stream.read().pop(), 1)

token = item.eq
def tokens[I](values: Iterable[I]) -> Parser[I, list[I]]:
    return seq(*map(token, values))

def sel[I, R](*parsers: Parser[I, R]) -> Parser[I, R]:
    return reduce(Parser.alter, parsers)

def seq[I, R](*parsers: Parser[I, R]) -> Parser[I, list[R]]:
    return reduce(lambda ps, p: ps.pair(p).map(lambda x: [*x[0], x[1]]), parsers, Parser.okay([]))

@overload
def hsel[I, R1, R2](
    _p1: Parser[I, R1], _p2: Parser[I, R2]
) -> Parser[I, R1 | R2]: ...
    
@overload
def hsel[I, R1, R2, R3](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3]
) -> Parser[I, R1 | R2 | R3]: ...
    
@overload
def hsel[I, R1, R2, R3, R4](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4]
) -> Parser[I, R1 | R2 | R3 | R4]: ...
    
@overload
def hsel[I, R1, R2, R3, R4, R5](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5]
) -> Parser[I, R1 | R2 | R3 | R4 | R5]: ...
    
@overload
def hsel[I, R1, R2, R3, R4, R5, R6](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6]
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6]: ...
    
@overload
def hsel[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7]
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7]: ...
    
@overload
def hsel[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7], _p8: Parser[I, R8]
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8]: ...
    
@overload
def hsel[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7], _p8: Parser[I, R8],
    _p9: Parser[I, R9]
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9]: ...

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
def hseq[I, R1, R2](
    _p1: Parser[I, R1], _p2: Parser[I, R2]
) -> Parser[I, tuple[R1, R2]]: ...
    
@overload
def hseq[I, R1, R2, R3](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3]
) -> Parser[I, tuple[R1, R2, R3]]: ...
    
@overload
def hseq[I, R1, R2, R3, R4](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4]
) -> Parser[I, tuple[R1, R2, R3, R4]]: ...
    
@overload
def hseq[I, R1, R2, R3, R4, R5](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5]
) -> Parser[I, tuple[R1, R2, R3, R4, R5]]: ...
    
@overload
def hseq[I, R1, R2, R3, R4, R5, R6](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6]
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6]]: ...

@overload
def hseq[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7]
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7]]: ...
    
@overload
def hseq[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7], _p8: Parser[I, R8]
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8]]: ...
    
@overload
def hseq[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: Parser[I, R1], _p2: Parser[I, R2],
    _p3: Parser[I, R3], _p4: Parser[I, R4],
    _p5: Parser[I, R5], _p6: Parser[I, R6],
    _p7: Parser[I, R7], _p8: Parser[I, R8],
    _p9: Parser[I, R9]
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8, R9]]: ...

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
