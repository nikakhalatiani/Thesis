<start>   ::= <expr>
<expr>    ::= <term> ", " <term> | <term> ", " <expr>

<term>    ::= <number>
<number>  ::= <digit>+
<digit>   ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

where int(<term>) != 0