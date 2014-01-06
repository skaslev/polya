####################################################################################################
#
# terms.py
#
# Authors:
# Jeremy Avigad
# Rob Lewis
#
# A Term is either an Atom or a AppTerm.
#
# An STerm is a scaled term, i.e. something of the form (c * t), where c is a Fraction and t
# is a Term. When terms are canonized, such a scalar is needed.
#
# Subclasses of Atom include:
#
#     One (the constant term 1)
#     Var
#     IVar (indexed variables, used to name subterms)
#     UVar (unification variables)
#
# An AppTerm consists of a function applied to a sequence of arguments. Subclasses of AppTerm
# include:
#
#     FuncTerm
#     AddTerm
#     MulTerm
#     AbsTerm
#     MinTerm  (max(x1, ..., xn) is represented by -min(-x1, ..., -xn))
#
# For all AppTerms other than AbsTerm and MulTerm, the arguments are STerms. The argument to abs(t)
# need only be a term, because the scalar can be brought outside. Each MulTerm is of the form
#
#  (t1^n1) * ... * (tk^nk)
#
# where each ti is a Term and each ni is an integer. When canonizing, scalars are collected and
# brought to the front, so each ti need only by a Term. Such a pair (t, n) is called a MulPair.
#
# This module defines Python syntax for entering Terms and STerms, and the methods for canonizing
# and printing them.
#
# This module also defines comparisons between Terms and / or STerms, of the form
#
#   term1 comp term2
#
# For sorting and testing equality, every Term (and Sterm) has an associated key. These keys should
# be used for all comparisons, because the built-in comparison operators are co-opted for
# constructing expressions. For example, use
#
#   term1.key == term2.key
#
# and similarly for STerms.
#
# TODO: would it be better to have one AppTerm, and put all the info into the function component?
# TODO: could have a generic canonization for AC operations
#
####################################################################################################


import fractions
import numbers


class Error(Exception):
    pass


class Contradiction(Exception):
    def __init__(self, msg):
        self.msg = msg


####################################################################################################
#
# For pretty printing
#
####################################################################################################


ATOM, SUM, PRODUCT = range(3)


def pretty_print_fraction(frac):
    if frac.denominator == 1:
        return ATOM, str(frac)
    else:
        return PRODUCT, str(frac)


####################################################################################################
#
# Term
#
####################################################################################################


class Term:

    def __init__(self):
        self.key = None
        self.__hash__ = None

    def pretty_print(self):
        """
        Returns a pair, (level, string). The string is a representation of the term. The level is
        one of ATOM, SUM, or PRODUCT, describing the form of the term. This is used, recursively,
        to decide when to add parentheses.
        """
        pass

    def canonize(self):
        """Puts the term in a canonical normal form. Always returns an STerm."""
        pass

    def __str__(self):
        return self.pretty_print()[1]

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        # case where self is an AddTerm is handled in that class
        if isinstance(other, numbers.Rational):
            return self + STerm(other, One())
        elif isinstance(other, STerm):
            return other + self
        elif isinstance(other, Term):
            if isinstance(other, AddTerm):
                return other + self
            elif self.key == other.key:
                return STerm(2, self)
            else:
                return AddTerm([STerm(1, self), STerm(1, other)])
        else:
            raise Error('Cannot add Term {0!s} to {1!s}'.format(self, other))

    def __radd__(self, other):
        return self + other

    def __mul__(self, other):
        # case where self is a MulTerm is handled in that class
        if isinstance(self, One):
            return other
        elif isinstance(other, numbers.Rational):
            return STerm(other, self)
        elif isinstance(other, Term):
            if isinstance(other, One):
                return self
            if isinstance(other, MulTerm):
                return other * self
            elif self.key == other.key:
                return MulPair(self, 2)
            else:
                return MulTerm([MulPair(self, 1), MulPair(other, 1)])
        elif isinstance(other, STerm):
            #todo: I added this, but I'm not sure that this is the desired behavior. Check w Jeremy
            return other * self
        else:
            raise Error('Cannot multiply Term {0!s} by {1!s}'.format(self, other))

    def __rmul__(self, other):
        return self * other

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + other * -1

    def __rsub__(self, other):
        return (-1) * self + other

    def __div__(self, other):
        if isinstance(other, int):
            return self * fractions.Fraction(1, other)
        return self * (other ** -1)

    def __rdiv__(self, other):
        return (self ** -1) * other

    def __truediv__(self, other):
        return self / other

    def __rtruediv__(self, other):
        return other * self ** (-1)

    def __pow__(self, n):
        # case where self is a MulTerm is handled in that class
        return MulTerm([MulPair(self, n)])

    def __abs__(self):
        return AbsTerm(self)

    def __lt__(self, other):
        return TermComparison(self, LT, other)

    def __le__(self, other):
        return TermComparison(self, LE, other)

    def __gt__(self, other):
        return TermComparison(self, GT, other)

    def __ge__(self, other):
        return TermComparison(self, GE, other)

    def __eq__(self, other):
        return TermComparison(self, EQ, other)

    def __ne__(self, other):
        return TermComparison(self, NE, other)


class Atom(Term):

    def __init__(self, name, key):
        Term.__init__(self)
        self.name = name
        self.key = key

    def pretty_print(self):
        return ATOM, self.name

    def canonize(self):
        return STerm(1, self)


class AppTerm(Term):

    def __init__(self, func_name, args, key):
        Term.__init__(self)
        self.func_name = func_name
        self.args = args
        self.key = key + tuple([a.key for a in args])


####################################################################################################
#
# Subclasses of Atom
#
####################################################################################################


class One(Atom):

    def __init__(self):
        Atom.__init__(self, '1', key=(10, 0))


class Var(Atom):

    def __init__(self, name):
        Atom.__init__(self, name, key=(20, name))


class IVar(Atom):

    def __init__(self, index):
        self.index = index
        Atom.__init__(self, 't' + str(index), key=(30, index))


class UVar(Atom):

    def __init__(self, index):
        self.index = index
        Atom.__init__(self, 'u' + str(index), key=(40, index))


def _str_to_list(s):
    if ',' in s:
        return [item.strip() for item in s.split(',')]
    elif ' ' in s:
        return [item.strip() for item in s.split()]
    else:
        return [s]


def Vars(name_str):
    """
    Create a list of variables

    Examples:
      x, y, z = Vars('x, y, z')
      a, b, c = Vars('a b c')
    """
    names = _str_to_list(name_str)
    if len(names) == 1:
        return Var(names[0])
    else:
        variables = ()
        for name in names:
            variables += (Var(name),)
        return variables


####################################################################################################
#
# Subclasses of FuncTerm
#
####################################################################################################


class AddTerm(AppTerm):

    def __init__(self, args):
        AppTerm.__init__(self, 'sum', args, key=(50, 'sum'))

    def pretty_print(self):
        arg_strings = [a.pretty_print()[1] for a in self.args]
        return SUM, ' + '.join(arg_strings)

    def canonize(self):
        cargs = [arg.canonize() for arg in self.args]
        new_addterm = reduce(lambda x, y: x + y, cargs, 0)    # remove duplicates
        new_args = sorted(new_addterm.args, key=lambda a: a.key)
        first_coeff = new_args[0].coeff
        new_args2 = [arg / first_coeff for arg in new_args]
        return STerm(first_coeff, AddTerm(new_args2))

    def __add__(self, other):
        args = list(self.args)
        # determine the list of STerms to add
        if isinstance(other, fractions.Rational):
            args2 = [STerm(other, One())] if other != 0 else []
        elif isinstance(other, AddTerm):
            args2 = other.args
        elif isinstance(other, Term):
            args2 = [STerm(1, other)]
        elif isinstance(other, STerm):
            if other.coeff == 0:
                args2 = []
            elif isinstance(other.term, AddTerm):
                args2 = [arg * other.coeff for arg in other.term.args]
            else:
                args2 = [other]
        else:
            raise Error('Cannot add AddTerm {0!s} and {1!s}'.format(self, other))
        # add each argument in args2 to args
        for b in args2:
            for a in args:
                if b.term.key == a.term.key:
                    args.remove(a)
                    if a.coeff != -b.coeff:
                        args.append(STerm(a.coeff + b.coeff, a.term))
                    break
            else:
                args.append(b)
        return AddTerm(args) if args else zero


class MulTerm(AppTerm):

    def __init__(self, args):
        AppTerm.__init__(self, 'prod', args, key=(60, 'prod'))

    def pretty_print(self):
        if len(self.args) == 1:
            return self.args[0].pretty_print()
        else:
            arg_strings = []
            for a in self.args:
                level, s = a.pretty_print()
                if level == SUM:
                    arg_strings.append('(' + s + ')')
                else:
                    arg_strings.append(s)
            return PRODUCT, ' * '.join(arg_strings)

    def canonize(self):
        cargs = [a.canonize() for a in self.args]
        scalar = reduce(lambda x, y: x * y, [a.coeff for a in cargs], 1)
        new_multerm = reduce(lambda x, y: x * y, [a.term for a in cargs], One())
        new_args = sorted(new_multerm.args, key=lambda a: a.key)
        return STerm(scalar, MulTerm(new_args))

    def __mul__(self, other):
        args = list(self.args)
        scalar = 1
        # determine the list of MulPairs to multiply, and possibly a scalar
        if isinstance(other, fractions.Rational):
            scalar = other
            args2 = []
        elif isinstance(other, One):
            args2 = []
        elif isinstance(other, MulTerm):
            args2 = other.args
        elif isinstance(other, Term):
            args2 = [MulPair(other, 1)]
        elif isinstance(other, STerm):
            scalar = other.coeff
            if isinstance(other.term, MulTerm):
                args2 = other.term.args
            else:
                args2 = [MulPair(other.term, 1)]
        else:
            raise Error('Cannot multiply MulTerm {0!s} by {1!s}'.format(self, other))
        # multiply args by each argument in args2
        for b in args2:
            for a in args:
                if b.term.key == a.term.key:
                    args.remove(a)
                    if a.exponent != -b.exponent:
                        args.append(MulPair(a.term, a.exponent + b.exponent))
                    break
            else:
                args.append(b)
        if scalar == 0:
            return zero
        else:
            result = MulTerm(args) if args else One()
            return result if scalar == 1 else STerm(scalar, result)

    def __pow__(self, n):
        return MulTerm([a ** n for a in self.args])


class AbsTerm(AppTerm):

    def __init__(self, arg):
        AppTerm.__init__(self, 'abs', [arg], key=(70, 'abs'))

    def pretty_print(self):
        return ATOM, 'abs({0})'.format(self.args[0].pretty_print()[1])

    def canonize(self):
        return abs(self.args[0].canonize())

    def __abs__(self):
        return self


# TODO: not implemented yet
# add binary min and max methods to Term, STerm, and MinTerm
# handling should be similar to AddTerm
class MinTerm(AppTerm):

    def __init__(self, args):
        AppTerm.__init__(self, 'min', args, key=(80, 'min'))


class FuncTerm(AppTerm):

    def __init__(self, func_name, args):
        AppTerm.__init__(self, func_name, args, key=(90, func_name))

    def pretty_print(self):
        return ATOM, '{0}({1})'.format(self.func_name,
                                       ', '.join([a.pretty_print()[1] for a in self.args]))

    def canonize(self):
        return STerm(1, FuncTerm(self.func_name, [a.canonize() for a in self.args]))


class Func():
    """
    User defined functions.

    Example:
      x, y, z = Vars('x, y, z')
      f = Func('f')
      print f(x, y, z)
    """

    def __init__(self, name, arity=None):
        self.name = name
        self.arity = arity

    def __call__(self, *args):
        if self.arity is not None and len(args) != self.arity:
            raise Error('Wrong number of arguments to {0!s}'.format(self.name))

        return FuncTerm(self.name, args)


####################################################################################################
#
# STerm
#
####################################################################################################


class STerm:

    def __init__(self, coeff, term):
        self.coeff = fractions.Fraction(coeff)
        if coeff != 0:
            self.term = term
        else:
            self.term = One()
        self.key = (term.key, coeff)
        self.__hash__ = None

    def pretty_print(self):
        if self.coeff == 0:
            return ATOM, '0'
        elif self.coeff == 1:
            return self.term.pretty_print()
        elif isinstance(self.term, One):
            return pretty_print_fraction(self.coeff)
        else:
            lc, sc = pretty_print_fraction(self.coeff)
            if lc != ATOM:
                sc = '({0})'.format(sc)
            lt, st = self.term.pretty_print()
            if lt == ATOM:
                return PRODUCT, '{0}*{1}'.format(sc, st)
            elif lt == SUM:
                return PRODUCT, '{0}*({1})'.format(sc, st)
            else:    # lt == PRODUCT
                return PRODUCT, '{0} * {1}'.format(sc, st)

    def canonize(self):
        t = self.term.canonize()
        return t * self.coeff

    def __str__(self):
        return self.pretty_print()[1]

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        if self.coeff == 0:
            return other
        elif isinstance(self.term, AddTerm):
            return self.coeff * self.term + other    # make first term an AddTerm
        elif isinstance(other, numbers.Rational):
            return self + STerm(other, One())
        elif isinstance(other, AddTerm):
            return other + self
        elif isinstance(other, Term):
            if self.term.key == other.key:
                return STerm(self.coeff + 1, self.term)
            else:
                return AddTerm([self, STerm(1, other)])
        elif isinstance(other, STerm):
            if other.coeff == 0:
                return self
            elif isinstance(other.term, AddTerm):
                return other.coeff * other.term + self
            else:
                if self.term.key == other.term.key:
                    if self.coeff + other.coeff == 0:
                        return zero
                    else:
                        return STerm(self.coeff + other.coeff, self.term)
                else:
                    return AddTerm([self, other])
        else:
            raise Error('Cannot add STerm')

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return self + (-1) * other

    def __rsub__(self, other):
        return other + (-1) * self

    def __mul__(self, other):
        if isinstance(other, numbers.Rational):
            return STerm(self.coeff * other, self.term)
        elif isinstance(other, Term):
            return STerm(self.coeff, self.term * other)
        elif isinstance(other, STerm):
            return STerm(self.coeff * other.coeff, self.term * other.term)

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        if isinstance(other, numbers.Rational):
            if other == 0:
                Error('Divide by 0')
            else:
                return STerm(self.coeff / other, self.term)
        elif isinstance(other, Term):
            return STerm(self.coeff, self.term / other)
        elif isinstance(other, STerm):
            if other.coeff == 0:
                Error('Divide by 0')
            else:
                return STerm(self.coeff / other.coeff, self.term / other.term)

    def __pow__(self, n):
        if not isinstance(n, (int, long)):
            Error('Non integer power')    # TODO: for now, we only handle integer powers
        else:
            return STerm(self.coeff ** n, self.term ** n)

    def __abs__(self):
        return STerm(abs(self.coeff), abs(self.term))

    def __lt__(self, other):
        return TermComparison(self, LT, other)

    def __le__(self, other):
        return TermComparison(self, LE, other)

    def __gt__(self, other):
        return TermComparison(self, GT, other)

    def __ge__(self, other):
        return TermComparison(self, GE, other)

    def __eq__(self, other):
        return TermComparison(self, EQ, other)

    def __ne__(self, other):
        return TermComparison(self, NE, other)


####################################################################################################
#
# MulPair
#
####################################################################################################


class MulPair:

    def __init__(self, term, exponent):
        self.term = term
        self.exponent = exponent
        self.key = (term.key, exponent)

    def pretty_print(self):
        if self.exponent == 1:
            return self.term.pretty_print()
        else:
            l, s = self.term.pretty_print()
            if l == ATOM:
                return ATOM, '{0}**{1!s}'.format(s, self.exponent)
            else:
                return ATOM, '({0})**{1!s}'.format(s, self.exponent)

    def canonize(self):
        return self.term.canonize() ** self.exponent

    def __str__(self):
        return self.pretty_print()[1]

    def __repr__(self):
        return self.__str__()

    def __pow__(self, n):
        return MulPair(self.term, self.exponent * n)


####################################################################################################
#
# Comparisons
#
####################################################################################################


# relations between terms
GT, GE, EQ, LE, LT, NE = range(6)


# strings for printing them out
comp_str = {GT: '>', GE: '>=', EQ: '==', LE: '<=', LT: '<', NE: '!='}


# swaps GT and LT, GE and LE, fixes EQ and NE
def comp_reverse(i):
    if i == NE:
        return NE
    else:
        return 4 - i


# swaps GT and LE, GE and LT, EQ and NE
def comp_negate(i):
    return (i+3) % 6


# evaluations
comp_eval = {GT: lambda x, y: x > y, GE: lambda x, y: x >= y, EQ: lambda x, y: x == y,
             LE: lambda x, y: x <= y, LT: lambda x, y: x < y, NE: lambda x, y: x != y}


class TermComparison():

    def __init__(self, term1, comp, term2):
        #print comp
        #print 'creating t_c: ', term1, comp_str[comp], term2
        if isinstance(term1, numbers.Rational):
            self.term1 = STerm(term1, one)
        else:
            self.term1 = term1
        if isinstance(term2, numbers.Rational):
            self.term2 = STerm(term2, one)
        else:
            self.term2 = term2
        self.comp = comp
        self.key = (self.term1.key, comp, self.term2.key)

    def __str__(self):
        return '{0!s} {1} {2!s}'.format(self.term1, comp_str[self.comp], self.term2)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """
        Two TermComparisons are the same if and only if they have the same key.
        """
        if not isinstance(other, TermComparison):
            return False
        else:
            return self.term1.key == other.key

    def canonize(self):
        """
        Returns a comparison "t1 comp t2", where t1 is a Term and t2 is an STerm. A comparison
        with 0 has the form t1 comp zero. Otherwise, t1 has smaller key than t2.
        """
        #print 'canonizing t_c.', self.term1, comp_str[self.comp], self.term2
        t1 = self.term1.canonize()
        t2 = self.term2.canonize()
        #print 't1:', t1.coeff, t1.term, 'key:', t1.term.key, isinstance(t1, STerm)
        #print 't2:', t2.coeff, t2.term, 'key:', t2.term.key, isinstance(t2, STerm)
        comp = self.comp
        if t1.term.key == t2.term.key:
            t = t1.term
            t1, t2 = t1 - t2, zero
            if t1.coeff == 0:
                if comp in [LT, GT, NE]:  # There's a contradiction, 0 != 0
                    return TermComparison(t, comp, STerm(1, t))
                else:
                    return TermComparison(t, EQ, STerm(1, t))

        if t1.term.key > t2.term.key:
            t1, comp, t2 = t2, comp_reverse(comp), t1
        if t1.coeff == 0:
            t1, comp, t2 = t2, comp_reverse(comp), zero
        if t1.coeff < 0:
            comp = comp_reverse(comp)

        return TermComparison(t1.term, comp, t2 / t1.coeff)


####################################################################################################
#
# Constants
#
####################################################################################################


one = One()

zero = STerm(0, One())


####################################################################################################
#
# Tests
#
####################################################################################################


if __name__ == '__main__':
    u, v, w, x, y, z = Vars('u, v, w, x, y, z')
    f = Func('f')
    g = Func('g')

    def test(t):
        print 'term:', t
        print 'canonized:', t.canonize()
        print

    test(x + 0)
    test(f(x, y, z))
    test(x + y)
    test(x + x)
    test(x + (x + y))
    test(x)
    test((x + y) + (z + x))
    test(x * y)
    test(2 * x * y)
    test(2 * (x + y) * w)
    test(2 * ((x + y) ** 5) * g(x) * (3 * (x * y + f(x) + 2 + w) ** 2))
    test((u + 3 * v + u + v + x)**2)
    test(u + 3 * v)
    test((x + (y * z)**5 + (3 * u + 2 * v)**2)**4 * (u + 3 * v + u + v + x)**2)
    test(g(f(x, 2*y), z+(4*w+u**2)**3))
    test(x < 3 * y)
    test(2 * f(x, y + z)**2 == 3 * u * v)
    test(-2 * (x + y) * w >= (x + (y * z)**5 + (3 * u + 2 * v)**2)**4 * (u + 3 * v + u + v + x)**2)
    test(x < -3 * y)
    test((u+v+3*w)-z)
