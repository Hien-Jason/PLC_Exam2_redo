import re
import pprint

#--------------------------------------------------------------------------#
#                            List of TOKENS                                #
#--------------------------------------------------------------------------# 
TOKENS = [
    (r'BEGIN',                      'BEGIN'),
    (r'END',                        'END'),
    (r'case',                       'case_key'),
    (r'itr',                        'itr_key'),
    (r'other',                      'other_key'),
    (r'times',                      'times_key'),
    (r'nat',                        'int_key'),
    (r'0|-?[1-9][0-9]*',          'lit_int8b'),
    (r'0|-?[1-9][0-9]*_b8',       'lit_int8b'),
    (r'0|-?[1-9][0-9]*_b4',       'lit_int4b'),
    (r'0|-?[1-9][0-9]*_b2',       'lit_int2b'),
    (r'0|-?[1-9][0-9]*_b1',       'lit_int1b'),
    (r'[a-zA-Z_]{1,7}',             'var_name'),
    (r'\.',                         'end_stmt'),
    (r'var',                        'declare_var'),
    (r'\+',                         'add'),
    (r'-',                          'subtract'),
    (r'\*',                         'multiply'),
    (r'/',                          'divide'),
    (r'%',                          'module'),
    (r'=',                          'assign'),
    (r'==',                         'EQ'),
    (r'!=',                         'NEQ'),
    (r'<',                          'LT'),
    (r'>',                          'GT'),
    (r'<=',                         'LTE'),
    (r'>=',                         'GTE'),
    (r'\(',                         'L_paren'),
    (r'\)',                         'R_paren'),
    (r'\[',                         'L_bracket'),
    (r'\]',                         'R_bracket'), 
]

BYTE_SPECIFIC_INT = [
    r'0|[1-9][0-9]*_b8',
    r'0|[1-9][0-9]*_b4',
    r'0|[1-9][0-9]*_b2',
    r'0|[1-9][0-9]*_b1'
]

#--------------------------------------------------------------------------#
#                            TOKEN                                        #
#--------------------------------------------------------------------------# 
class Token:
	def __init__(self, type, value=None):
		self.type = type
		self.value = value
        
	

	def __repr__(self):
		if self.value: return f'{self.value}:{self.type}'
		return f'{self.type}'



#--------------------------------------------------------------------------#
#                            LEXER                                         #
#--------------------------------------------------------------------------#
class Lexer:
    #read program (text file) and create a list of tokens   
    def tokenize(self, file):
        tokens = []
        
        with open (file, "r") as f:
            code = f.read()  
            print(code)
            start = re.search(r'BEGIN',code).span()[0]
            end = re.search(r'END',code).span()[1]
            #cut the text that's above BEGIN and below END
            code = code[start:end]
            #Create the list of tokens
            raw_tokens = code.split()                  
            print()

        #matches the tokens to its type using regular expressions
        for tok in raw_tokens:
            before = len(tokens)
            for pattern, type in TOKENS:
                if re.fullmatch(pattern,tok):
                    if pattern in BYTE_SPECIFIC_INT:
                        num = tok[0:len(tok)-3]
                        tokens.append(Token(type, num))
                    else:
                        tokens.append(Token(type, tok))
                    break   
            after = len(tokens)
            #Checks for tokens not added to tokens list
            if after == before:
                print('Lexical error: ',tok,' at index: ', raw_tokens.index(tok),' (invalid lexeme)')
                return None, 'Yes'
                
        return tokens, 'No'




#--------------------------------------------------------------------------#
#                            PARSER                                        #
#--------------------------------------------------------------------------#
class Parser: 
    
    #constructor for Parser
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_ind = -1
        self.current_tok = None
        self.syn_errors = []

    #function to move to next token in the list
    def to_next_tok(self):
        self.tok_ind += 1
        if self.tok_ind >= 0 and self.tok_ind < len(self.tokens):
            self.current_tok = self.tokens[self.tok_ind].type
        else:
            print (self.current_tok)
            print("no more tokens error")
            exit() 
        return self.current_tok


    #Starts checking the token list for syntax errors, calls statement_list to get started
    def check_syntax(self):
        if self.to_next_tok() == 'BEGIN':
            result = self.Statement_list()
            if result == 'Good':
                return "No"
            elif result == 'Bad':               
                return 'Yes'
        else:
            print("Error: Read in tokens before BEGIN")
            return "Yes"
        return 'Yes'
    

    #Recursively check all statements in the program (text file)
    def Statement_list(self):
        next = self.to_next_tok()
        self.tok_ind -= 1
        if next == "END":
            return "Good"       
        elif self.Statement() == 'Good':
            if self.Statement_list() == 'Good':
                return "Good"
            else:
                return 'END not found'
        else: 
            return 'Bad'
    

    #classify the current statement so the correct function will check its syntax 
    def Statement(self):
        key = self.to_next_tok()

        if key == 'int_key':
            if self.Var_decl()  == 'Good':
                return 'Good'
        elif key == 'var_name':
            if self.Var_assign()  == 'Good':
                return 'Good'
        elif key == 'case_key':
            if self.Case()  == 'Good':
                return 'Good'
        elif key == 'itr_key':
             if self.Itr()  == 'Good':
                return 'Good'
        else:
            return "Bad"

    
    #Checks if variable declaration statement has correct syntax
    def Var_decl(self):
        var = self.to_next_tok()
        stop = self.to_next_tok()
        if var == 'var_name' and stop == 'end_stmt':
            return "Good"
        else:
            return "Bad"
    

    #Checks if variable assignment/initialization statement has correct syntax
    def Var_assign(self):
        operator = self.to_next_tok()
        if operator == 'assign':           
            status = self.Math_expr()
            if status == 'Good':
                stop = self.to_next_tok()
                if stop == 'end_stmt':
                    return "Good"
                else:
                    print('Error: expecting "."')               
                    return "Bad"
        else:
            print('Error: expecting "="')               
            return "Bad"
    

    #Checks if case statement has correct syntax
    def Case(self):
        if self.Boolean_expr() == 'Good':
            next = self.to_next_tok()
            if next == "L_bracket":            
                if self.If_true() == 'Good':              
                    next = self.to_next_tok()
                    if next == 'other_key':
                        next = self.to_next_tok()
                        if next == "L_bracket":
                            if self.If_false() == 'Good':
                                if self.to_next_tok() == 'end_stmt':
                                    return 'Good'
                                else:
                                    self.tok_ind -= 1
                                    print('Syntax error: Expecting "."')
                                    return 'Bad'
                        else:
                            self.tok_ind -= 1                       
                            return 'Bad'                                    
                    elif next == 'end_stmt':                    
                        return 'Good'
                    else:
                        self.tok_ind -= 1
                        print('Syntax error: Expecting "."') 
                        return 'Bad' 
            else:
                self.tok_ind -= 1
                print('Expecting "["')
                return 'Bad'      
        else: 
            return 'Bad'          
    

    #Checks if Boolean expression has correct syntax
    def Boolean_expr(self):
        rela_op = ["EQ", "NEQ", "LT", "GT", "LTE", "GTE"]
        next = self.to_next_tok()
        if next == 'L_paren':
            if self.Number() == 'Good':
                if self.to_next_tok() in rela_op:
                    if self.Number() == 'Good':
                        if self.to_next_tok() == 'R_paren':
                            return "Good"
                        else:
                            self.tok_ind -= 1
                            return 'bad'
                else:
                    self.tok_ind -= 1 
                    return 'bad'
        else:
            self.tok_ind -= 1
            return "Bad"

        return 'Bad'


    #Recursively CHecks all statments in case's (if statment) execution block for syntax errors
    def If_true(self):
        next = self.to_next_tok()
        if next == "R_bracket":         
            return 'Good'
        self.tok_ind -= 1
        if self.Statement() == 'Good':                             
            if self.If_true() == 'Good':
                return 'Good'        
        
        print('Syntax error at If_true')
        return 'Bad'
    

    #Recursively CHecks all statments in other's (else statment) execution block for syntax errors 
    def If_false(self):
        next = self.to_next_tok()
        if next == "R_bracket":         
            return 'Good'
        self.tok_ind -= 1
        if self.Statement() == 'Good':                             
            if self.If_false() == 'Good':
                return 'Good' 
        print('Syntax error in if_false execution block')             
        return 'Bad'
        
    
    
    #Checks grammar of itr (for loop) statement
    def Itr(self):
        if self.Number() == 'Good':
            if self.to_next_tok() == 'times_key':
                next = self.to_next_tok()
                if next == 'L_bracket':
                    if self.To_repeat() == 'Good':
                        if self.to_next_tok() == 'end_stmt':
                            return 'Good'
                        else:                
                            self.tok_ind -= 1
                            print('Syntax error: "." expected')
                            return 'Bad'
                else:                
                    self.tok_ind -= 1
                    print('Syntax error: "[" expected')
                    return 'Bad'
            else:                
                self.tok_ind -= 1
                print('Syntax error: "times" expected')
                return 'Bad'
        return 'Syntax error at Itr'
    

    #Recursively Checks all statements in itr's execution block for syntax errors
    def To_repeat(self):
        next = self.to_next_tok()
        if next == "R_bracket":         
            return 'Good'
        self.tok_ind -= 1
        if self.Statement() == 'Good':                             
            if self.To_repeat() == 'Good':
                return 'Good'                        
        print('Syntax error at To_repeat')
        return 'Bad'
    

    #Checks if mathmetical expression's syntax is correct
    def Math_expr(self):
        operator = ["add", "subtract", "multiply", "divide", "module"]
        if self.Term() == "Good":
            if self.to_next_tok() in operator:
                if self.Math_expr() == 'Good':
                    return "Good"
            self.tok_ind -= 1
            return 'Good'
            
        return 'Bad'


    #Checks if term's syntax is correct ()
    def Term(self):
        operator = ["add", "subtract", "multiply", "divide", "module"]
        if self.Factor() == "Good":
            return "Good"
        elif self.to_next_tok() in operator:
            if self.Factor() == 'Good':
                return 'Good' 
        self.tok_ind -= 1          
        return 'Bad'


    #Checks the operand's syntax (number, expression in parentheses)
    def Factor(self):
        if self.Number() == 'Good':
            return 'Good'
        elif self.to_next_tok() == 'L_paren':
            if self.Math_expr() == 'Good':
                if self.to_next_tok() == 'R_paren':                    
                    return 'Good'
                self.tok_ind -= 1
        self.tok_ind -= 1
        return 'Bad'


    #Check if the next token is a number (literal + variable)
    def Number(self):
        nums = [
            'lit_int8b', 
            'lit_int4b', 
            'lit_int2b', 
            'lit_int1b', 
            'var_name'
        ]
        next = self.to_next_tok()
        if next in nums :
            return 'Good'
        self.tok_ind -= 1
        return 'bad'

    



#--------------------------------------------------------------------------#
#                            Run time code                                 #
#--------------------------------------------------------------------------#

mylex = Lexer()

#token list created
mytokens, lex_stat = mylex.tokenize("no_error_test1.txt")



if lex_stat == 'No':
    myParse = Parser(mytokens)
    #yes if there is a syntax error, no if there are no errors
    syntax_stat = myParse.check_syntax()
    print ('Lexical error: ',lex_stat)
    print ('Syntax error: ', syntax_stat)
    if syntax_stat == 'Yes':
        exit()
    print('\ntoken list: \n')
    pprint.pprint(mytokens)

  
    
    
    













