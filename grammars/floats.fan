<start>   ::= <expr>
<expr>    ::= <term> ", " <expr> | <term> ", " <term> ", " <term>
<term>    ::= <number>
<number>  ::= "-"?<float> := str(produce_gaussian_float())
<float>   ::= <digit>+ "." <digit>+

def produce_gaussian_float():
    import random
    mu = 0
    sigma = 400
    value = random.gauss(mu, sigma)
    return value