import os
import sys
import subprocess

from jack_tokenizer import JackTokenizer
from compilation_engine import CompilationEngine

class JackAnalyzer:
    def __init__(self, target_path):
        if os.path.isdir(target_path):
            self.jack_files = [
                os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith('.jack')
            ]
            if len(self.jack_files) == 0:
                raise ValueError('No jack files found in the target directory')
        elif os.path.isfile(target_path) and target_path.endswith('.jack'):
            self.jack_files = [target_path]
        else:
            raise ValueError('Target file is a not a jack file')
    

    def analyze(self):
        parser_output_files = []

        for jack_file in self.jack_files:
            target_dir = os.path.join(os.path.dirname(jack_file), 'target')
            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)
            basename = os.path.basename(jack_file).split('.')[0]

            tokenizer_output_file = os.path.join(target_dir, basename+'T.xml')
            parser_output_file = os.path.join(target_dir, basename+'.xml')

            tokenizer = JackTokenizer(jack_file)
            compilation_engine = CompilationEngine(tokenizer)

            # Writing the *T.xml file
            while tokenizer.has_more_tokens():
                token, token_type = tokenizer.advance()
                if token_type == 'stringConstant':
                    token = tokenizer.string_val()

                tokenizer.write_token_tag(token_type, token)

            tokenizer.write_xml_file(tokenizer_output_file)
            # Reinitialize current_token_index
            tokenizer.current_token_index = -1

            # Writing the analyzed *.xml file
            while tokenizer.has_more_tokens():
                token, token_type = tokenizer.advance()

                if token == 'class':
                    compilation_engine.compile_class(token, token_type)

            compilation_engine.wrtie_xml_file(parser_output_file)

            parser_output_files.append(parser_output_file)
        
        return parser_output_files


if __name__ == '__main__':
    target = sys.argv[1]

    if target == '--testall':
        test_tool = '../../../tools/TextComparer.sh'

        test_dirs = ['../ArrayTest', '../ExpressionLessSquare', '../Square']
        for dir in test_dirs:
            jack_analyzer = JackAnalyzer(dir)
            print(f'\nAnalyzing: {dir}')
            output_files = jack_analyzer.analyze()

            compare_files = [f.split('.jack')[0]+'.xml' for f in jack_analyzer.jack_files]
            for output, compare in zip(output_files, compare_files):
                print(f'\nRunning TextComparer on: {output}, {compare}')
                subprocess.run([test_tool, output, compare])

    else:
        jack_analyzer = JackAnalyzer(target)
        output_files = jack_analyzer.analyze()
