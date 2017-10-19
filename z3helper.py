

def is_quant(e):
    return e.__class__.__name__ == 'QuantifierRef'
# def is_not(e):
#     try:
#         return str(e.decl()) == 'Not'
#     except:
#         return False
# def is_and(e):
#     try:
#         return str(e.decl()) == 'And'
#     except:
#         return False

#################### Helper function to get all variables from an expression ######################
# https://stackoverflow.com/questions/14080398/z3py-how-to-get-the-list-of-variables-from-a-formula
# Wrapper for allowing Z3 ASTs to be stored into Python Hashtables. 
# class AstRefKey:
#     def __init__(self, n):
#         self.n = n
#     def __hash__(self):
#         return self.n.hash()
#     def __eq__(self, other):
#         return self.n.eq(other.n)
#     def __repr__(self):
#         return str(self.n)
#
# def askey(n):
#     assert isinstance(n, AstRef)
#     return AstRefKey(n)
#
# def get_vars(f):
#     r = set()
#     def collect(f):
#       if is_const(f):
#           if f.decl().kind() == Z3_OP_UNINTERPRETED and not askey(f) in r:
#               r.add(askey(f))
#               log('  Found variable: {}'.format(str(f)))
#       else:
#           for c in f.children():
#               collect(c)
#     collect(f)
#     return r
###################################################################################################
