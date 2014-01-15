####################################################################################################
#
# function_module.py
#
# Authors:
# Jeremy Avigad
# Rob Lewis
#
# The routine for learning facts using axioms.
# FunctionModule is initialized with a list of axioms.
# Each time update_blackboard is called, the module will check to see if any new clauses can be
# instantiated from its known axioms, and if so, will add them to the blackboard.
#
####################################################################################################

import polya.main.terms as terms
import polya.main.messages as messages
import polya.main.formulas as formulas
import fractions
import copy
# from itertools import product, ifilter
# from inspect import getargspec
# from copy import copy
# from scipy.linalg import lu
# from numpy import array


def substitute(term, u_index, coeff, i_index):
    """
    Replaces all instances of u_{u_index} in term with coeff * t_{i_index}.
    """
    return reduce_term(term, {u_index: (coeff, i_index)})


def reduce_term(term, env):
    """
    env maps UVar indices to (coeff, IVar index) pairs.
    Replaces all defined UVars in term with their designated values.
    Returns a pair of a new STerm and a flag whether all UVars have been replaced.
    """
    #todo: this duplicates some functionality of Term.substitute(), but adds the check for UVars.
    #can we recover this some other way?
    if isinstance(term, terms.STerm):
        l = reduce_term(term.term, env)
        return terms.STerm(term.coeff*l[0].coeff, l[0].term), l[1]
    if isinstance(term, terms.UVar):
        if term.index in env:
            c, j = env[term.index]
            return terms.STerm(c, terms.IVar(j)), True
        else:
            return terms.STerm(1, term), False

    elif isinstance(term, terms.Atom):
        return terms.STerm(1, term), True

    elif isinstance(term, terms.AddTerm):
        rfunc = lambda (s1, flag1), (s2, flag2): (s1+s2, flag1 and flag2)
        t = reduce(rfunc, [(lambda a: (ap.coeff*a[0], a[1]))(reduce_term(ap.term, env))
                           for ap in term.args])
        return terms.STerm(1, t[0]), t[1]
    elif isinstance(term, terms.MulTerm):
        rfunc = lambda (s1, flag1), (s2, flag2): (s1*s2, flag1 and flag2)
        t = reduce(rfunc, [(lambda a:(a[0]**mp.exponent, a[1]))(reduce_term(mp.term, env))
                           for mp in term.args])
        return terms.STerm(1, t[0]), t[1]
    elif isinstance(term, terms.FuncTerm):
        flag1 = True
        nargs = []
        for a in term.args:
            t = reduce_term(a.term, env)
            s, flag2 = t[0], t[1]
            nargs.append(a.coeff * s)
            flag1 = flag1 and flag2
        return terms.STerm(1, terms.FuncTerm(term.func_name, nargs)), flag1

    else:
        raise Exception("Unknown term type encountered in reduce_term: "+str(term))


class NoTermException(Exception):
    pass


def add_list(l1, l2):
    """Adds two vectors component-wise."""
    return [l1[i]+l2[i] for i in range(len(l1))]


def scale_list(c, l):
    """Scales vector l by constant c."""
    return [c*li for li in l]


def elim_var(i, pivot, rows):
    """
    Adds multiple of vector pivot to each vector in rows to eliminate the ith coordinate.
    """
    if pivot[i] == 0:
        raise Exception
    new_rows = [add_list(r, scale_list(-fractions.Fraction(r[i], pivot[i]), pivot)) for r in rows]
    return new_rows


def elim_var_mul(i, pivot, rows):
    """
    pivot:=[c,a1,a2,...,an] represents c*t1^a1 * t2^a2*...*tn^an. Similarly for r in rows.
    Uses pivot to eliminate ti from each r in rows, respecting the
    """
    if pivot[i] == 0:
        raise Exception
    new_rows = []
    for r in rows:
        scale = -fractions.Fraction(r[i], pivot[i])
        if pivot[0] != 1 and scale.denominator != 1:
            # We (likely) have an irrational.
            #todo: there are situations where we don't: pivot[0] == 4, scale == 1/2.
            raise NoTermException
        new_rows.append([r[0]*pivot[0]**scale] + add_list(r[1:], scale_list(scale, pivot[1:])))
    return new_rows


def add_fm_eq_elim(coeff, term, B):
    """
    Given an additive term, performs fourier-motzkin elimination on known equalities to deduce
    whether term is equal to any problem term.
    """
    if len(term.args) == 1:
        return coeff*term.args[0].coeff, term.args[0].term.index

    nargs = [find_problem_term(B, p.term) for p in term.args]
    for i in range(len(nargs)):
        nargs[i] = (term.args[i].coeff*nargs[i][0], nargs[i][1])

    # Do some linear algebra
    urow = [0]*B.num_terms + [-1]
    for (c, i) in nargs:
        urow[i] = c

    mat = []
    for tc in B.get_equalities():
        i, c = tc.term1.index, tc.term2.coeff
        j = (B.num_terms if c == 0 else tc.term2.term.index)
        row = [0]*(B.num_terms+1)
        row[i] = -1
        row[j] = c
        mat.append(row[:])

    for i in (i for i in range(B.num_terms) if isinstance(B.term_defs[i], terms.AddTerm)):
        row = [0]*(B.num_terms+1)
        row[i] = -1
        for p in B.term_defs[i].args:
            row[p.term.index] = p.coeff
        mat.append(row[:])

    mat.append(urow)

    #begin FM elimination
    rows_i = copy.copy(mat)
    for i in range(B.num_terms):  # check if u = c*i
        rows_j = copy.copy(rows_i)
        for j in range(i + 1, B.num_terms):
            try:
                r = next(r for r in rows_j if r[j] != 0 and r[-1] == 0)
            except StopIteration:
                continue
            rows_j = elim_var(j, r, [row for row in rows_j if row is not r])

        row = next(r for r in rows_j if r[-1] != 0)
        l = len([k for k in row if k != 0])
        if l == 1:
            #we have u = 0. What to do?
            return 0, 0
        elif l == 2:
            #we've found a match for u
            ind = next(k for k in range(len(row)) if row[k] != 0)
            coeff = -fractions.Fraction(row[ind], row[-1])*coeff
            return coeff, ind
        else:
            try:
                r = next(r for r in rows_i if r[i] != 0 and r[-1] == 0)
                rows_i = elim_var(i, r, [row for row in rows_i if row is not r])
            except StopIteration:
                if rows_i[-1][i] != 0:  # there is a t_i in u, and nowhere else. Can't elim.
                    raise NoTermException

    raise NoTermException


def mul_fm_eq_elim(coeff, term, B):
    """
    Given a multiplicative term, performs fourier motzkin elimination on known equalities to see
    whether term is equal to a problem term.
    The first coordinate of the elimination matrix represents the constant coefficient; the ith
    coordinate represents the exponent of ti in c*t1^e1*...*tn^en = 1.
    """
    if len(term.args) == 1 and term.args[0].exponent == 1:
        return coeff, B.term_name(term.args[0]).index

    p = find_problem_term(B, term.args[0].term)
    nt = coeff*(p[0]*terms.IVar(p[1]))**term.args[0].exponent
    for a in term.args[1:]:
        p = find_problem_term(B, a.term)
        nt *= (p[0]*terms.IVar(p[1]))**a.exponent

    nt = nt.canonize()

    if isinstance(nt, terms.STerm):
        coeff, nt = nt.coeff, nt.term
    else:
        coeff = 1

    if nt.key in B.term_names:
        return coeff, B.term_names[nt.key].index

    if all(B.implies(a.term.index, terms.NE, 0, 0) for a in nt.args):
        # we can do FM elim.
        urow = [0]*B.num_terms + [-1]
        for a in nt.args:
            urow[a.term.index] = a.exponent
        urow[0] = 1

        mat = []
        for tc in (e for e in B.get_equalities() if e.term2.coeff != 0):
            i, c, j = tc.term1.index, tc.term2.coeff, tc.term2.term.index
            if B.implies(i, terms.NE, 0, 0):  # if ti != 0, then tj != 0
                row = [0]*(B.num_terms+1)
                row[i] = -1
                row[j] = 1
                row[0] = c
                mat.append(row[:])

        for i in (i for i in range(B.num_terms) if
                  isinstance(B.term_defs[i], terms.MulTerm) and B.implies(i, terms.NE, 0, 0)):
            row = [0]*(B.num_terms+1)
            row[i] = -1
            for p in (p for p in B.term_defs[i].args if p.term.index != 0):
                row[p.term.index] = p.exponent
            row[0] = 1
            mat.append(row[:])

        mat.append(urow)

        rows_i = copy.copy(mat)
        print rows_i
        for i in range(1, B.num_terms):
            rows_j = copy.copy(rows_i)
            for j in range(i+1, B.num_terms):
                try:
                    r = next(r for r in rows_j if r[j] != 0 and r[-1] == 0 and r[0] == 1)
                except StopIteration:
                    try:
                        r = next(r for r in rows_j if r[j] != 0 and r[-1] == 0)
                    except StopIteration:
                        continue

                rows_j = elim_var_mul(j, r, [row for row in rows_j if row is not r])

            for row in (r for r in rows_j if r[-1] != 0):
                l = len([k for k in row if k != 0])
                if l == 1 or row[0] == 0:
                    #we have u = 0. What to do?
                    return 0, 0
                elif l == 2:
                    #we've found a match for u: it's a constant.
                    return coeff*row[0], 0
                elif l == 3:
                    #we've found a match for u, nonconstant
                    coeff = coeff*row[0]
                    ind = next(i for i in range(1, len(row)) if row[i] != 0)
                    if row[ind] == 1:  # otherwise, we have u = ti**k, k!=1
                        print coeff, ind
                        return coeff, ind
            try:
                r = next(r for r in rows_i if r[i] != 0 and r[-1] == 0 and r[0] == 1)
            except StopIteration:
                try:
                    r = next(r for r in rows_i if r[i] != 0 and r[-1] == 0)
                except StopIteration:
                    if rows_i[-1][i] != 0:  # there is a t_i in u, and nowhere else.
                        raise NoTermException

            rows_i = elim_var_mul(i, r, [row for row in rows_i if row is not r])
        raise NoTermException
    raise NoTermException


def find_problem_term(B, term1):
    """
    term is a Term such that all variable occurrences are IVars.
    returns (c, i) such that term = c*ti, or raises NoTermException.

    if term1 is a FuncTerm, recursively find problem terms matching each of the arguments, then
    search for a problem term with the same function name whose arguments are equal to the arguments
    of term1.

    if term1 is an additive or multiplicative term, recursively finds problem terms matching each
    of the arguments, and performs FM elimination on equalities to see if their sum/product is equal
    to a problem term.
    """
    messages.announce('    finding problem term:' + str(term1), messages.DEBUG)
    sterm = term1.canonize()
    term, coeff = sterm.term, sterm.coeff
    if isinstance(term, terms.IVar):
        return coeff, term.index

    b, ind = B.has_name(term)
    if b:
        return coeff, ind

    if isinstance(term, terms.FuncTerm):
        nargs = [find_problem_term(B, p.term) for p in term.args]
        for i in range(len(nargs)):
            nargs[i] = (term.args[i].coeff*nargs[i][0], nargs[i][1])

        for i in range(B.num_terms):
            t = B.term_defs[i]
            if (isinstance(t, terms.FuncTerm) and t.func_name == term.func_name
               and len(t.args) == len(nargs)):
                match = True
                for k in range(len(t.args)):
                    targ, uarg = (t.args[k].coeff, t.args[k].term.index), nargs[k]
                    p = tuple(sorted((targ[1], uarg[1])))
                    if targ == uarg:
                        continue
                    elif targ[1] == uarg[1]:
                        if targ[1] in B.zero_equalities:
                            continue
                    elif p in B.equalities:
                        c = B.equalities[p]
                        if targ[1] < uarg[1]:
                            c = fractions.Fraction(1, c)
                        if uarg[0]*c==targ[0]:
                            continue
                    break

                if match:
                    return coeff, i
        raise NoTermException

    elif isinstance(term, terms.AddTerm):
        return add_fm_eq_elim(coeff, term, B)

    elif isinstance(term, terms.MulTerm):
        return mul_fm_eq_elim(coeff, term, B)

    raise NoTermException


def unify(B, termlist, uvars, arg_uvars, envs=None):
    """
    Takes Terms s1...sn involving uvars u1...um
    arg_uvars is a subset of uvars: those that occur alone as function arguments in s1...sn.
    Optional envs is a list of maps from UVar indices to (const, IVar index) pairs.
    Returns a list of assignments under which each si is equal to a problem term in B.
    """

    def occurs_as_arg(term, varkey):
        """
        Returns true if term is a FuncTerm and var occurs alone as an argument.
        """
        if not isinstance(term, terms.FuncTerm):
            return False
        return any(a.term.key == varkey for a in term.args)

    messages.announce(' Unifying :' + str(termlist) + str(arg_uvars) + str(envs),
                      messages.DEBUG)

    if len(uvars) == 0:
        return envs

    if len(arg_uvars) == 0:
        #todo: we should find a way to handle the case where no variables occur alone in func terms.
        return envs

    v = arg_uvars[0]
    vkey = terms.UVar(v).key
    try:
        t = next(term for term in termlist if occurs_as_arg(term, vkey))
    except StopIteration:
        raise Exception('arg_uvars not set up right.'+str(termlist)+str(uvars)+str(arg_uvars))
    ind = next(j for j in range(len(t.args)) if t.args[j].term.key == vkey)
    c = t.args[ind].coeff

    # we have: t = f(..., c*u_v, ...)
    #print 't:', t
    prob_f_terms = [i for i in range(B.num_terms) if
                    (isinstance(B.term_defs[i], terms.FuncTerm)
                     and B.term_defs[i].func_name == t.func_name
                     and len(B.term_defs[i].args) == len(t.args))]

    messages.announce('   probfterms:' + str(prob_f_terms), messages.DEBUG)

    s = [(fractions.Fraction(B.term_defs[i].args[ind].coeff, c),
          B.term_defs[i].args[ind].term.index) for i in prob_f_terms]

    # s is a list of pairs (coeff, j) such that c*coeff*tj occurs as an argument to f in a pr. term

    nenvs = []
    for (coeff, j) in s:
        #new_terms = [p.substitute({vkey: coeff*terms.IVar(j)}) for p in termlist]
        new_terms = [substitute(p, v, coeff, j) for p in termlist]
        closed_terms, open_terms = list(), list()

        for (a, b) in new_terms:
            if b:
                closed_terms.append(a)
            else:
                open_terms.append(a)

        try:
            messages.announce('   closed terms:' + str(closed_terms), messages.DEBUG)
            prob_terms = [find_problem_term(B, ct.term) for ct in closed_terms]
        except NoTermException:
            #print 'exception for:', v, '=', coeff, j
            continue

        #todo: prob_terms isn't actually used in what follows. Could it be?

        # At this point, every closed term matches something in the problem.
        cenvs = copy.deepcopy(envs) if envs else [{}]
        for c in cenvs:
            c[v] = (coeff, j)
            maps = unify(B, [o.term for o in open_terms],
                         [v0 for v0 in uvars if v0 != v], arg_uvars[1:], cenvs)
            nenvs.extend(maps)
    return nenvs


def instantiate(axiom, B):
    # Get a list of assignments that work for all of axiom's triggers.
    envs = unify(B, axiom.triggers, list(axiom.vars), list(axiom.trig_arg_vars))
    messages.announce(' Environments:', messages.DEBUG)
    for e in envs:
        messages.announce('  '+str(e), messages.DEBUG)

    # For each assignment, use it to instantiate a Clause from axiom and assert it in B.
    clauses = []
    for env in envs:
        literals = []
        for l in axiom.literals:
            comp = l.comp
            red = reduce_term(l.term1, env)[0].canonize()
            red_coeff, red_term = red.coeff, red.term
            try:
                #print 'finding prob term:', red, isinstance(red, terms.STerm)
                lcoeff, lterm = find_problem_term(B, red_term)
                lcoeff *= red_coeff
            except NoTermException:
                sred = red.canonize()
                lterm = B.term_name(sred.term).index
                lcoeff = sred.coeff

            red = reduce_term(l.term2.term, env)[0]
            red_coeff, red_term = red.coeff, red.term
            try:
                rcoeff, rterm = find_problem_term(B, red.term)
                rcoeff *= l.term2.coeff*red_coeff
            except NoTermException:
                sred = red.canonize()
                rterm = B.term_name(sred.term).index
                rcoeff = sred.coeff * l.term2.coeff

            literals.append(
                terms.comp_eval[comp](lcoeff*terms.IVar(lterm), rcoeff*terms.IVar(rterm))
            )
        clauses.append(literals)
        #print 'literals:', literals
    return clauses


class FunctionModule:

    def __init__(self, axioms=list()):
        """
        axioms is a list of Formula objects, that need to be converted into Axiom objects.
        """
        self.axioms = []
        for a in axioms:
            clauses = formulas.cnf(a)
            self.axioms.extend(formulas.Axiom(c) for c in clauses)

    def add_axiom(self, axiom):
        """
        axiom is a Formula.
        """
        clauses = formulas.cnf(axiom)
        self.axioms.extend(formulas.Axiom(c) for c in clauses)

    def update_blackboard(self, B):
        messages.announce_module('function axiom module')
        for a in self.axioms:
            messages.announce("Instantiating axiom: {}".format(a), messages.DEBUG)
            clauses = instantiate(a, B)
            for c in clauses:
                B.assert_clause(*c)