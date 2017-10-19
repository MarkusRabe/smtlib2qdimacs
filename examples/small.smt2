
(declare-fun c0 () Bool)
(declare-fun c1 () Bool)
(declare-fun c2 () Bool)
(define-fun e3 () Bool (not c1))
(define-fun e4 () Bool (and c2 e3))
(define-fun e5 () Bool (or c1 e4))
(define-fun e6 () Bool (and c0 e5))
(declare-fun c7 () Bool)
(declare-fun c8 () Bool)
(declare-fun c9 () Bool)
(define-fun e10 () Bool (not c8))
(define-fun e11 () Bool (and c9 e10))
(define-fun e12 () Bool (or c8 e11))
(define-fun e13 () Bool (and c7 e12))
(assert e13)

(define-fun e425 () Bool (and c9 c9))
(define-fun e426 () Bool (and c8 c7))
(define-fun e427 () Bool (or e3 e10))
(define-fun e428 () Bool (and e425 e427))
(assert e428)

(define-fun e70412 ((c2309 Bool) (c2310 Bool) (c2311 Bool) (c2312 Bool) (c2313 Bool) (c2314 Bool) (c2315 Bool) (c2316 Bool)) Bool (not (and c2309 c2310 c2311 c2312 c2313 c2314 c2315 c2316)))

(define-fun e70413 () Bool (forall ((c2309 Bool) (c2310 Bool) (c2311 Bool) (c2312 Bool) (c2313 Bool) (c2314 Bool) (c2315 Bool) (c2316 Bool)) (e70412 c2309 c2310 c2311 c2312 c2313 c2314 c2315 e13)))

(assert e70413)

