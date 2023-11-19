import argparse
import sys
from collections import defaultdict

# Character classes
LETTER = 0
DIGIT = 1
UNKNOWN = 99

# Token codes
INT_LIT = 10
IDENT = 11
ASSIGN_OP = 20
ADD_OP = 21
SUB_OP = 22
MULT_OP = 23
DIV_OP = 24
LEFT_PAREN = 25
RIGHT_PAREN = 26
SEMICOLON = 27
EOF = -1

# Error code
OK = 1
ERROR = 2
WARNING = 3
UNSET = -1
_parsing_msg = '(OK)'
_parsing_status = OK

# Equation evalution
_op_order = {ADD_OP:1, SUB_OP:1, MULT_OP:2, DIV_OP:2, LEFT_PAREN:3, RIGHT_PAREN:3}
_symbol_dic = {}
_parsing_stack = []

_print_mode = True
_file_pointer = 0
_file_content = ''
_char_class = 0
_lexeme = [' ']*100
_next_char = ''
_lex_len = 0
_next_token = 0

##########################Lexical Analyzer##########################
# get the next character of input and determine its character class   
def get_char():
    global _file_content
    global _file_pointer
    global _next_char
    global _char_class

    if _file_pointer >= len(_file_content):
        _char_class = EOF
        return

    _next_char = _file_content[_file_pointer]
    _file_pointer += 1
    if _next_char != EOF:
        if _next_char.isalpha():
            _char_class = LETTER
        elif _next_char.isdigit():
            _char_class = DIGIT
        else:
            _char_class = UNKNOWN
    else:
        _char_class = EOF
    
# add nextChar to lexeme
def add_char():
    global _lex_len
    global _next_char
    global _lexeme
    if _lex_len <= 98:
        _lexeme[_lex_len] = _next_char
        _lex_len += 1
        _lexeme[_lex_len] = 0

# lookup operators and parentheses and return the token
def lookup(ch):
    global _next_token

    if ch == '(':
        add_char()
        _next_token = LEFT_PAREN
    elif ch == ')':
        add_char()
        _next_token = RIGHT_PAREN
    elif ch == '+':
        add_char()
        _next_token = ADD_OP
    elif ch == '-':
        add_char()
        _next_token = SUB_OP
    elif ch == '*':
        add_char()
        _next_token = MULT_OP
    elif ch == '/':
        add_char()
        _next_token = DIV_OP
    elif ch == '=':
        add_char()
        _next_token = ASSIGN_OP
    elif ch == ';':
        add_char()
        _next_token = SEMICOLON
    elif ch != ' ':
        add_char()
        _next_token = UNKNOWN
    
    return _next_token

# lexical analyzer for arithmetic expressions
def lex():
    global _lex_len
    global _char_class
    global _next_token
    global _lexeme

    _lex_len = 0
    # skip space
    while _next_char == ' ':
        get_char()

    if _char_class == LETTER:
        add_char()
        get_char()
        while _char_class == LETTER or _char_class == DIGIT:
            add_char()
            get_char()
        _next_token = IDENT

    elif _char_class == DIGIT:
        add_char()
        get_char()
        while _char_class == DIGIT:
            add_char()
            get_char()
        _next_token = INT_LIT
  
    # Parentheses and operators
    elif _char_class == UNKNOWN:
        lookup(_next_char)
        get_char()

    elif _char_class == EOF:
        _next_token = EOF
        _lexeme[0] = 'E'
        _lexeme[1] = 'O'
        _lexeme[2] = 'F'
        _lexeme[3] = 0
        _lex_len = 3

    lex = ':=' if ''.join(_lexeme[:_lex_len]) == '=' else ''.join(_lexeme[:_lex_len])
    if _print_mode:
        print('[Lexer] : Next token is ', lex)
    return _next_token
            

############################Evaluation############################
def eval_stack():
    global _parsing_status
    global _parsing_msg

    stmt = ' '.join(lex for _, lex in _parsing_stack).replace('=', ':=')
    if _next_token == SEMICOLON:
        stmt += ' '+ ''.join(_lexeme[:_lex_len])
    if not _print_mode:
        print(f'[ Eval ] {stmt}')

    lefthand_symbol = _parsing_stack[0][1]
    if lefthand_symbol not in _symbol_dic.keys():
        _symbol_dic[lefthand_symbol] = 0
    
    n_id = 1
    n_const = 0
    n_op = 0
    op_stack = []
    n_stack = []
    postfix_eq = []

    # convert into postfix equation
    for i in range(2, len(_parsing_stack)):
        token = _parsing_stack[i][0]
        lexeme = _parsing_stack[i][1]

        if token == INT_LIT or token == IDENT:
            if token == IDENT and lexeme not in _symbol_dic.keys():
                _symbol_dic[lexeme] = 'Unknown'
                _parsing_msg = f'(ERROR) 정의되지 않은 변수({lexeme})가 참조됨'
                _parsing_status = ERROR
            postfix_eq.append(_parsing_stack[i])
            
        elif token == ADD_OP or token == SUB_OP or token == DIV_OP  or \
             token == MULT_OP or token == LEFT_PAREN:
            if len(op_stack) != 0 and op_stack[-1][0] != LEFT_PAREN:
                while _op_order[op_stack[-1][0]] >= _op_order[token]:
                    postfix_eq.append(op_stack.pop())
            op_stack.append(_parsing_stack[i])

        elif token == RIGHT_PAREN:
            while len(op_stack) != 0 and op_stack[-1][0] != LEFT_PAREN:
                x = op_stack.pop()
                postfix_eq.append(x)

    while op_stack:
        x = op_stack.pop()
        if x[0] == LEFT_PAREN: continue
        postfix_eq.append(x)
    
    # evaluate equation
    try:
        for token, lexeme in postfix_eq:
            n1, n2 = 0, 0
            if token == ADD_OP:
                n_op += 1
                n2, n1 = n_stack.pop(), n_stack.pop()
                if n2 != 'Unknown' and n1 != 'Unknown':
                    n_stack.append(n1+n2)
                else:
                    n_stack.append('Unknown')
            elif token == SUB_OP:
                n_op += 1
                n2, n1 = n_stack.pop(), n_stack.pop()
                if n2 != 'Unknown' and n1 != 'Unknown':
                    n_stack.append(n1-n2)
                else:
                    n_stack.append('Unknown')
            elif token == DIV_OP:
                n_op += 1
                n2, n1 = n_stack.pop(), n_stack.pop()
                if n2 != 'Unknown' and n1 != 'Unknown':
                    n_stack.append(n1/n2)
                else:
                    n_stack.append('Unknown')
            elif token == MULT_OP:
                n_op += 1
                n2, n1 = n_stack.pop(), n_stack.pop()
                if n2 != 'Unknown' and n1 != 'Unknown':
                    n_stack.append(n1*n2)
                else:
                    n_stack.append('Unknown')
            else:
                if token == INT_LIT:
                    n_const +=1
                    n_stack.append(int(lexeme))
                else:
                    n_id += 1
                    n_stack.append(_symbol_dic[lexeme])

        _symbol_dic[lefthand_symbol] = n_stack.pop()

    except:
        _parsing_status = ERROR
                
    _parsing_stack.clear()
    if _parsing_status == UNSET: _parsing_status = OK
    return n_id, n_const, n_op
        
############################Parser############################
def error():
    global _parsing_msg
    global _parsing_status
    global _parsing_stack

    _parsing_status = WARNING
    _parsing_msg = '(ERROR) Syntax error'
    # _parsing_stack.clear()

''' factor
Parses strings in the language generated by the rule:
<factor> → <left_paren><expression><right_paren> | <ident> | <const>
'''
def factor():
    _parsing_stack.append((_next_token, ''.join(_lexeme[:_lex_len])))
    if _next_token == LEFT_PAREN:
        lex()
        expression()
        if _next_token == RIGHT_PAREN:
            _parsing_stack.append((_next_token, ''.join(_lexeme[:_lex_len])))
            lex()
        else:
            error()
    elif _next_token == IDENT or _next_token == INT_LIT:
        lex()
    else:
        error()
    

''' factor_tail
Parses strings in the language generated by the rule:
<factor_tail> → <mult_op><factor><factor_tail> | ε
'''
def factor_tail():
    if _next_token == MULT_OP or _next_token == DIV_OP:
        _parsing_stack.append((_next_token, ''.join(_lexeme[:_lex_len])))
        lex()
        factor()
        factor_tail()

''' term
Parses strings in the language generated by the rule:
<term> → <factor> <factor_tail>
'''
def term():
    factor()
    factor_tail()

''' term_tail
Parses strings in the language generated by the rule:
<term_tail> → <add_op><term><term_tail> | ε
'''
def term_tail():
    global _parsing_status
    global _parsing_msg

    if _next_token == ADD_OP or _next_token == SUB_OP:
        _parsing_stack.append((_next_token, ''.join(_lexeme[:_lex_len])))
        lex()
        if _next_token == ADD_OP or _next_token == SUB_OP:
            _parsing_status = WARNING
            op = ''.join(_lexeme[:_lex_len])
            _parsing_msg = f'(WARNING) 중복 연산자 ({op}) 제거'
            lex()
        term()
        term_tail()

''' expression
Parses strings in the language generated by the rule:
<expression> → <term><term_tail>
'''
def expression():
    term()
    term_tail()

''' statement
Parses strings in the language generated by the rule:
<statement> → <ident><assignment_op><expression>
- Error handling : if there isn't any assign operator after first identification 
- replace the next lexeme into a assign operator
'''
def statement():
    global _parsing_status
    global _parsing_msg

    if _next_token == IDENT:
        _parsing_stack.append((_next_token, ''.join(_lexeme[:_lex_len])))
        lex()
        if _next_token == ASSIGN_OP:
            _parsing_stack.append((ASSIGN_OP, ''.join(_lexeme[:_lex_len])))
            lex()
            expression()
        else:
            _parsing_stack.append((ASSIGN_OP, '='))
            _parsing_status = WARNING
            op = ''.join(_lexeme[:_lex_len])
            _parsing_msg = f'(WARNING) 잘못된 연산자 ({op})를 = 로 대체'
            lex()
            expression()
    else:
        error()
    
    # print parsing result of a single line of the code
    n_id, n_const, n_op = eval_stack()
    if not _print_mode:
        print(f'[Parser] ID: {n_id}; CONST: {n_const}; OP: {n_op}')
        print('[Parser]', _parsing_msg)
        _parsing_status = UNSET
        _parsing_msg = "(OK)"

''' statements
Parses strings in the language generated by the rule:
<statements> → <statement>| <statement><semi_colon><statements>
'''
def statements():
    global _next_token
    statement()
    if _next_token == SEMICOLON:
        lex()
        statements()


''' program
Parses strings in the language generated by the rule:
<program> -> <statements>
'''
def program():
    statements()
    # print evaluatin result before parsing ends
    if not _print_mode:
        eval_result = ''
        for name, value in _symbol_dic.items():
            eval_result += f' {name}: {value};'
        print('[Parser] Result ==>', eval_result[:-1])


# main driver
def main(path):
    global _file_content
    global _next_token
    global _file_pointer
    # Check whether file exists
    try:
        f = open(path, 'rb')
    except OSError:
        print("[system] Could not open/read file :", path)
        sys.exit()

    # Open the input data file    
    with open(path) as f:
        for line in f:
            _file_content += ' ' + line.strip() 
        
    _file_content = _file_content.replace(':=', '=')
    _file_content = _file_content.strip()

    print("[system] Start parsing")
    get_char()
    lex()
    program()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('path', help='input file path')
    parser.add_argument("-v", action='store_true')

    args = parser.parse_args()
    _print_mode = args.v
    if args.v:
        print('[system] Print next_token when everytime it changes')
    else:
        print('[system] Print parsing status and skip printing next_tokens')

    main(args.path)