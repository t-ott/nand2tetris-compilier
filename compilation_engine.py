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

        token, token_type = self.tokenizer.advance()
        assert token_type == 'identifier', \
            f'Invalid class identifier "{token}" with ' \
            'type: {token_type}"'
        self._create_tag(class_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token_type == 'symbol', \
            'Error in class definition, expecting symbol ' \
            f'but got token "{token}" with type: {token_type}'
        self._create_tag(class_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_class_var_dec(class_tag, token, token_type)

        while token != '}':
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
            assert token_type == 'keyword' or token_type == 'identifier', \
                'Error in classVarDec, expecting keyword or identifier but ' \
                f'got token "{token}" with type: {token_type}.'
            self._create_tag(class_var_dec_tag, token_type, token)

            # one or more varNames
            while token != ';': 
                # varName
                token, token_type = self.tokenizer.advance()
                assert token_type == 'identifier', \
                    'Error in classVarDec, expecting identifier but ' \
                    f'got token "{token}" with type: {token_type}.'
                self._create_tag(class_var_dec_tag, token_type, token)

                # "," or ";" 
                token, token_type = self.tokenizer.advance()
                assert token_type == 'symbol', \
                    'Error in classVarDec, expecting symbol but ' \
                    f'got token "{token}" with type: {token_type}.'
                self._create_tag(class_var_dec_tag, token_type, token)
            
            # self._create_tag(class_var_dec_tag, token_type, token)

            token, token_type = self.tokenizer.advance()
            return self.compile_class_var_dec(class_tag, token, token_type)


    def compile_subroutine(self, parent_tag, token, token_type):
        # if self.tokenizer.current_token not in ['constructor', 'function', 'method']:
        #     # No more subroutines
        #     return token, token_type
        
        if token not in ['constructor', 'function', 'method']:
            # No more subroutines
            return token, token_type

        subroutine_tag = self.parser_root.createElement('subroutineDec')
        parent_tag.appendChild(subroutine_tag)
        self._create_tag(subroutine_tag, token_type, token)

        if token == 'function' or token == 'method':
            # type
            token, token_type = self.tokenizer.advance()
            assert token_type == 'keyword', \
                'Error in subroutine definition, expecting ' \
                f'keyword but got token "{token}" with type: ' \
                f'{token_type}.'
            self._create_tag(subroutine_tag, token_type, token)
        elif token == 'constructor':
            token, token_type = self.tokenizer.advance()
            assert token_type == 'identifier', \
                'Error in subroutine definition, expecting ' \
                f'identifier but got token "{token}" with type: ' \
                f'{token_type}.'
            self._create_tag(subroutine_tag, token_type, token)           

        token, token_type = self.tokenizer.advance()
        assert token_type == 'identifier', \
            'Error in subroutine definition, expecting ' \
            f'identifier but got token "{token}" with type: ' \
            f'{token_type}.'
        self._create_tag(subroutine_tag, token_type, token)
        

        token, token_type = self.tokenizer.advance()
        assert token_type == 'symbol', \
             'Error in subroutine definition, expecting ' \
            f'symbol but got token "{token}" with type: ' \
            f'{token_type}.'
        self._create_tag(subroutine_tag, token_type, token)

        # add empty text to tag to force minidom to create closing tag
        parameter_list_tag = self._create_tag(subroutine_tag, 'parameterList', '')

        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_parameter_list(parameter_list_tag, token, token_type)

        assert token_type == 'symbol', \
            'Error in subroutine definition following ' \
            'parameterList, expecting symbol but got ' \
            f'token "{token}" with type: {token_type}.'
        self._create_tag(subroutine_tag, token_type, token)

        # start of subroutineBody
        token, token_type = self.tokenizer.advance()
        assert token_type == 'symbol', \
            'Error in subroutine definition following ' \
            'parameterList, expecting symbol but got ' \
            f'token "{token}" with type: {token_type}.'

        subroutine_body_tag = self._create_tag(subroutine_tag, 'subroutineBody', None)
        self._create_tag(subroutine_body_tag, token_type, token)

        # start of varDec(s)
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_var_dec(subroutine_body_tag, token, token_type)

        # start of statement(s)
        statements_tag = self._create_tag(subroutine_body_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)

        assert token == '}', \
            'Error at end of subRoutine, expecting token "}" but got ' \
            f'token "{token}" with type {token_type}'
        self._create_tag(subroutine_body_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_parameter_list(self, parent_tag, token, token_type):
        if token == ')':
            # end of parameter list
            return token, token_type
        
        while token != ')':
            assert token_type == 'keyword', \
                'Error in parameterList, expecting token type "keyword" but ' \
                f'got token {token} with type {token_type}'
            self._create_tag(parent_tag, token_type, token)
        
            token, token_type = self.tokenizer.advance()
            assert token_type == 'identifier', \
                'Error at end of parameterList, expecting token type "identifier" but ' \
                f'got token "{token}" with type {token_type}'     
            self._create_tag(parent_tag, token_type, token)   
            
            token, token_type = self.tokenizer.advance()
            if token == ',':
                # has another parameter
                self._create_tag(parent_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_var_dec(self, parent_tag, token, token_type):
        if token != 'var':
            # end of var decs
            return token, token_type

        var_dec_tag = self._create_tag(parent_tag, 'varDec', None)
        self._create_tag(var_dec_tag, token_type, token)

        # type
        token, token_type = self.tokenizer.advance()
        assert token_type == 'identifier' or token_type == 'keyword', \
            'Error in varDec, expecting identifier but ' \
            f'got token "{token}" with type: {token_type}.'
        self._create_tag(var_dec_tag, token_type, token)

        # one or more varNames
        while token != ';': 
            # varName
            token, token_type = self.tokenizer.advance()
            assert token_type == 'identifier', \
                'Error in varDec, expecting identifier but ' \
                f'got token "{token}" with type: {token_type}.'
            self._create_tag(var_dec_tag, token_type, token)

            # "," or ";" 
            token, token_type = self.tokenizer.advance()
            assert token_type == 'symbol', \
                'Error in varDec, expecting symbol but ' \
                f'got token "{token}" with type: {token_type}.'
            self._create_tag(var_dec_tag, token_type, token)

        # end of varDecs, or another varDec
        token, token_type = self.tokenizer.advance()
        return self.compile_var_dec(parent_tag, token, token_type)


    def compile_statements(self, parent_tag, token, token_type):

        # print(f'\nWorking on statement starting with token: {token}')

        # if token == '}' or token == ';' or token == ')':
        if token == '}':
            # TODO: Check that this is actually correct...
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
        assert token == 'do', \
            'Error in do statement, expecting token "do" but '\
            f'got token "{token}" with type: {token_type}'          
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token_type == 'identifier', \
            'Error in do statement, expecting identifier but '\
            f'got token "{token}" with type: {token_type}'    
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token == '(' or token == '.', \
            'Error in do statement, expecting "(" or "." but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        if token == '(':
            token, token_type = self.tokenizer.advance()
            expression_list_tag = self._create_tag(parent_tag, 'expressionList', '')
            self.compile_expression_list(expression_list_tag, token, token_type)
        elif token == '.':
            token, token_type = self.tokenizer.advance()
            assert token_type == 'identifier', \
                'Error in do statement, expecting identifier but '\
                f'got token "{token}" with type: {token_type}'
            self._create_tag(parent_tag, token_type, token)

            token, token_type = self.tokenizer.advance()
            assert token == '(', \
                'Error in do statement, expecting "(" but ' \
                f'got token "{token}" with type: {token_type}'              
            self._create_tag(parent_tag, token_type, token)

            token, token_type = self.tokenizer.advance()
            expression_list_tag = self._create_tag(parent_tag, 'expressionList', '')
            token, token_type = self.compile_expression_list(expression_list_tag, token, token_type)

        # end of expressionList
        assert token == ')', \
            'Error in do statement, expecting ")" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token == ';', \
            'Error in do statement, expecting ";" but ' \
            f'got token "{token}" with type: {token_type}'              
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_let(self, parent_tag, token, token_type):
        assert token == 'let', \
            'Error in let statement, expecting token "let" but '\
            f'got token "{token}" with type: {token_type}'
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
            assert token == ']', \
                'Error in let statement, expecting token "]" but ' \
                f'got token "{token} with type: {token_type}'
            self._create_tag(parent_tag, token_type, token)
            token, token_type = self.tokenizer.advance()
        
        assert token == '=', \
            'Error in let statement, expecting token "=" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        # expression
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.tokenizer.advance()
        token, token_type = self.compile_expression(expression_tag, token, token_type)

        assert token == ';', \
            'Error in let statement, expecting token ";" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)
        token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_while(self, parent_tag, token, token_type):
        assert token == 'while', \
            'Error in while statement, expecting token "while" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)
        
        token, token_type = self.tokenizer.advance()
        assert token == '(', \
            'Error in while statement, expecting token "(" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)
        
        token, token_type = self.tokenizer.advance()
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.compile_expression(expression_tag, token, token_type)
        assert token == ')', \
            'Error in while statement, expecting token ")" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token == '{', \
            'Error in while statement, expecting token "{" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        statements_tag = self._create_tag(parent_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)

        # token, token_type = self.tokenizer.advance()
        assert token == '}', \
            'Error in while statement, expecting token "}" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()

        return token, token_type


    def compile_return(self, parent_tag, token, token_type):
        assert token == 'return', \
            'Error in return statement, expecting token "return" but ' \
            f'got token "{token}" with type: {token_type}' 
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        if token != ';':
            expression_tag = self._create_tag(parent_tag, 'expression', None)
            token, token_type = self.compile_expression(expression_tag, token, token_type)
        assert token == ';', \
            'Error in return statement, expecting token ";" but ' \
            f'got token "{token}" with type: {token_type}'             
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        return token, token_type


    def compile_if(self, parent_tag, token, token_type):
        assert token == 'if', \
            'Error in if statement, expecting token "if" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token == '(', \
            'Error in if statement, expecting token "(" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        expression_tag = self._create_tag(parent_tag, 'expression', None)
        token, token_type = self.compile_expression(expression_tag, token, token_type)
        assert token == ')', \
            'Error in if statement, expecting token ")" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        assert token == '{' , \
            'Error in if statement, expecting token "{" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        statements_tag = self._create_tag(parent_tag, 'statements', None)
        token, token_type = self.compile_statements(statements_tag, token, token_type)
        assert token == '}', \
            'Error in if statement, expecting token "}" but ' \
            f'got token "{token}" with type: {token_type}'
        self._create_tag(parent_tag, token_type, token)

        token, token_type = self.tokenizer.advance()
        if token == 'else':
            # print('In else branch...')

            self._create_tag(parent_tag, token_type, token)
            
            token, token_type = self.tokenizer.advance()
            assert token == '{', \
                'Error in else branch of if statement, expecting token "{" but ' \
                f'got token "{token}" with type: {token_type}'
            self._create_tag(parent_tag, token_type, token)

            token, token_type = self.tokenizer.advance()
            statements_tag = self._create_tag(parent_tag, 'statements', None)
            token, token_type = self.compile_statements(statements_tag, token, token_type)
            assert token == '}', \
                'Error in else branch of if statement, expecting token "}" but ' \
                f'got token "{token}" with type: {token_type}'
            self._create_tag(parent_tag, token_type, token)

            token, token_type = self.tokenizer.advance()

        return token, token_type

    def compile_expression(self, parent_tag, token, token_type):

        token, token_type = self.compile_term(parent_tag, token, token_type)

        while token in OP_SYMBOLS:
            self._create_tag(parent_tag, token_type, token)
            token, token_type = self.tokenizer.advance()
            token, token_type = self.compile_term(parent_tag, token, token_type)

        return token, token_type


    def compile_term(self, parent_tag, token, token_type):

        if token_type == 'symbol':
            if token == ';':
                # print('Done with term because of symbol ";"')
                return token, token_type
            elif token == ')':
                # print('Done with term because of symbol ")"')
                return token, token_type
            elif token == '(':
                term_tag = self._create_tag(parent_tag, 'term', None)
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

                expression_tag = self._create_tag(term_tag, 'expression', None)
                token, token_type = self.compile_expression(expression_tag, token, token_type)
                assert token == ')', \
                    'Error in term parsing, expecting token ")" with ' \
                    f'type "symbol" but got token "{token}" with type: ' \
                    f'{token_type}'

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
                print(f'In compile_term(), need to handle symbol {token}')
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

                token, token_type = self.tokenizer.advance()
                assert token_type == 'identifier', \
                    'Error in term parsing, expecting subroutineName with ' \
                    f'type "identifier" but got token "{token}" with type: ' \
                    f'{token_type}'
                self._create_tag(term_tag, token_type, token)

                token, token_type = self.tokenizer.advance()
                assert token == '(', \
                    'Error in term parsing, expecting token "(" but got ' \
                    f'token "{token}" with type: {token_type}'
                self._create_tag(term_tag, token_type, token)

                expression_list_tag = self._create_tag(term_tag, 'expressionList', '')
                token, token_type = self.tokenizer.advance()
                token, token_type = self.compile_expression_list(expression_list_tag, token, token_type)

                assert token == ')', \
                    'Error in term parsing, expecting token ")" but got ' \
                    f'token "{token}" with tpe: {token_type}'
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()
                
            elif token == '[':
                # array indexing
                self._create_tag(term_tag, initial_token_type, initial_token)
                self._create_tag(term_tag, token_type, token)

                expression_tag = self._create_tag(term_tag, 'expression', None)
                token, token_type = self.tokenizer.advance()
                token, token_type = self.compile_expression(expression_tag, token, token_type)
                assert token == ']', \
                    'Error in term parsing, expecting token "]" but got ' \
                    f'token "{token}" with tpe: {token_type}'
                self._create_tag(term_tag, token_type, token)
                token, token_type = self.tokenizer.advance()

            elif token == ';' or token == ')' or token == ']' or token == ',':
                # identifier only
                self._create_tag(term_tag, initial_token_type, initial_token)
                return token, token_type
                # self._create_tag(term_tag, token_type, token)

            elif token in OP_SYMBOLS:
                self._create_tag(term_tag, initial_token_type, initial_token)
                return token, token_type

            else:
                print(f'NEED TO HANDLE THIS TERM SITUATION. TOKEN: {token} TOKEN_TYPE: {token_type}')

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
            print(f'NEED TO HANDLE THIS TERM. TOKEN: "{token}" WITH TOKEN_TYPE: {token_type}')

        return token, token_type


    def compile_expression_list(self, parent_tag, token, token_type):
        while True:
            if token == ')':
                break

            expression_tag = self._create_tag(parent_tag, 'expression', None)
            token, token_type = self.compile_expression(expression_tag, token, token_type)
            
            if token == ',':
                # Additional expression
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

        with open(output_file, 'w') as f:
            f.write(xml_str)