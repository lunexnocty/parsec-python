from dataclasses import dataclass
from functools import reduce
from typing import Any, Callable, Iterable, Unpack, cast, overload

from parsec.context import Context as _Context
from parsec.error import AlterError as _AlterError
from parsec.error import EOSError as _EOSError
from parsec.error import Expected as _Expected
from parsec.error import ParseErr as _ParseErr
from parsec.error import UnExpected as _UnExpected


@dataclass
class Okay[R]:
    value: R


@dataclass
class Fail:
    error: _ParseErr


@dataclass
class Result[I, R]:
    context: _Context[I]
    outcome: Okay[R] | Fail
    consumed: int

    @classmethod
    def okay(cls, ctx: _Context[I], value: R, consumed: int) -> 'Result[I, R]':
        return cls(ctx, Okay(value), consumed)

    @classmethod
    def fail(cls, ctx: _Context[I], error: _ParseErr, consumed: int) -> 'Result[I, R]':
        return cls(ctx, Fail(error), consumed)


class Parser[I, R]:
    """Monadic parser combinator.

    A parser that can be combined using monadic, functor, and applicative interfaces to build complex parsers.
    """

    def __init__(self, fn: Callable[[_Context[I]], Result[I, R]] | None = None) -> None:
        self._fn = fn

    def define(self, p: 'Parser[I, R]') -> None:
        """
        Lazily define this parser as another parser (for recursion).

        Args:
            p (Parser[I, R]): The parser to define as.

        Returns:
            None

        Example:
            >>> p1.define(p2)
        """
        self._fn: Callable[[_Context[I]], Result[I, R]] | None = lambda ctx: p.run(ctx)

    def run(self, ctx: _Context[I]) -> Result[I, R]:
        """
        Execute the parser on the given context.

        Args:
            ctx (_Context[I]): The parsing context.

        Returns:
            Result[I, R]: The parse result.

        Example:
            >>> p.run(ctx)
        """
        if self._fn is None:
            raise RuntimeError('UnDefined Parser')
        return self._fn(ctx)

    def __rshift__[S](self, fn: Callable[[R], 'Parser[I, S]']) -> 'Parser[I, S]':
        """
        Monadic bind operator (`>>`).

        Sequences two parsers, passing the result of the first parser to a function that returns the next parser.
        Enables dependent parsing where the output of the first parser determines the subsequent parser.

        Args:
            fn (Callable[[R], Parser[I, S]]): Function producing the next parser, given the result of the first.

        Returns:
            Parser[I, S]: Sequenced parser dependent on the previous parser's result.

        Example:
            >>> p1: Parser[I, R]
            >>> def next_parser(x: R) -> Parser[I, S]: ...
            >>> p: Parser[I, S] = p1 >> next_parser
        """
        return self.bind(fn)

    def __or__[S](self, p: 'Parser[I, S]') -> 'Parser[I, R | S]':
        """
        Prioritized alternative operator (`|`).

        Creates a new parser that first attempts to apply the first parser.
        If the first parser succeeds, its result is returned.
        If the first parser fails, the second parser is attempted from the original input position.
        Backtrace occurs if the first parser experienced a consuming failure.

        The first successful parse result is returned.

        Args:
            p (Parser[I, S]): The parser to try if the the first parser fails.

        Returns:
            Parser[I, R | S]: Prioritized alternative parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, R | S] = p1 | p2
        """
        return self.otherwise(p)

    def __truediv__[S](self, p: 'Parser[I, S]') -> 'Parser[I, R | S]':
        """
        Fast alternative operator (`/`).

        Attempts this parser; if it fails without consuming input, applies the alternative parser.
        No backtracking occurs if input was consumed.

        Args:
            p (Parser[I, S]): The parser to try if this parser fails without input consumption.

        Returns:
            Parser[I, R | S]: Fast alternative parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, R | S] = p1 / p2
        """
        return self.fast_otherwise(p)

    @overload
    def __and__[S, *TS](
        self: 'Parser[I, tuple[Unpack[TS]]]', p: 'Parser[I, S]'
    ) -> 'Parser[I, tuple[Unpack[TS], S]]': ...

    @overload
    def __and__[S](self, p: 'Parser[I, S]') -> 'Parser[I, tuple[R, S]]': ...

    def __and__[S, *TS](self, p: 'Parser[I, S]') -> 'Parser[I, Any]':
        """
        Sequencing (product) operator (`&`).

        Applies two parsers in sequence, producing a tuple of their results.
        Flattens tuple if the first result is a tuple (left-associative chaining).

        Args:
            p (Parser[I, S]): Parser to apply after this parser.

        Returns:
            Parser[I, tuple[R, S]]: Sequenced parser with tupled result.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, tuple[R, S]] = p1 & p2
        """

        def _flat_(t: tuple[Any, Any]) -> tuple[Any, ...]:
            if isinstance(t[0], tuple):
                return (*cast(tuple[Any, ...], t[0]), t[1])
            return t

        return self.pair(p).map(_flat_)

    def __lshift__[S](self, fn: Callable[['Parser[I, R]'], 'Parser[I, S]']) -> 'Parser[I, S]':
        """
        Parser transformation operator (`<<`).

        Applies a transformation function to this parser.

        Args:
            fn (Callable[[Parser[I, R]], Parser[I, S]]): Transformation function.

        Returns:
            Parser[I, S]: Parser resulting from transformation.

        Example:
            >>> def decorate(p: Parser[I, R]) -> Parser[I, S]: ...
            >>> p1: Parser[I, R]
            >>> p: Parser[I, S] = p1 << decorate
        """
        return fn(self)

    def __matmul__[S](self, fn: Callable[[R], S]) -> 'Parser[I, S]':
        """
        Functor mapping operator (`@`).

        Applies a function to the result of the parser.

        Args:
            fn (Callable[[R], S]): Function to map over the parser's result.

        Returns:
            Parser[I, S]: Parser with mapped result.

        Example:
            >>> p1: Parser[I, R]
            >>> def f(x: R) -> S: ...
            >>> p: Parser[I, S] = p1 @ f
        """
        return self.map(fn)

    def __invert__(self):
        return self.absent()

    @classmethod
    def okay(cls, value: R) -> 'Parser[I, R]':
        """
        Lifts a value into a parser that always succeeds without consuming input.

        Args:
            value (R): Value to be returned by the parser.

        Returns:
            Parser[I, R]: Parser that always succeeds with the given value.

        Example:
            >>> Parser.okay(42)
        """
        return cls(lambda ctx: Result[I, R].okay(ctx, value, 0))

    @classmethod
    def fail(cls, error: _ParseErr) -> 'Parser[I, R]':
        """
        Creates a parser that always fails with the specified error, consuming no input.

        Args:
            error (_ParseErr): Error to return.

        Returns:
            Parser[I, R]: Parser that always fails.

        Example:
            >>> Parser.fail(_ParseErr(...))
        """
        return cls(lambda ctx: Result[I, R].fail(ctx, error, 0))

    def bind[S](self, fn: Callable[[R], 'Parser[I, S]']) -> 'Parser[I, S]':
        """
        Monadic bind.

        Runs the parser, and if it succeeds, feeds the result into a function to produce the next parser.

        Args:
            fn (Callable[[R], Parser[I, S]]): Function producing the next parser.

        Returns:
            Parser[I, S]: Parser sequencing dependent computations.

        Example:
            >>> p1: Parser[I, R]
            >>> def f(x: R) -> Parser[I, S]: ...
            >>> p: Parser[I, S] = p1.bind(f)
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, S]:
            r1 = self.run(ctx)
            match r1.outcome:
                case Okay(value=v):
                    r2 = fn(v).run(r1.context)
                    r2.consumed += r1.consumed
                    return r2
                case Fail(error=e):
                    return Result[I, S].fail(r1.context, e, r1.consumed)

        return parse

    def map[S](self, fn: Callable[[R], S]) -> 'Parser[I, S]':
        """
        Functor map.

        Applies a function to the result of the parser if it succeeds.

        Args:
            fn (Callable[[R], S]): Function to apply to the parser result.

        Returns:
            Parser[I, S]: Parser with mapped result.

        Example:
            >>> p1: Parser[I, R]
            >>> def f(x: R) -> S: ...
            >>> p: Parser[I, S] = p1.map(f)
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, S]:
            r = self.run(ctx)
            match r.outcome:
                case Okay(value=v):
                    return Result[I, S].okay(r.context, fn(v), r.consumed)
                case Fail(error=e):
                    return Result[I, S].fail(r.context, e, r.consumed)

        return parse

    def apply[S](self, pfn: 'Parser[I, Callable[[R], S]]') -> 'Parser[I, S]':
        """
        Applicative apply.

        Applies a parser yielding a function to the result of this parser.

        Args:
            pfn (Parser[I, Callable[[R], S]]): Parser producing a function.

        Returns:
            Parser[I, S]: Parser applying the function to this parser's result.

        Example:
            >>> pf: Parser[I, Callable[[R], S]]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, S] = p1.apply(pf)
        """
        return pfn.bind(self.map)

    def alter(self, p: 'Parser[I, R]') -> 'Parser[I, R]':
        """
        Backtracking alternative.

        Tries this parser; if it fails, backtracks input and tries the alternative parser.
        Combines errors from both alternatives if both fail.

        Args:
            p (Parser[I, R]): Alternative parser.

        Returns:
            Parser[I, R]: Parser representing the choice.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, R]
            >>> p: Parser[I, R] = p1.alter(p2)
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, R]:
            r1 = self.run(ctx)
            if isinstance(r1.outcome, Okay):
                return r1
            ctx = r1.context.backtrack(r1.consumed, ctx.state) if r1.consumed else r1.context
            r2 = p.run(ctx)
            if isinstance(r2.outcome, Okay):
                return r2
            alt_err = _AlterError([r1.outcome.error, r2.outcome.error])
            return Result[I, R].fail(r2.context, alt_err.join(), r2.consumed)

        return parse

    def fast_alter(self, p: 'Parser[I, R]') -> 'Parser[I, R]':
        """
        Non-consuming fast alternative.

        Tries this parser; if it fails without consuming input, tries the alternative parser.
        Does not backtrack if input was consumed.

        Args:
            p (Parser[I, R]): Alternative parser.

        Returns:
            Parser[I, R]: Fast alternative parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, R]
            >>> p: Parser[I, R] = p1.fast_alter(p2)
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, R]:
            r1 = self.run(ctx)
            if r1.consumed > 0 or isinstance(r1.outcome, Okay):
                return r1
            r2 = p.run(r1.context)
            if isinstance(r2.outcome, Okay):
                return r2
            alt_err = _AlterError([r1.outcome.error, r2.outcome.error])
            return Result[I, R].fail(r2.context, alt_err.join(), r2.consumed)

        return parse

    def pair[S](self, p: 'Parser[I, S]') -> 'Parser[I, tuple[R, S]]':
        """
        Sequentially applies two parsers, returning results as a tuple.

        Args:
            p (Parser[I, S]): Parser to apply after this parser.

        Returns:
            Parser[I, tuple[R, S]]: Parser producing a tuple of results.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, tuple[R, S]] = p1.pair(p2)
        """
        return p.apply(self.map(lambda x: lambda y: (x, y)))

    def otherwise[S](self, p: 'Parser[I, S]') -> 'Parser[I, R | S]':
        """
        Prioritized alternative.

        Tries this parser; on failure, tries the alternative parser from the original input position.

        Args:
            p (Parser[I, S]): Alternative parser.

        Returns:
            Parser[I, R | S]: Alternative parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, R | S] = p1.otherwise(p2)
        """
        p1 = self.as_type(type[R | S])
        p2 = p.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.alter(p2))

    def fast_otherwise[S](self, p: 'Parser[I, S]') -> 'Parser[I, R | S]':
        """
        Fast prioritized alternative.

        Tries this parser; if it fails without consuming input, tries the alternative parser.

        Args:
            p (Parser[I, S]): Alternative parser.

        Returns:
            Parser[I, R | S]: Fast alternative parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p2: Parser[I, S]
            >>> p: Parser[I, R | S] = p1.fast_otherwise(p2)
        """
        p1 = self.as_type(type[R | S])
        p2 = p.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.fast_alter(p2))

    def maybe(self) -> 'Parser[I, R | None]':
        """
        Optional parser combinator.

        Attempts to apply the parser; if it fails, returns None without consuming input.

        Returns:
            Parser[I, R | None]: Parser that yields the result or None.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R | None] = p1.maybe()
        """
        return self.default(None)

    def default[S](self, value: S) -> 'Parser[I, R | S]':
        """
        Default value combinator.

        Attempts the parser; if it fails, returns the specified default value.

        Args:
            value (S): Value to return on failure.

        Returns:
            Parser[I, R | S]: Parser yielding original or default value.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R | S] = p1.default(0)
        """
        return self.otherwise(Parser[I, R | S].okay(value))

    def prefix(self, _prefix: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Prefix combinator.

        Applies the prefix parser, discards its result, then applies this parser.

        Args:
            _prefix (Parser[I, Any]): Parser whose result is ignored.

        Returns:
            Parser[I, R]: Parser ignoring the prefix.

        Example:
            >>> ws: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.prefix(ws)
        """
        return self.apply(_prefix.map(lambda x: lambda y: y))

    def suffix(self, _suffix: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Suffix combinator.

        Applies this parser, then the suffix parser, discarding the suffix result.

        Args:
            _suffix (Parser[I, Any]): Parser whose result is ignored.

        Returns:
            Parser[I, R]: Parser ignoring the suffix.

        Example:
            >>> ws: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.suffix(ws)
        """
        return _suffix.apply(self.map(lambda x: lambda y: x))

    def between(self, _prefix: 'Parser[I, Any]', _suffix: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Between combinator.

        Applies the prefix parser, then this parser, then the suffix parser, discarding prefix and suffix results.

        Args:
            _prefix (Parser[I, Any]): Prefix parser.
            _suffix (Parser[I, Any]): Suffix parser.

        Returns:
            Parser[I, R]: Parser yielding only the result of this parser.

        Example:
            >>> lparen: Parser[I, Any]
            >>> rparen: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.between(lparen, rparen)
        """
        return self.prefix(_prefix).suffix(_suffix)

    def ltrim(self, ignore: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Left trim combinator.

        Consumes zero or more occurrences of the ignore parser before applying this parser.

        Args:
            ignore (Parser[I, Any]): Parser to ignore.

        Returns:
            Parser[I, R]: Parser with leading ignored input removed.

        Example:
            >>> ws: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.ltrim(ws)
        """
        return self.prefix(ignore.many())

    def rtrim(self, ignore: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Right trim combinator.

        Applies this parser, then consumes zero or more occurrences of the ignore parser, discarding results.

        Args:
            ignore (Parser[I, Any]): Parser to ignore.

        Returns:
            Parser[I, R]: Parser with trailing ignored input removed.

        Example:
            >>> ws: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.rtrim(ws)
        """
        return self.suffix(ignore.many())

    def trim(self, ignore: 'Parser[I, Any]') -> 'Parser[I, R]':
        """
        Trim combinator.

        Applies left and right trim using the ignore parser.

        Args:
            ignore (Parser[I, Any]): Parser to ignore.

        Returns:
            Parser[I, R]: Parser with leading and trailing ignored input removed.

        Example:
            >>> ws: Parser[I, Any]
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.trim(ws)
        """
        return self.ltrim(ignore).rtrim(ignore)

    def absent(self) -> 'Parser[I, None]':
        @Parser
        def parse(ctx: _Context[I]) -> Result[I, None]:
            r = self.run(ctx)
            ctx = r.context.backtrack(r.consumed, ctx.state) if r.consumed else r.context
            match r.outcome:
                case Okay(value=v):
                    return Result[I, None].fail(ctx, _UnExpected(repr(v), ctx.state.format()), 0)
                case Fail():
                    return Result[I, None].okay(ctx, None, 0)

        return parse

    def sep_by(self, sep: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        """
        Separated-by combinator.

        Parses zero or more occurrences of this parser, separated by the sep parser.

        Args:
            sep (Parser[I, Any]): Separator parser.

        Returns:
            Parser[I, list[R]]: Parser yielding a list of results.

        Example:
            >>> comma: Parser[I, Any]
            >>> num: Parser[I, R]
            >>> p: Parser[I, list[R]] = num.sep_by(comma)
        """
        remains = self.prefix(sep).many()
        return remains.apply(self.map(lambda x: lambda xs: [x, *xs]))

    def end_by(self, sep: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        """
        End-by combinator.

        Parses zero or more occurrences of this parser, each followed by the sep parser.

        Args:
            sep (Parser[I, Any]): Separator parser.

        Returns:
            Parser[I, list[R]]: Parser yielding a list of results.

        Example:
            >>> semi: Parser[I, Any]
            >>> stmt: Parser[I, R]
            >>> p: Parser[I, list[R]] = stmt.end_by(semi)
        """
        return self.suffix(sep).many()

    def many_till(self, end: 'Parser[I, Any]') -> 'Parser[I, list[R]]':
        """
        Many-till combinator.

        Parses zero or more occurrences of this parser until the end parser succeeds.

        Args:
            end (Parser[I, Any]): End parser.

        Returns:
            Parser[I, list[R]]: Parser yielding a list of results.

        Example:
            >>> stop: Parser[I, Any]
            >>> item: Parser[I, R]
            >>> p: Parser[I, list[R]] = item.many_till(stop)
        """
        return self.many().suffix(end)

    def repeat(self, n: int) -> 'Parser[I, list[R]]':
        """
        Repeat combinator.

        Applies the parser exactly n times, collecting results in a list.

        Args:
            n (int): Number of times to apply the parser.

        Returns:
            Parser[I, list[R]]: Parser yielding a list of n results.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, list[R]] = p1.repeat(3)
        """
        if n == 0:
            return Parser[I, list[R]].okay([])
        return self.repeat(n - 1).apply(self.map(lambda x: lambda xs: [x, *xs]))

    def where(self, fn: Callable[[R], bool]) -> 'Parser[I, R]':
        """
        Predicate filter combinator.

        Applies the parser and succeeds only if the result satisfies the predicate.

        Args:
            fn (Callable[[R], bool]): Predicate to test the result.

        Returns:
            Parser[I, R]: Parser that fails if predicate is not satisfied.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.where(lambda x: x > 0)
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, R]:
            r = self.run(ctx)
            if isinstance(r.outcome, Fail):
                return r
            if fn(r.outcome.value):
                return r
            return Result[I, R].fail(
                r.context, _UnExpected(repr(r.outcome.value), r.context.state.format()), r.consumed
            )

        return parse

    def eq(self, value: R) -> 'Parser[I, R]':
        """
        Equality filter combinator.

        Parses and succeeds only if the result equals the specified value.

        Args:
            value (R): _Expected value.

        Returns:
            Parser[I, R]: Parser filtered by equality.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.eq(5)
        """
        return self.where(lambda v: v == value)

    def neq(self, value: R) -> 'Parser[I, R]':
        """
        Inequality filter combinator.

        Parses and succeeds only if the result does not equal the specified value.

        Args:
            value (R): Value to reject.

        Returns:
            Parser[I, R]: Parser filtered by inequality.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.neq(0)
        """
        return self.where(lambda v: v != value)

    def range(self, ranges: Iterable[R]) -> 'Parser[I, R]':
        """
        Range membership filter combinator.

        Parses and succeeds only if the result is in the specified range.

        Args:
            ranges (Iterable[R]): Acceptable values.

        Returns:
            Parser[I, R]: Parser filtered by range.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.range(range(10))
        """
        return self.where(lambda v: v in ranges)

    def some(self) -> 'Parser[I, list[R]]':
        """
        One-or-more combinator.

        Parses one or more occurrences of this parser, collecting results in a list.

        Returns:
            Parser[I, list[R]]: Parser yielding a non-empty list of results.

        Example:
            >>> digit: Parser[I, R]
            >>> p: Parser[I, list[R]] = digit.some()
        """
        return self.bind(lambda x: self.many().map(lambda xs: [x, *xs]))

    def many(self) -> 'Parser[I, list[R]]':
        """
        Zero-or-more combinator.

        Parses zero or more occurrences of this parser, collecting results in a list.

        Returns:
            Parser[I, list[R]]: Parser yielding a list of results.

        Example:
            >>> digit: Parser[I, R]
            >>> p: Parser[I, list[R]] = digit.many()
        """
        return self.some().alter(Parser[I, list[R]].okay([]))

    def chainl1(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]') -> 'Parser[I, R]':
        """
        Left-associative chain combinator (non-empty).

        Parses one or more occurrences separated by an operator parser, combining results left-associatively.

        Args:
            op (Parser[I, Callable[[R], Callable[[R], R]]]): Operator parser.

        Returns:
            Parser[I, R]: Parser yielding the combined result.

        Example:
            >>> plus: Parser[I, Callable[[int], Callable[[int], int]]]
            >>> num: Parser[I, int]
            >>> p: Parser[I, int] = num.chainl1(plus)
        """

        def rest(x: R) -> Parser[I, R]:
            return op.bind(lambda f: self.bind(lambda y: rest(f(x)(y)))).alter(Parser[I, R].okay(x))

        scan = self.bind(lambda x: rest(x))
        return scan

    def chainr1(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]') -> 'Parser[I, R]':
        """
        Right-associative chain combinator (non-empty).

        Parses one or more occurrences separated by an operator parser, combining results right-associatively.

        Args:
            op (Parser[I, Callable[[R], Callable[[R], R]]]): Operator parser.

        Returns:
            Parser[I, R]: Parser yielding the combined result.

        Example:
            >>> power: Parser[I, Callable[[int], Callable[[int], int]]]
            >>> num: Parser[I, int]
            >>> p: Parser[I, int] = num.chainr1(power)
        """

        def scan() -> Parser[I, R]:
            return self.bind(lambda x: op.bind(lambda f: scan().map(lambda y: f(x)(y))).alter(Parser[I, R].okay(x)))

        return scan()

    def chainl(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]', initial: R) -> 'Parser[I, R]':
        """
        Left-associative chain combinator with initial value.

        Parses zero or more occurrences separated by an operator parser, combining results left-associatively, starting from the initial value.

        Args:
            op (Parser[I, Callable[[R], Callable[[R], R]]]): Operator parser.
            initial (R): Initial value.

        Returns:
            Parser[I, R]: Parser yielding the combined result.

        Example:
            >>> plus: Parser[I, Callable[[int], Callable[[int], int]]]
            >>> num: Parser[I, int]
            >>> p: Parser[I, int] = num.chainl(plus, 0)
        """
        return self.chainl1(op).alter(Parser[I, R].okay(initial))

    def chainr(self, op: 'Parser[I, Callable[[R], Callable[[R], R]]]', initial: R) -> 'Parser[I, R]':
        """
        Right-associative chain combinator with initial value.

        Parses zero or more occurrences separated by an operator parser, combining results right-associatively, starting from the initial value.

        Args:
            op (Parser[I, Callable[[R], Callable[[R], R]]]): Operator parser.
            initial (R): Initial value.

        Returns:
            Parser[I, R]: Parser yielding the combined result.

        Example:
            >>> power: Parser[I, Callable[[int], Callable[[int], int]]]
            >>> num: Parser[I, int]
            >>> p: Parser[I, int] = num.chainr(power, 1)
        """
        return self.chainr1(op).alter(Parser[I, R].okay(initial))

    def as_type[S](self, _: type[S]) -> 'Parser[I, S]':
        """
        Type cast combinator.

        Casts the parser to a different result type (no runtime conversion).

        Args:
            _ (type[S]): Target type.

        Returns:
            Parser[I, S]: Parser with casted result type.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, Any] = p1.as_type(Any)
        """
        return cast(Parser[I, S], self)

    def label(self, expected: str) -> 'Parser[I, R]':
        """
        Label combinator.

        Assigns a human-readable label to the parser for diagnostic messages on failure.

        Args:
            expected (str): _Expected description.

        Returns:
            Parser[I, R]: Labeled parser.

        Example:
            >>> p1: Parser[I, R]
            >>> p: Parser[I, R] = p1.label("integer")
        """

        @Parser
        def parse(ctx: _Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Okay):
                return ret
            return Result[I, R].fail(ret.context, _Expected(expected, [ret.outcome.error]), ret.consumed)

        return parse


@Parser
def item[I](ctx: _Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, _EOSError(ctx.state.format()), 0)
    v = ctx.stream.read().pop()
    return Result[I, I].okay(ctx.update(v), v, 1)


@Parser
def look[I](ctx: _Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, _EOSError(ctx.state.format()), 0)
    v = ctx.stream.peek().pop()
    return Result[I, I].okay(ctx, v, 0)


eos = item.absent()


def tokens[I](values: Iterable[I]) -> Parser[I, list[I]]:
    ps = [item.eq(v) for v in values]
    return reduce(lambda p1, p2: p1.pair(p2).map(lambda x: [*x[0], x[1]]), ps, Parser[I, list[I]].okay([]))
