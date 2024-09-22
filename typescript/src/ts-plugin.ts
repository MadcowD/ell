import * as ts from 'typescript'
import { EllTSC } from './tsc'

// todo. this can be used for compile only users.
// we can write LMPs to a well-known file and look them up at runtime.
// at runtime we won't have access to the typescript source code, but we hope
// to have access to source maps so that we can match lmp functions that we are
// executing in to what we record at compile time by line numbers and file names
export function ellTypescriptPlugin(program: ts.Program) {
  return {
    before(ctx: ts.TransformationContext) {
      const ell = new EllTSC()
      // here we need the project root
      return (sourceFile: ts.SourceFile) => {
        const visitor = (node: ts.Node): ts.Node => {
          // if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) || ts.isFunctionExpression(node) || ts.isArrowFunction(node)) {
          //   const functionName = ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node) ? node.name?.getText() : 'anonymous';
          //   const sourceCode = node.getText(sourceFile);
          //   console.log(`Function ${functionName}:\n${sourceCode}\n`);
          // }
          // return ts.visitEachChild(node, visitor, ctx);
          ell.getLMPsInFile(sourceFile.fileName).then((lmp) => {
            console.log(lmp)
          })
          return node
        }

        return ts.visitNode(sourceFile, visitor)
      }
    },
  }
}
