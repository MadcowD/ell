import * as path from 'path'
import ts from 'typescript'
import { Logger } from './_logger'

const logger = new Logger('ell-tsc')

const LMP_FUNCTION_EXPORT_NAMES = ['simple', 'complex']

// FIXME. remove this once we have a stable import
const ELL_MODULE_IDENTIFIERS = ['ell-ai' ]
const isEllModuleIdentifier = (identifier: string) =>
  identifier.includes('ell') || ELL_MODULE_IDENTIFIERS.includes(identifier)

/**
 * Get all import declarations in a source file
 * @param sourceFile
 * @returns
 */
const getAllImportDeclarations = (sourceFile: ts.SourceFile): ts.ImportDeclaration[] => {
  const importDeclarations: ts.ImportDeclaration[] = []

  const visit = (statements: ts.Statement[] | ts.NodeArray<ts.Statement>) => {
    statements.forEach((statement) => {
      if (ts.isImportDeclaration(statement)) {
        importDeclarations.push(statement)
      }
    })
  }
  visit(sourceFile.statements)
  return importDeclarations
}

/**
 * True if the source file imports `ell-ai`
 * @param sourceFile
 * @returns
 */
const hasEllImport = (sourceFile: ts.SourceFile): boolean => {
  const importDecls = getAllImportDeclarations(sourceFile)
  return importDecls.some(
    (decl) => ts.isStringLiteral(decl.moduleSpecifier) && isEllModuleIdentifier(decl.moduleSpecifier.text)
  )
}

export interface EllTSC {
  getAST(filePath: string): Promise<ts.SourceFile | undefined>
  getLMPsInFile(filePath: string): Promise<LMPDefinition[]>
  getFunctionSource(filePath: string, line: number, column: number): Promise<string | null>
}



export type LMPDefinitionType = 'simple' | 'complex'
export type LMPDefinition = {
  lmpDefinitionType: LMPDefinitionType
  lmpName: string
  fqn: string
  config: string
  source: string
  fn: string
  filepath: string
  line: number
  column: number
  endLine: number
  endColumn: number
}

export class EllTSC implements EllTSC {
  private program: ts.Program
  // maps filePath to LMPs
  private lmpCache: Map<string, LMPDefinition[]> = new Map()
  private tsconfigPath: string 
  constructor(rootDir: string = process.cwd()) {
    const configPath = ts.findConfigFile(rootDir, ts.sys.fileExists, 'tsconfig.json')
    if (!configPath) {
      throw new Error("Could not find a valid 'tsconfig.json'.")
    }
    this.tsconfigPath = configPath
    const configFile = ts.readConfigFile(configPath, ts.sys.readFile)
    const parsedCommandLine = ts.parseJsonConfigFileContent(configFile.config, ts.sys, path.dirname(configPath))

    this.program = ts.createProgram({
      rootNames: parsedCommandLine.fileNames,
      options: parsedCommandLine.options,
      projectReferences: parsedCommandLine.projectReferences,
    })
  }

  public namespace(filePath: string): string {
    const tsconfigDir = path.dirname(this.tsconfigPath)
    return filePath.replace(tsconfigDir, '').replace(/\//g, '.').replace(/\.ts$/g, '').slice(1)

  }
  public fqn(filepath:string,name:string): string {
    return `${this.namespace(filepath)}.${name}`
  }

  private getNodeAtPosition(sourceFile: ts.SourceFile, line: number, column: number): ts.Node | undefined {
    const position = ts.getPositionOfLineAndCharacter(sourceFile, line - 1, column - 1)

    let foundNode: ts.Node | undefined

    function visit(node: ts.Node) {
      if (node.getStart() <= position && position < node.getEnd()) {
        foundNode = node
        ts.forEachChild(node, visit)
      }
    }

    ts.forEachChild(sourceFile, visit)

    return foundNode
  }

  async getAST(filePath: string): Promise<ts.SourceFile | undefined> {
    return this.program.getSourceFile(filePath)
  }

  async getLMP(filePath: string, line: number, column: number): Promise<LMPDefinition | undefined> {
    let lmp: LMPDefinition | undefined
    const lmps = await this.getLMPsInFile(filePath)
    lmp = lmps.find((lmp) => lmp.line === line)
    if (!lmp) {
      lmp = lmps.find((lmp) => {
        const { line: startLine, endLine } = lmp
        return line >= startLine && line <= endLine
      })
      if (!lmp) {
        logger.error(`LMP not found for ${filePath}:${line}:${column}`)
        logger.error('lmps',lmps)
        // logger.debug(await this.getAST(filePath).then((x) => x?.getText()))
      }
    }
    return lmp
  }

  async getLMPsInFile(filePath: string): Promise<LMPDefinition[]> {
    if (this.lmpCache.has(filePath)) {
      return this.lmpCache.get(filePath)!
    }
    const sourceFile = await this.getAST(filePath)
    if (!sourceFile) {
      logger.info('Could not get ast for files', {
        availableFiles: this.program.getSourceFiles().map((f) => f.fileName),
      })
      throw new Error('Could not get AST for file ' + filePath)
    }

    // Fast path: no ell import
    if (!hasEllImport(sourceFile)) {
      return []
    }

    // The symbol `myEll` in any of:
    // import * as myEll from "ell-ai";
    // import myEll from "ell-ai";
    // import {default as myEll} from "ell-ai";
    //
    // Bound to `null` when
    // import {simple, complex} from "ell-ai";
    let ellModuleImportIdentifier: string | null = null

    const lmpDefinitions: LMPDefinition[] = []
    const lmpTypeToAlias: Record<LMPDefinitionType, string> = {
      simple: 'simple',
      complex: 'complex',
    }
    const aliasToLMPType: Record<string, LMPDefinitionType> = {
      simple: 'simple',
      complex: 'complex',
    }

    const getFqn = (filePath: string, name: string) => {
      return this.fqn(filePath, name)
    }

    function visitImportDeclaration(node: ts.ImportDeclaration) {
      if (ts.isStringLiteral(node.moduleSpecifier) && isEllModuleIdentifier(node.moduleSpecifier.text)) {
        if (node.importClause) {
          if (node.importClause.name) {
            // Default import
            ellModuleImportIdentifier = node.importClause.name.text
          } else if (node.importClause.namedBindings) {
            if (ts.isNamedImports(node.importClause.namedBindings)) {
              // Named imports
              node.importClause.namedBindings.elements.forEach((element) => {
                // We're using an alias bound to 'name' for something
                if (element.propertyName) {
                  if (element.propertyName.text === 'default') {
                    // default import
                    ellModuleImportIdentifier = element.name.text
                  } else if (
                    // If it's one of the lmp functions
                    LMP_FUNCTION_EXPORT_NAMES.includes(element.propertyName.text)
                  ) {
                    // Store the alias for future use
                    const alias = element.name.text
                    const lmpType = element.propertyName.text as LMPDefinitionType
                    lmpTypeToAlias[lmpType] = alias
                    aliasToLMPType[alias] = lmpType
                  }
                }
              })
            } else if (ts.isNamespaceImport(node.importClause.namedBindings)) {
              // Namespace import
              // todo. match on property access
              // import * as ell from "ell-ai";
              // ell.simple
              ellModuleImportIdentifier = node.importClause.namedBindings.name.text
            }
          }
        }
      }
    }
    function visitCallExpression(node: ts.CallExpression): Pick<LMPDefinition, 'lmpDefinitionType' | 'config' | 'fn'> | undefined {
      // Bare function call
      // mySimpleAlias()
      // myComplexAlias()
      if (ts.isIdentifier(node.expression)) {
        if (Object.keys(aliasToLMPType).includes(node.expression.text)) {
          if (node.arguments.length > 0) {
            const lmpFnConfig = node.arguments[0]
            const lmpFn = node.arguments[1]
            return {
              lmpDefinitionType: aliasToLMPType[node.expression.text],
              config: lmpFnConfig.getText(sourceFile),
              fn: lmpFn.getText(sourceFile),
            }
          }
        }
      }
      // Method/property access
      // myEll.mySimpleAlias()
      if (
        ts.isPropertyAccessExpression(node.expression) &&
        Object.keys(aliasToLMPType).includes(node.expression.name.text) &&
        ts.isIdentifier(node.expression.expression) &&
        node.expression.expression.text === ellModuleImportIdentifier
      ) {
        if (node.arguments.length > 0) {
          return {
            lmpDefinitionType: aliasToLMPType[node.expression.name.text],
            config: node.arguments[0].getText(sourceFile),
            fn: node.arguments[1].getText(sourceFile),
          }
        }
      }
    }

    function visit(node: ts.Node) {
      if (ts.isImportDeclaration(node)) {
        visitImportDeclaration(node)
        // } else if (ts.isCallExpression(node)) {
      } else if (ts.isVariableStatement(node)) {
        const declaration = node.declarationList.declarations[0]
        if (ts.isVariableDeclaration(declaration) && declaration.initializer) {
          if (ts.isCallExpression(declaration.initializer)) {
            const lmp = visitCallExpression(declaration.initializer)
            if (lmp) {
              if (ts.isIdentifier(declaration.name)) {
                const lmpName = declaration.name.text
                const { line, character } = sourceFile!.getLineAndCharacterOfPosition(node.getStart(sourceFile))
                const { line: endLine, character: endCharacter } = sourceFile!.getLineAndCharacterOfPosition(
                  node.getEnd()
                )

                lmpDefinitions.push({
                  lmpDefinitionType: lmp.lmpDefinitionType,
                  config: lmp.config,
                  fn: lmp.fn,
                  lmpName,
                  fqn: getFqn(filePath, lmpName),
                  source: node.getText(sourceFile),
                  filepath: filePath,
                  // Add 1 because TypeScript uses 0-based line numbers
                  line: line + 1,
                  column: character + 1,
                  endLine: endLine + 1,
                  endColumn: endCharacter + 1,
                })
              }
            }
          }
        }
      }

      ts.forEachChild(node, visit)
    }

    visit(sourceFile)

    this.lmpCache.set(filePath, lmpDefinitions)
    return lmpDefinitions
  }
}

// new EllTSC()
//   .getLMPsInFile(path.resolve("src/example.ts"))
//   .then(console.log);
