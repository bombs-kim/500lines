import * as acorn from 'acorn'
import * as walk from 'acorn-walk'
import escodegen from 'escodegen'


function classToFunction(ast) {
  const newBody = [];

  walk.simple(ast, {
    ClassDeclaration: (node) => {
      // Create the constructor function
      const constructor = node.body.body.find(
        (method) => method.kind === 'constructor'
      );

      if (constructor) {
        const constructorFunction = {
          type: 'FunctionDeclaration',
          id: node.id,
          params: constructor.value.params,
          body: constructor.value.body,
        };
        newBody.push(constructorFunction);
      }

      // Create prototype methods
      node.body.body.forEach((method) => {
        if (method.kind !== 'constructor') {
          const prototypeAssignment = {
            type: 'ExpressionStatement',
            expression: {
              type: 'AssignmentExpression',
              operator: '=',
              left: {
                type: 'MemberExpression',
                computed: false,
                object: {
                  type: 'MemberExpression',
                  computed: false,
                  object: {
                    type: 'Identifier',
                    name: node.id.name,
                  },
                  property: {
                    type: 'Identifier',
                    name: 'prototype',
                  },
                },
                property: {
                  type: 'Identifier',
                  name: method.key.name,
                },
              },
              right: {
                type: 'FunctionExpression',
                params: method.value.params,
                body: method.value.body,
              },
            },
          };
          newBody.push(prototypeAssignment);
        }
      });
    },
  });

  return newBody;
}

function convertClassToES5(code) {
  const ast = acorn.parse(code, { ecmaVersion: 2020 });

  // Modify the AST to convert classes
  const body = classToFunction(ast);

  // Replace the original body with the transformed body
  ast.body = body;

  // Generate the transformed code
  const newCode = escodegen.generate(ast);
  return newCode;
}

// Example usage
const inputCode = `
class Example {
  constructor(a, b) {
    this.a = a;
    this.b = b;
  }

  sum() {
    return this.a + this.b;
  }

  printSum() {
    console.log(this.sum());
  }
}
`;

const outputCode = convertClassToES5(inputCode);
console.log(outputCode);
