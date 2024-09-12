import * as acorn from 'acorn'
import * as walk from 'acorn-walk'
import escodegen from 'escodegen'


// To handle the transformation where only property accesses are modified
// to use the getattr function (excluding method calls like console.log),
// we'll need to walk through the AST, differentiate between simple
// property accesses and method calls, and modify only the former.


// The global attribute access handler that will be inserted
const getterFunction = `
const getattr = (obj, prop) => {
    let val = obj[prop];
    if (typeof val == "undefined") {
        return obj.__getattr__(prop);
    }
    return val;
};`;

// Source code
const sourceCode = `
class A {
    constructor(celsius) {
        this.celsius = celsius;
    }

    __getattr__(prop) {
        if (prop == "fahrenheit") {
            return this.celsius * 9 / 5 + 32;
        }
    }
}

const a = new A(22);
console.log(a.celsius);
console.log(a.fahrenheit);
`;

// Step 1: Parse the source code into an AST
const ast = acorn.parse(sourceCode, { ecmaVersion: 2020, sourceType: "module" });

// Step 2: Walk through the AST and transform property accesses
walk.ancestor(ast, {
  MemberExpression(node, state, ancestors) {
    const parent = ancestors[ancestors.length - 2];

    if (parent.type == "AssignmentExpression") {
      return
    }

    if (parent.type == "CallExpression" && parent.callee == node) {
      return
    }

    // console.log(parent.type);

    // Transform each member expression (e.g., a.celsius) to getattr(a, "celsius")
    node.type = "CallExpression";
    node.callee = {
      type: "Identifier",
      name: "getattr"
    };
    node.arguments = [
      node.object, // The object being accessed (e.g., a)
      {
        type: "Literal",
        value: node.property.name, // The property being accessed (e.g., "celsius")
      }
    ];
  }
});

// Step 3: Generate the transpiled code from the modified AST
const transpiledCode = getterFunction + "\n" + escodegen.generate(ast);

// Output the transpiled code
console.log(transpiledCode);
