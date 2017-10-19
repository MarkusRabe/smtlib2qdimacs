#!/usr/bin/env python2

import z3
from z3 import SolverFor, Bool, BitVec, BitVecVal, And, Or, Not, Implies, Extract, sat, Goal, Then, is_or, is_not, If, is_bv, is_bool, is_const, parse_smt2_file, parse_smt2_string, Z3_PRINT_SMTLIB_FULL, Z3_OP_UNINTERPRETED, AstRef, is_and, is_not

from z3helper import is_quant

import os, sys, re, itertools

Write2QBF = False

def log(x):
    print('  ' + x)

# Creates a dictionary mapping tuples of bitvec and bit-index to a boolean variable
def create_bitmap(bitvecs):
    bitmap = {}
    constraints = []
    for bv in bitvecs:
        for i in range(bv.size()):
            var = Bool(str(bv)+'_bit'+str(i))
            bitmap[(bv,i)] = var
            mask = BitVecVal(2**i, bv.size())
            constraints.append(var == ((bv & mask) == mask))
    return bitmap, And(constraints)

def encode_literal(var_mapping, Tseitin_vars, max_var, l):
    var = None
    if is_not(l):
        var = l.children()[0]
        lit_str = '-'
    else:
        var = l
        lit_str = ''
    assert is_const(var) # will fail

    if var.get_id() not in var_mapping:
        max_var += 1
        Tseitin_vars.append(max_var)
        var_mapping[var.get_id()] = max_var
    lit_str += str(var_mapping[var.get_id()]) + ' '
    return max_var, lit_str

def assert_consistent_quantifiers(quantifiers):
    
    for i, q in enumerate(quantifiers):
        if len(q[1]) == 0:
            log('Warning: empty quantifier, index ' + str(i))
        if q[0] == 'max': 
            assert i == 0
            assert len(quantifiers) == 2
            assert quantifiers[1][0] == 'count'
            assert len(quantifiers[i+1][1]) > 0
            break
        if q[0] == 'a' and len(quantifiers) > i + 1:
            assert quantifiers[i+1][0] == 'e'
            assert len(quantifiers) > i+1
        if q[0] == 'e' and len(quantifiers) > i:
            assert i == len(quantifiers)-1 or quantifiers[i+1][0] == 'a'
        
        # if i + 1 < len(quantifiers):
        #     for j in range(i+1,len(quantifiers)):
        #         q_strs = map(str,quantifiers[j])
        #         for v in q[1]:
        #             assert(str(v) not in q_strs)
        

def writeQDIMACS(filename, constraint, quantifiers, bitmap=None):
    # filename: String
    # constraints: list of BV constraints
    # quantifiers: list of tuples (['a','e','max','count'], list of vars)
    
    assert_consistent_quantifiers(quantifiers)
    
    log('Bit blasting')
    bitmap = {}
    
    for q in quantifiers:
        bitvecs = filter(is_bv, q[1])
        localBitmap, localBitmapConstraints = create_bitmap(bitvecs)
        bitmap.update(localBitmap)
        constraint = And(localBitmapConstraints, constraint)
        newQuantifiedVars = filter(lambda v: not is_bv(v), q[1])
        for (_,boolvar) in localBitmap.iteritems():
            newQuantifiedVars.append(boolvar)
        q[1] = newQuantifiedVars
    
    g = Goal()
    g.add(constraint)
    matrix = []
    t = Then('simplify', 'bit-blast', 'tseitin-cnf')
    subgoal = t(g)
    # print(subgoal[0][0].children()[1].children()[0] == bitmap())
    assert len(subgoal) == 1
    
    # print('Printing quantifier')
    # print(quantifiers)
    # print('Printing goal')
    # print(g)
    # exit()
    
    max_var = 0
    var_mapping = {} # maps to qdimacs variables
    
    textFile = open(filename, "w")
        
    log('Creating and writing symbol table')
    textFile.write('c Symbol table for bitvectors\n')
    symbol_table = []
    for ((bv,i),boolvar) in bitmap.iteritems():
        max_var += 1
        var_mapping[boolvar.get_id()] = max_var
        # symbol_table.append('c ' + str(boolvar) + ' --> ' + str(max_var))
        textFile.write('c ' + str(boolvar) + ' --> ' + str(max_var) + '\n')
    
    log('Reserving variable names for quantified variables')
    for i, q in enumerate(quantifiers):
        for var in q[1]:
            if var.get_id() not in var_mapping:
                max_var += 1
                var_mapping[var.get_id()] = max_var
    
    # minTseitin = max_var + 1
    Tseitin_vars = []
    
    log('Generating clauses ... (this may take a while)')
    clause_num = 0
    for c in subgoal[0]:
        clause_num += 1
        if clause_num % 10000 == 0:
            log('  {} clauses'.format(clause_num))
        if is_or(c):
            clause = ''
            for l in c.children(): # literals
                max_var, lit_str = encode_literal(var_mapping, Tseitin_vars, max_var, l)
                clause += lit_str
            matrix.append(clause)
        elif is_const(c) or is_not(c):
            max_var, lit_str = encode_literal(var_mapping, Tseitin_vars, max_var, c)
            matrix.append(lit_str)
        else: 
            log('Error: Unknown element ' + str(c))
            assert false
    matrix.append('')
    log('  Generated ' + str(clause_num) + ' clauses')
    
    log('Writing header')
    textFile.write('p cnf {} {}\n'.format(max_var,clause_num))
    
    # Extending quantifiers by innermost existential if necessary
    if quantifiers[-1][0] == 'a' and len(Tseitin_vars) > 0: #  max_var + 1 - minTseitin > 0
        quantifiers.append(['e',[]]) # empty existential
            
    log('Writing quantifiers')
    for i, q in enumerate(quantifiers):
        textFile.write(q[0])
        for v in q[1]:
            # try:
            v_id = v.get_id()
            textFile.write(' ' + str(var_mapping[v_id]))
            # except Exception as ex:
            #     log(' Error when writing var {} to file ({})'.format(str(v), str(ex)))
            #
            #     template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            #     message = template.format(type(ex).__name__, ex.args)
            #     print message
            #
            #     exit()
        
        if i == len(quantifiers) - 1:
            log('Adding {} Tseitin variables'.format(len(Tseitin_vars)))
            for varID in Tseitin_vars:
                textFile.write(' '+str(varID))
            
            # for varID in range(minTseitin,max_var+1):
#                 # log('Adding var {}'.format(varID))
#                 textFile.write(' '+str(varID))
#                 # quantifiers[-1][1].append(varID)
            # log('  OK (added {} Tseitin vars)'.format(len(range(minTseitin,max_var+1))))
        
        textFile.write(' 0\n')
    
    log('Writing clauses')
    textFile.write('0\n'.join(matrix))
    textFile.close()
    
    return var_mapping
    
#
#     # model is a dict from max_vars to values (boolean for Bools and numbers for BVs)
#     model = {}
#     for v in max_vars:
#         if is_bv(v):
#             value = 0
#             for i in range(v.size()):
#                 bool_var = max_bitmap[(v,i)]
#                 assert is_bool(bool_var) and is_const(bool_var)
#                 dimacs_var_id = var_map[bool_var.get_id()]
#                 bool_value = values[dimacs_var_id]
#                 assert value != None
#                 if bool_value:
#                     value += 2**(v.size() - i - 1) # TODO: correct?
#             model[v] = value
#         else:
#             assert is_bool(v)
#             value = values[var_map[v.get_id()]]
#             assert value != None
#             model[v] = value
#
#     return model

def toSMT2Benchmark(f, status="unknown", name="benchmark", logic=""):
  v = (z3.Ast * 0)()
  return z3.Z3_benchmark_to_smtlib_string(f.ctx_ref(), name, logic, status, "", 0, v, f.as_ast())

def flatten_and_tree(expr):
    if is_and(expr):
        return sum(map(flatten_and_tree,expr.children()),[])
    else:
        return [expr]

# Can only handle one quantifier in an And-tree
def flatten_quantifier(expr):
    
    boundvariables = []
    quantifiers = []
    
    es = flatten_and_tree(expr)
    
    assert(len(filter(is_quant,es)) <= 1)
    
    for idx, e in enumerate(es):
        negated = False
        if is_not(e):
            e = e.children()[0]
            negated = True
        if is_quant(e):
            while is_quant(e):
                variables = []
                for i in range(e.num_vars()):
                    # variables += [[expr.var_name(i), expr.var_sort(i)]]
                    if str(e.var_sort(i)).startswith('BitVec'):
                        var = BitVec(e.var_name(i), e.var_sort(i).size())
                    else:
                        assert(str(e.var_sort(i)) == ('Bool'))
                        var = Bool(e.var_name(i))
                    
                    variables.append(var)
                
                    # if var in boundvariables:
                    #     log('ERROR: Currently require all variable names to be unique.')
                    #     exit()
                
                if e.is_forall():
                    negated = not negated
                if negated:
                     new_quant = 'a'
                else:
                    new_quant = 'e'
                quantifiers += [[new_quant, variables]]
                boundvariables += variables
                e = e.body()
            es[idx] = e
            break; # only supports the case that at most one of the conjuncts is a quantiifer
    
    return And(es), boundvariables, quantifiers

def separateQuantifiersFromConstraints(expr):
    
    log('Separating constraints from quantifiers')
    
    # if not is_quant(expr):
        # expr2 = expr.children()[2]
        # print toSMT2Benchmark(expr2)
        # exit()
    
    new_expr, boundvariables, quantifiers = flatten_quantifier(expr)
    
    return new_expr, boundvariables, quantifiers


def reencode_quantifiers(expr, boundvariables, quantifiers):
    
    z3.set_option(max_args=10000000, max_lines=1000000, max_depth=10000000, max_visited=1000000)
    smt2string = toSMT2Benchmark(expr)
    
    # Have to scan the string, because other methods proved to be too slow.
    log('Detect declarations of the free variables in SMTLIB2 string') 
    free_variables = re.findall('\(declare-fun (\w+) \(\) (Bool)|\(declare-fun (\w+) \(\) \(\_ BitVec (\d+)\)', smt2string)
    free_variables += re.findall('\(declare-const (\w+) (Bool)|\(declare-const (\w+) \(\_ BitVec (\d+)\)', smt2string)
    
    print(free_variables)
    exit()
    
    for fv in free_variables:
        if str(fv).startswith('?'):
            print('Error: Variable starts with "?". Potential for confusion with quantified variables. This case is not handled.')
            exit()
    
    log('  Found {} free variables'.format(len(free_variables)))
    
    # Turn free variables into z3 variabes and add them to the quantifier
    for idx, (a,b,x,y) in enumerate(free_variables):
        assert(a != '' or x != '')
        if a != '':
            assert(b == 'Bool')
            free_variables[idx] = Bool(a)
        else:
            free_variables[idx] = BitVec(x,int(y))
    
    quantifiers = [['e', free_variables]] + quantifiers
    
    
    log('Replacing de Bruijn indices by variables')
    matches = re.findall('\?(\d+)', smt2string)
    deBruijnIDXs = map(int,set(matches))
    assert(len(deBruijnIDXs) <= len(boundvariables))
    # sort de Bruijn indeces in decreasing order so that replacing smaller numbers does not accidentally match larger numbers
    deBruijnIDXs = list(deBruijnIDXs)
    deBruijnIDXs.sort()
    deBruijnIDXs.reverse()
    
    for idx in deBruijnIDXs:
        smt2string = smt2string.replace('?{}'.format(idx), str(boundvariables[-(1+int(idx))]))
    
    log('Generating SMTLIB without quantifiers')
    # introduce quantified variables to enable re-parsing
    declarations = []
    for var in boundvariables:
        if is_bv(var):
            declarations.append('(declare-fun {} () (_ BitVec {}))'.format(str(var), var.size()))
        else: 
            assert(is_bool(var))
            declarations.append('(declare-fun {} () Bool)'.format(str(var)))
    
    smt2string  = '\n'.join(declarations) + '\n' + smt2string
    
    log('Reparsing SMTLIB without quantifiers')
    flat_constraints = parse_smt2_string(smt2string)
    
    # log('Extract all variables')
    # allvariables = get_vars(flat_constraints)
    #
    # log('Search for free variables')
    # freevariables = []
    # known_vars = set(map(str,boundvariables))
    # for idx, var in enumerate(allvariables):
    #     if idx+1 % 10000 == 0:
    #         log('  {} variables checked if free'.format(idx))
    #     if str(var) not in known_vars:
    #         freevariables.append(var.n) # var.n because var is only the AstRefKey object
    #
    # log('Found {} free variables'.format(len(freevariables)))
    #
    # quantifiers = [['e', freevariables]] + quantifiers
    
    # delete empty quantifiers
    i = 0
    while i < len(quantifiers):
        if len(quantifiers[i][1]) == 0:
            del(quantifiers[i])
        else:
            i += 1
        
    for i in range(len(quantifiers)-1):
        if quantifiers[i][0] == quantifiers[i+1][0]:
            mergedQuantifiers[-1][1] += quantifiers[i+1][1]
        else:
            mergedQuantifiers += [quantifiers[i+1]]
    
    # merge successive quantifiers of the same type
    if len(quantifiers) > 0:
        mergedQuantifiers = [quantifiers[0]]
        for i in range(len(quantifiers)-1):
            if quantifiers[i][0] == quantifiers[i+1][0]:
                mergedQuantifiers[-1][1] += quantifiers[i+1][1]
            else:
                mergedQuantifiers += [quantifiers[i+1]]
        
        quantifiers = mergedQuantifiers
        
    # print quantifiers
    return quantifiers, And(flat_constraints)
    
    
if __name__ == "__main__":
    
    assert(len(sys.argv) > 1)
    
    if '-h' in sys.argv or '--help' in sys.argv:
        print('Usage: smt2dimacs.py <file.efy>')
        exit()
        
    if '-2' in sys.argv:
        Write2QBF = True
    
    filename = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            filename = arg
    if filename == None:
        print('Error: no filename given')
        exit()
        
    outfile = filename+'.qdimacs'
    for arg in sys.argv[1:]:
        if arg.startswith('-o='):
            outfile = arg[3:]
            log('Setting output file: ' + outfile)
    
    log('Parsing SMTLIB')
    expr = parse_smt2_file(filename)
    
    new_expr, boundvariables, quantifiers = separateQuantifiersFromConstraints(expr)
    quantifiers, constraint = reencode_quantifiers(new_expr, boundvariables, quantifiers)
    
    if Write2QBF:
        constraint = Not(constraint)
        for q in quantifiers:
            assert(q[0] == 'a' or q[0] == 'e')
            if q[0] == 'a':
                q[0] = 'e'
            elif q[0] == 'e':
                q[0] = 'a'
        
    writeQDIMACS(outfile, constraint, quantifiers)
    