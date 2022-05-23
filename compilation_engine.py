from xml.dom import minidom

OP_SYMBOLS = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
UNARY_OP_SYMBOLS = ['-', '~']
KEYWORD_CONSTANTS = ['true', 'false', 'null', 'this']

class CompilationEngine:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.parser_root = minidom.Document()


    def _create_tag(self, parent_tag, child, child_text):
        child_tag = self.parser_root.createElement(child)
        parent_tag.appendChild(child_tag)

        if child_text is not None:
            child_text = self.parser_root.createTextNode(child_text)
            child_tag.appendChild(child_text)

        return child_tag


    def compile_class(self, token, token_type):
        class_tag = self.parser_root.createElement('class')
        self.parser_root.appendChild(class_tag)
        
        self._create_tag(class_tag, token_type, token)

        # className
        token, token_type = self.tokenizer.advance()
        self._create_tag(class_tag, token_type, token)

        # '{'
        token, token_type = self.tokenizer.advance()
        self._create_tag(class_tag, token_type, token)

        # classVarDec
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_class_var_dec(class_tag, token, token_type)

        while token != '}':
            # zero or more subroutineDec
            token, token_type = self.compile_subroutine(class_tag, token, token_type)
        
        self._create_tag(class_tag, token_type, token)


    def compile_class_var_dec(self, class_tag, token, token_type):
        if token not in ['static', 'field']:
            return token, token_type

        else:
            class_var_dec_tag = self._create_tag(class_tag, 'classVarDec', None)
            self._create_tag(class_var_dec_tag, token_type, token)

            # type
            token, token_type = self.tokenizer.advance()
            self._create_tag(class_var_dec_tag, token_type, token)

            # one or more varName
            while token != ';': 
                # varName
                token, token_type = self.tokenizer.advance()
                self._create_tag(class_var_dec_tag, token_type, token)

                # ',' or ';' 
                token, token_type = self.tokenizer.advance()
                self._create_tag(class_var_dec_tag, token_type, token)

            token, token_type = self.tokenizer.advance()
            return self.compile_class_var_dec(class_tag, token, token_type)


    def compile_subroutine(self, parent_tag, token, token_type):
        if token not in ['constructor', 'function', 'method']:
            # No more subroutines
            return token, token_type

        subroutine_tag = self.parser_root.createElement('subroutineDec')
        parent_tag.appendChild(subroutine_tag)
        self._create_tag(subroutine_tag, token_type, token)

        if token == 'function' or token == 'method':
            # type
            token, token_type = self.tokenizer.advance()
            self._create_tag(subroutine_tag, token_type, token)
        elif token == 'constructor':
            # className
            token, token_type = self.tokenizer.advance()
            self._create_tag(subroutine_tag, token_type, token)           

        # subroutineName
        token, token_type = self.tokenizer.advance()
        self._create_tag(subroutine_tag, token_type, token)

        # '('
        token, token_type = self.tokenizer.advance()
        self._create_tag(subroutine_tag, token_type, token)

        # Add empty text to tag to force minidom to create closing tag
        parameter_list_tag = self._create_tag(subroutine_tag, 'parameterList', '')

        # zero or more parameters
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_parameter_list(parameter_list_tag, token, token_type)

        # ')'
        self._create_tag(subroutine_tag, token_type, token)

        # '{' (start of subroutineBody)
        token, token_type = self.tokenizer.advance()
        subroutine_body_tag = self._create_tag(subroutine_tag, 'subroutineBody', None)
        self._create_tag(subroutine_body_tag, token_type, token)

        # zero or more varDec
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_var_dec(subroutine_body_tag, token, token_type)

        # statement
        statements_tag = self._create_tag(subroutine_body_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)

        # '}' (end of subroutineBody)
        self._create_tag(subroutine_body_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_parameter_list(self, parent_tag, token, token_type):
        if token == ')':
            # end of parameter list
            return token, token_type
        
        while token != ')':
            # type
            self._create_tag(parent_tag, token_type, token)
        
            # varName
            token, token_type = self.tokenizer.advance()   
            self._create_tag(parent_tag, token_type, token)   
            
            token, token_type = self.tokenizer.advance()
            if token == ',':
                # has another parameter
                self._create_tag(parent_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_var_dec(self, parent_tag, token, token_type):
        if token != 'var':
            # end of varDecs
            return token, token_type

        var_dec_tag = self._create_tag(parent_tag, 'varDec', None)
        self._create_tag(var_dec_tag, token_type, token)

        # type
        token, token_type = self.tokenizer.advance()
        self._create_tag(var_dec_tag, token_type, token)

        # one or more varNames
        while token != ';': 
            # varName
            token, token_type = self.tokenizer.advance()
            self._create_tag(var_dec_tag, token_type, token)

            # "," or ";" 
            token, token_type = self.tokenizer.advance()
            self._create_tag(var_dec_tag, token_type, token)

        # end of varDecs, or another varDec
        token, token_type = self.tokenizer.advance()
        return self.compile_var_dec(parent_tag, token, token_type)


    def compile_statements(self, parent_tag, token, token_type):
        if token == '}':
            # end of statements
            return token, token_type

        elif token == 'do':
            do_statement_tag = self._create_tag(parent_tag, 'doStatement', None)
            token, token_type = self.compile_do(do_statement_tag, token, token_type)
        elif token == 'let':
            let_statement_tag = self._create_tag(parent_tag, 'letStatement', None)
            token, token_type = self.compile_let(let_statement_tag, token, token_type)
        elif token == 'while':
            while_statement_tag = self._create_tag(parent_tag, 'whileStatement', None)
            token, token_type = self.compile_while(while_statement_tag, token, token_type)
        elif token == 'return':
            return_statement_tag = self._create_tag(parent_tag, 'returnStatement', None)
            token, token_type = self.compile_return(return_statement_tag, token, token_type)
        elif token == 'if':
            if_statement_tag = self._create_tag(parent_tag, 'ifStatement', None)
            token, token_type = self.compile_if(if_statement_tag, token, token_type)

        return self.compile_statements(parent_tag, token, token_type)


    def compile_do(self, parent_tag, token, token_type):
        # do    
        self._create_tag(parent_tag, token_type, token)

        # subroutineName or className (start of subroutineCall)
        token, token_type = self.tokenizer.advance() 
        self._create_tag(parent_tag, token_type, token)

        # '(' or '.'
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)

        if token == '(':
            # start expressionList
            token, token_type = self.tokenizer.advance()
            expression_list_tag = self._create_tag(parent_tag, 'expressionList', '')
            self.compile_expression_list(expression_list_tag, token, token_type)
        elif token == '.':
            # subroutineName
            token, token_type = self.tokenizer.advance()
            self._create_tag(parent_tag, token_type, token)

            # '('
            token, token_type = self.tokenizer.advance()            
            self._create_tag(parent_tag, token_type, token)

            # start of expressionList
            token, token_type = self.tokenizer.advance()
            expression_list_tag = self._create_tag(parent_tag, 'expressionList', '')
            token, token_type = self.compile_expression_list(expression_list_tag, token, token_type)

        # ')' (end of expressionList)
        self._create_tag(parent_tag, token_type, token)

        # ';' (end of doStatement)
        token, token_type = self.tokenizer.advance()           
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_let(self, parent_tag, token, token_type):
        # let
        self._create_tag(parent_tag, token_type, token)

        # varName
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)
        
        token, token_type = self.tokenizer.advance()
        # check for array indexing
        if token == '[':
            self._create_tag(parent_tag, token_type, token)
            expression_tag = self._create_tag(parent_tag, 'expression', None)
            token, token_type = self.tokenizer.advance()
            token, token_type = self.compile_expression(expression_tag, token, token_type)

            # ']' (end of array index)
            self._create_tag(parent_tag, token_type, token)
            token, token_type = self.tokenizer.advance()
        
        # '='
        self._create_tag(parent_tag, token_type, token)

        # expression
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_expression(expression_tag, token, token_type)

        # ';' (end of letStatement)
        self._create_tag(parent_tag, token_type, token)
        token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_while(self, parent_tag, token, token_type):
        # while
        self._create_tag(parent_tag, token_type, token)
        
        # '('
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)
        
        # expression
        token, token_type = self.tokenizer.advance()
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.compile_expression(expression_tag, token, token_type)

        # ')' (end of expression)
        self._create_tag(parent_tag, token_type, token)

        # '{'
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)

        # statements
        token, token_type = self.tokenizer.advance()
        statements_tag = self._create_tag(parent_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)

        # '}' (end of statements)
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_return(self, parent_tag, token, token_type):
        # return
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        if token != ';':
            # expression
            expression_tag = self._create_tag(parent_tag, 'expression', None)
            token, token_type = self.compile_expression(expression_tag, token, token_type)

        # ';' (end of returnStatement)          
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_if(self, parent_tag, token, token_type):
        # if
        self._create_tag(parent_tag, token_type, token)

        # '('
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)

        # expression
        token, token_type = self.tokenizer.advance()
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.compile_expression(expression_tag, token, token_type)

        # ')' (end of expression)
        self._create_tag(parent_tag, token_type, token)

        # '{'
        token, token_type = self.tokenizer.advance()
        self._create_tag(parent_tag, token_type, token)

        # statements
        token, token_type = self.tokenizer.advance()
        statements_tag = self._create_tag(parent_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)

        # '}' (end of statements)
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        if token == 'else':
            # else branch of ifStatement
            self._create_tag(parent_tag, token_type, token)
            
            # '{'
            token, token_type = self.tokenizer.advance()
            self._create_tag(parent_tag, token_type, token)

            # statements
            token, token_type = self.tokenizer.advance()
            statements_tag = self._create_tag(parent_tag, 'statements', None)
            token, token_type = self.compile_statements(statements_tag, token, token_type)

            # '}' (end of statements)
            self._create_tag(parent_tag, token_type, token)

            token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_expression(self, parent_tag, token, token_type):
        # term
        token, token_type = self.compile_term(parent_tag, token, token_type)

        # zero or more (op term) groupings
        while token in OP_SYMBOLS:
            self._create_tag(parent_tag, token_type, token)
            token, token_type = self.tokenizer.advance()
            token, token_type = self.compile_term(parent_tag, token, token_type)

        return token, token_type


    def compile_term(self, parent_tag, token, token_type):
        if token_type == 'symbol':
            if token == ';' or token == ')':
                # end of term
                return token, token_type

            elif token == '(':
                term_tag = self._create_tag(parent_tag, 'term', None)
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

                expression_tag = self._create_tag(term_tag, 'expression', None)
                token, token_type = self.compile_expression(expression_tag, token, token_type)

                # ')' (end of expression)
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

                return token, token_type
            
            elif token in UNARY_OP_SYMBOLS:
                term_tag = self._create_tag(parent_tag, 'term', None)
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()
                
                token, token_type = self.compile_term(term_tag, token, token_type)
                return token, token_type

            else:
                raise ValueError(f'Need to handle symbol: {token}')

        else:
            term_tag = self._create_tag(parent_tag, 'term', None)

        if token_type == 'identifier':
            # save and look-ahead
            initial_token, initial_token_type = token, token_type
            token, token_type = self.tokenizer.advance()

            if token == '.':
                # subroutine call
                self._create_tag(term_tag, initial_token_type, initial_token)
                self._create_tag(term_tag, token_type, token)

                # subroutine name
                token, token_type = self.tokenizer.advance()
                self._create_tag(term_tag, token_type, token)

                # '('
                token, token_type = self.tokenizer.advance()
                self._create_tag(term_tag, token_type, token)

                expression_list_tag = self._create_tag(term_tag, 'expressionList', '')
                token, token_type = self.tokenizer.advance()
                token, token_type = self.compile_expression_list(expression_list_tag, token, token_type)

                # ')' (end of expression list)
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()
                
            elif token == '[':
                # array indexing
                self._create_tag(term_tag, initial_token_type, initial_token)
                self._create_tag(term_tag, token_type, token)

                expression_tag = self._create_tag(term_tag, 'expression', None)
                token, token_type = self.tokenizer.advance()
                token, token_type = self.compile_expression(expression_tag, token, token_type)
                
                # end of array indexing
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

            elif token == ';' or token == ')' or token == ']' or token == ',':
                # identifier only
                self._create_tag(term_tag, initial_token_type, initial_token)
                return token, token_type

            elif token in OP_SYMBOLS:
                self._create_tag(term_tag, initial_token_type, initial_token)
                return token, token_type

            else:
                raise ValueError(f'Need to handle term with tokens: {initial_token} {token}')

        elif token_type == 'stringConstant':
            self._create_tag(term_tag, token_type, token)
            token, token_type = self.tokenizer.advance()

        elif token_type == 'integerConstant':
            self._create_tag(term_tag, token_type, token)
            token, token_type = self.tokenizer.advance()

        elif token in KEYWORD_CONSTANTS:
            self._create_tag(term_tag, token_type, token)
            token, token_type = self.tokenizer.advance()

        else:
            raise ValueError(
                'Unexpected token within term. '
                f'Token: {token} with token type: {token_type}'
            )

        return token, token_type


    def compile_expression_list(self, parent_tag, token, token_type):
        while True:
            if token == ')':
                # end of expressionList
                break

            expression_tag = self._create_tag(parent_tag, 'expression', None)
            token, token_type = self.compile_expression(expression_tag, token, token_type)
            
            if token == ',':
                # additional expression
                self._create_tag(parent_tag, token_type, token)
                token, token_type = self.tokenizer.advance()
        
        return token, token_type


    def wrtie_xml_file(self, output_file: str) -> None:
        xml_str = self.parser_root.toprettyxml(indent='  ')

        # remove xml header
        xml_str = '\n'.join([l for l in xml_str.splitlines()[1:]])

        # format empty tags in two lines instead of one
        empty_tag_lines = [l for l in xml_str.splitlines() if '><' in l]
        for l in empty_tag_lines:
            indentation = l.split('<', 1)[0]
            open_tag = l.split('><')[0]
            close_tag = l.split('><')[1]
            xml_str = xml_str.replace(l, open_tag+'>\n'+indentation+'<'+close_tag)

        # get rid of empty lines
        xml_str = '\n'.join([l for l in xml_str.splitlines() if not l.isspace()])

        # write to file
        with open(output_file, 'w') as f:
            f.write(xml_str)
