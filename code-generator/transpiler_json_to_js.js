import escodegen from 'escodegen'

function createBinaryExpression(operator, left, right) {
    return {
        type: 'BinaryExpression',
        operator: operator,
        left: parseExpression(left),
        right: parseExpression(right),
    };
}

function parseExpression(expression) {
    if (Array.isArray(expression)) {
        const [operator, left, right] = expression;
        return createBinaryExpression(operator, left, right);
    } else if (typeof expression === 'number') {
        return {
            type: 'Literal',
            value: expression,
            raw: String(expression),
        };
    } else if (typeof expression === 'string') {
        return {
            type: 'Identifier',
            name: expression,
        };
    }
}

function generateCodeFromExpression(expression) {
    const ast = parseExpression(expression);
    return escodegen.generate(ast);
}

const jsonExpression = ['+', 3, ['*', 5, 'a']];
const generatedCode = generateCodeFromExpression(jsonExpression);

console.log(generatedCode);
