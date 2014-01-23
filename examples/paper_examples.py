from polya import *
import z3
import timeit

u, v, w, x, y, z = Vars('u v w x y z')
a, b, c, d, e = z3.Reals('a b c d e')


def test1():
    # This example comes from Agigad and Friedman (2006)
    # Solved in ~.08 seconds
    solve(0<x, x<y, (1+x**2)/(2+y)**17 >= (1+y**2)/(2+x)**10)

def z3test1():
    # solved in ~.5 seconds
    s = z3.Solver()
    s.add(0<a, a<b, (1+a**2)/(2+b)**17 >= (1+b**2)/(2+a)**10)
    print s.check()

def test2():
    # This example comes from Avigad and Friedman (2006)
    # solved in ~.1 seconds
    exp = Func('exp')

    B = Blackboard()
    B.assert_comparisons(0<x, x<y, (1+x**2)/(2+exp(y))>=(2+y**2)/(1+exp(x)))

    fm = FunctionModule([ForAll([x, y], And(Implies(x<y, exp(x)<exp(y)),
                                                            exp(x)>0))])

    fm.update_blackboard(B)
    run(B)

def z3test2():
    # Not solved.
    s = z3.Solver()
    exp = z3.Function('exp', z3.RealSort(), z3.RealSort())
    s.add(0<a, a<b, (1+a**2)/(2+exp(b))>=(2+b**2)/(1+exp(a)))
    s.add(z3.ForAll([a, b], z3.And(z3.Implies(a<b, exp(a)<exp(b)), exp(a)>0)))
    print s.check()

def test3():
    # From the Isabelle mailing list- Isabelle will not solve automatically.
    # solved in ~.02 seconds.
    solve(x>0, x<1, y>0, y<1, (x+y)-(x*y) <= 0)

def z3test3():
    # Solves this one in. 0.004 sec
    s = z3.Solver()
    s.add(a>0, a<1, b>0, b<1, (a+b)-(a*b) <= 0)
    print s.check()

def test4():
    # A variant on the above.
    # Solved in ~.03 seconds.
    solve(0 < x, x < 1, 0 < y, y < 1, x**150*y**150 > x**150+y**150)

def z3test4():
    # Does not finish.
    s = z3.Solver()
    s.add(a>0, a<1, b>0, b<1, (a**150 +b) < (a**150*b**150))
    print s.check()

def test5():
    # solved in .005 sec

    S = Solver()
    f = Func('f')
    S.assert_comparisons(x<y, f(x)>f(y))
    S.add_axiom(ForAll([x, y], Implies(x<y, f(x)<f(y))))
    S.check()

def z3test5():
    # solved in .005 sec, but sometimes much longer??
    s = z3.Solver()
    f = z3.Function('exp', z3.RealSort(), z3.RealSort())
    s.add(a<b)
    s.add(f(a)>f(b))
    s.add(z3.ForAll([a, b], z3.Implies(a<b, f(a)<f(b))))
    print s.check()

def test6():
    # solved in .04 sec
    f = Func('f')
    fm = FunctionModule(
        [ForAll([x, y], (f(x)+f(y))/2 >= f((x+y)/2))]
    )

    B = Blackboard()
    B.assert_comparisons(z>0, f(x)+f(y)-z<0, f((x+y)/2)-4*z>0)
    fm.update_blackboard(B)

    run(B)

def z3test6():
    # solved in .007 sec
    f = z3.Function('f', z3.RealSort(), z3.RealSort())
    s = z3.Solver()
    s.add(z3.ForAll([a, b], (f(a)+f(b))/2 >= f((a+b)/2)))
    s.add(c>0, f(a)+f(b)-c<0, f((a+b)/2)-4*c>0)

    print s.check()

def test7():
    # solved in .02 sec
    f = Func('f')
    fm = FunctionModule(
        [ForAll([x, y], f(x*y)==f(x)*f(y)),
         ForAll([x], Implies(x>2, f(x)<0))]
    )

    C = Blackboard()
    C.assert_comparisons(x>1, y>2, f(x*y)>0)
    fm.update_blackboard(C)

    run(C)

def z3test7():
    #times out
    f = z3.Function('f', z3.RealSort(), z3.RealSort())
    s = z3.Solver()
    s.add(z3.ForAll([a, b], f(a*b) == f(a)*f(b)))
    s.add(z3.ForAll([a], z3.Implies(a>2, f(a)<0)))
    s.add(a>1, b>2, f(a*b)>0)

    print s.check()

def test8():
    # a b c d e
    # u v w x y
    f = Func('f')
    S = Solver()
    S.assert_comparisons(f(y, v, w+x)<0, u>0, v>0, u==w, v==x, u==y)

    S.add_axiom(ForAll([x, y], f(x, y, x+y)>0))
    S.check()


def z3test8():
    f = z3.Function('f', z3.RealSort(), z3.RealSort(), z3.RealSort(), z3.RealSort())
    s = z3.Solver()
    s.add(z3.ForAll([a, b], f(a, b, a+b) > 0))
    s.add(f(e, b, c + d)<0, a>0, b>0, a == c, b == d, a == e)

    print s.check()


def test9a():
    # solved in .08 sec
    ceil = Func('ceil')
    x, a, b, m = Vars('x, a, b, m')
    S = Solver()
    S.add_axiom(ForAll([x], ceil(x) >= x))
    S.assert_comparisons(a < b, x > a, m >= ceil((b - a) / (x - a)))
    S.assert_comparison(a + (b - a) / (m + 1) >= x)
    S.check()

def z3test9a():
    # not solved
    ceil = z3.Function('ceil', z3.RealSort(), z3.RealSort())
    s = z3.Solver()
    x = z3.Real('x')
    s.add(z3.ForAll([x], ceil(x) >= x))
    m = z3.Real('m')
    s.add(a<b, x>a, m>=ceil((b-a)/x-a))
    s.add(a+(b-a)/(m+1)>= x)
    print s.check()


def test9():
    # solved in .08 sec
    ceil = Func('ceil')
    f = Func('f')
    x, a, b, m = Vars('x, a, b, m')
    S = Solver()
    S.add_axiom(ForAll([x], ceil(x) >= x))
    S.add_axiom(ForAll([m], f(m) < a + (b - a) / (m + 1)))
    S.assert_comparisons(a < b, x > a, m >= ceil((b - a) / (x - a)))
    S.assert_comparison(f(m) >= x)
    S.check()

def z3test9():
    # not solved
    ceil = z3.Function('ceil', z3.RealSort(), z3.RealSort())
    f = z3.Function('f', z3.RealSort(), z3.RealSort())
    s = z3.Solver()
    x = z3.Real('x')
    m = z3.Real('m')
    s.add(z3.ForAll([x], ceil(x) >= x))
    s.add(z3.ForAll([m], f(m) < a+ (b-a)/(m+1)))
    s.add(a<b, x>a, m>=ceil((b-a)/x-a))
    s.add(f(m)>=x)
    print s.check()


def test10():
    abs2 = Func('abs')
    f = Func('f')
    x, y, z, i = Vars('x, y, z, i')
    S = Solver()
    S.add_axiom(ForAll([x,y], abs2(x + y) <= abs2(x) + abs2(y)))
    S.add_axiom(ForAll([x], abs2(x) == abs2(-1*x)))
    S.assert_comparison(i >= 0)
    S.assert_comparison(abs2(f(x) - f(y)) < 1 / (2 * (i + 1)))
    S.assert_comparison(abs2(f(y) - f(z)) < 1 / (2 * (i + 1)))
    S.assert_comparison(abs2(f(x) - f(z)) >= 1 / (i + 1))
    S.check()

def z3test10():
    abs2 = z3.Function('abs', z3.RealSort(), z3.RealSort())
    f = z3.Function('f', z3.RealSort(), z3.RealSort())
    x, y, z, i = z3.Reals('x y z i')
    S = z3.Solver()
    S.add(z3.ForAll([x,y], abs2(x + y) <= abs2(x) + abs2(y)))
    S.add(i >= 0, abs2(f(y) - f(x)) < 1 / (2 * (i + 1)), abs2(f(z) - f(x)) < 1 / (2 * (i + 1)))
    S.add(abs2(f(z) - f(x)) >= 1 / (i + 1))
    print S.check()

t = timeit.default_timer()

test10()
#z3test10()




print round(timeit.default_timer() - t, 3)