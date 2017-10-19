# smtlib2qdimacs

A translator from SMTLIB2 to QDIMACS. Restricted to the bitvector theory and still incomplete. 

[SMTLIB2](http://smtlib.cs.uiowa.edu/) is the standard format for Satisfiability Modulo Theory (SMT) solvers and used in many industrial and academic tools. Recent progress in algorithms for Quantified Boolean Formulas (QBF) makes it tempting to run QBF solvers on problems formulated in SMTLIB2 that contain quantifiers. 

## Usage

> python smtlib2qdimacs.py -o=output.qdimacs input.smt

If no output file is specified, the tool will write to the file input.smt.qdimacs. Use the command line option '-2' to negate formulas. Depending on your problem, this may reduce the number of quantifier alternations by one. 

## Notes

It turns out it is surprisingly hard to bitblast quantified formulas and maintain a variable mapping. This script is a partial implementation. Using the [python z3 API](https://z3prover.github.io/api/html/z3.html). Beware that this script is still pretty slow. It may take a couple of seconds to produce formulas. 

Please contribute!

