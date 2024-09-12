import * as acorn from 'acorn'
import * as walk from 'acorn-walk'
import escodegen from 'escodegen'

function isEmptyConstructor(node) {
    return (
        node.type === 'MethodDefinition' &&
        node.kind === 'constructor' &&
        node.value.body.body.length === 0
    );
}

function removeEmptyConstructors(sourceCode) {
    // Parse the code to AST
    const ast = acorn.parse(sourceCode, { ecmaVersion: 2020 });

    // Traverse the AST
    walk.simple(ast, {
        ClassBody: (node) => {
            // Filter out empty constructors
            node.body = node.body.filter(method => !isEmptyConstructor(method));
        }
    });

    // Generate the modified code back from the AST
    const generatedCode = escodegen.generate(ast);
    return generatedCode;
}

const inputCode = `
class Example {
  constructor () {
  }

  someMethod () {
    console.log('some method');
  }
}
`;

const outputCode = removeEmptyConstructors(inputCode);
console.log(outputCode);
