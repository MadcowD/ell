const ts = require("typescript");
const path = require("path");

function parseTypeScriptModule(filePath) {
  const program = ts.createProgram([filePath], {});
  const sourceFile = program.getSourceFile(filePath);
  const checker = program.getTypeChecker();

  const moduleInfo = {
    name: path.parse(sourceFile.fileName).name,
    documentation: ts.displayPartsToString(
      sourceFile.symbol?.getDocumentationComment(checker)
    ),
    functions: [],
    classes: [],
    interfaces: [],
  };

  function visit(node) {
    if (ts.isFunctionDeclaration(node)) {
      moduleInfo.functions.push(parseFunction(node));
    } else if (ts.isClassDeclaration(node)) {
      moduleInfo.classes.push(parseClass(node));
    } else if (ts.isInterfaceDeclaration(node)) {
      moduleInfo.interfaces.push(parseInterface(node));
    }

    ts.forEachChild(node, visit);
  }

  function parseFunction(node) {
    return {
      name: node.name?.text,
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
      parameters: node.parameters.map(parseParameter),
      returnType: checker.typeToString(checker.getTypeAtLocation(node.type)),
    };
  }

  function parseClass(node) {
    return {
      name: node.name?.text,
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
      properties: node.members
        .filter(ts.isPropertyDeclaration)
        .map(parseProperty),
      methods: node.members.filter(ts.isMethodDeclaration).map(parseMethod),
    };
  }

  function parseInterface(node) {
    return {
      name: node.name?.text,
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
      properties: node.members
        .filter(ts.isPropertySignature)
        .map(parseProperty),
    };
  }

  function parseProperty(node) {
    return {
      name: node.name.text,
      type: checker.typeToString(checker.getTypeAtLocation(node)),
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
    };
  }

  function parseMethod(node) {
    return {
      name: node.name.text,
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
      parameters: node.parameters.map(parseParameter),
      returnType: checker.typeToString(checker.getTypeAtLocation(node.type)),
    };
  }

  function parseParameter(node) {
    return {
      name: node.name.text,
      type: checker.typeToString(checker.getTypeAtLocation(node)),
      documentation: ts.displayPartsToString(
        node.symbol?.getDocumentationComment(checker)
      ),
    };
  }

  visit(sourceFile);
  return moduleInfo;
}

try {
  const filePath = process.argv[2];
  const moduleInfo = parseTypeScriptModule(filePath);
  console.log(JSON.stringify(moduleInfo, null, 2));
} catch (error) {
  console.error(error);
}
