import * as path from 'path'
import ts from 'typescript'
import * as z from 'zod'
import { Logger } from './_logging'

const logger = new Logger('ell.tsc')

const LMP_FUNCTION_EXPORT_NAMES = ['simple', 'complex', 'tool']

const ELL_MODULE_IDENTIFIERS = ['ell-ai']
const isEllModuleIdentifier = (identifier: string) =>
  ELL_MODULE_IDENTIFIERS.includes(identifier)

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

export type LMPDefinitionType = 'simple' | 'complex' | 'tool'
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
  inputSchema?: z.ZodTypeAny
  outputSchema?: z.ZodTypeAny
}

export class EllTSC implements EllTSC {
  private program: ts.Program
  // maps filePath to LMPs
  private lmpCache: Map<string, LMPDefinition[]> = new Map()
  private tsconfigPath: string | undefined

  constructor(rootDir?: string) {
    if (!rootDir) {
      try {
        rootDir = process.cwd()
      } catch (e) {
        logger.error('Could not initialize tsc', { error: e })
        throw new Error('Could not initialize tsc')
      }
    }
    // todo. try to get the user config file...?
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
    if (!this.tsconfigPath) {
      return ''
    }
    const tsconfigDir = path.dirname(this.tsconfigPath)
    return filePath.replace(tsconfigDir, '').replace(/\//g, '.').replace(/\.ts$/g, '').slice(1)
  }

  public fqn(filepath: string, name: string): string {
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
        logger.error('lmps', lmps)
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
      tool: 'tool',
    }
    const aliasToLMPType: Record<string, LMPDefinitionType> = {
      simple: 'simple',
      complex: 'complex',
      tool: 'tool',
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

    function visitCallExpression(
      node: ts.CallExpression
    ): Pick<LMPDefinition, 'lmpDefinitionType' | 'config' | 'fn' | 'inputSchema' | 'outputSchema'> | undefined {
      // Bare function call
      // mySimpleAlias()
      // myComplexAlias()
      // myToolAlias()
      if (ts.isIdentifier(node.expression)) {
        if (Object.keys(aliasToLMPType).includes(node.expression.text)) {
          const lmpType = aliasToLMPType[node.expression.text]
          if (node.arguments.length > 0) {
            // todo. maybe allow config in second argument to ell.tool
            const config = lmpType === 'tool' ? '' : node.arguments[0].getText(sourceFile)
            const fn = (lmpType === 'tool' ? node.arguments[0] : node.arguments[1]).getText(sourceFile)
            if (lmpType === 'tool') {
              const { inputSchema, outputSchema } = getToolSchema(
                node.arguments[0] as ts.ArrowFunction | ts.FunctionExpression,
                checker
              )
              return {
                lmpDefinitionType: lmpType,
                config,
                fn,
                inputSchema,
                outputSchema,
              }
            }
            return {
              lmpDefinitionType: lmpType,
              config,
              fn,
            }
          }
        }
      }
      // Method/property access
      // myEll.mySimpleAlias()
      // myEll.myToolAlias()
      if (
        ts.isPropertyAccessExpression(node.expression) &&
        Object.keys(aliasToLMPType).includes(node.expression.name.text) &&
        ts.isIdentifier(node.expression.expression) &&
        node.expression.expression.text === ellModuleImportIdentifier
      ) {
        if (aliasToLMPType[node.expression.name.text] === 'tool') {
          const { inputSchema, outputSchema } = getToolSchema(
            node.arguments[0] as ts.ArrowFunction | ts.FunctionExpression,
            checker
          )
          return {
            lmpDefinitionType: 'tool',
            // todo. maybe allow config in second argument to ell.tool
            config: '',
            fn: node.arguments[0].getText(sourceFile),
            inputSchema,
            outputSchema,
          }
        }
        if (node.arguments.length > 0) {
          return {
            lmpDefinitionType: aliasToLMPType[node.expression.name.text],
            config: node.arguments[0].getText(sourceFile),
            fn: node.arguments[1].getText(sourceFile),
          }
        }
      }
    }

    const checker = this.program.getTypeChecker()

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
                  inputSchema: lmp.inputSchema,
                  outputSchema: lmp.outputSchema,
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

function getToolSchema(node: ts.ArrowFunction | ts.FunctionExpression, checker: ts.TypeChecker) {
  let inputSchema: z.ZodTypeAny | undefined
  let outputSchema: z.ZodTypeAny | undefined
  const functionType = checker.getTypeAtLocation(node)
  const callSignatures = functionType.getCallSignatures()
  // todo. hard to support overloads for tool calls....
  if (callSignatures.length > 0) {
    const signature = callSignatures[0]
    const parameters = signature.getParameters()
    if (parameters.length > 0) {
      const paramType = checker.getTypeOfSymbolAtLocation(parameters[0], parameters[0].valueDeclaration!)
      inputSchema = typeToZodSchema(paramType, checker)
    }

    // We may not need return type for today's tool call APIs,
    // but this is powerful information to know in case we want structured tool output
    // or the ability to chain tool calls via function composition.
    const returnType = signature.getReturnType()
    if (
      returnType.symbol &&
      returnType.symbol.name === 'Promise' &&
      returnType.symbol.getEscapedName() === 'Promise' &&
      (returnType as ts.TypeReference).typeArguments
    ) {
      const promiseTypeArg = (returnType as ts.TypeReference).typeArguments![0]
      outputSchema = typeToZodSchema(promiseTypeArg, checker)
    } else {
      outputSchema = typeToZodSchema(returnType, checker)
    }
  }
  return { inputSchema, outputSchema }
}

/**
 * Converts a TypeScript type into a Zod schema.
 * @param type The TypeScript type to convert.
 * @param checker The TypeScript type checker.
 * @returns A Zod schema representing the TypeScript type.
 */
function typeToZodSchema(type: ts.Type, checker: ts.TypeChecker): z.ZodTypeAny {
  if (type.flags & ts.TypeFlags.Number) {
    return z.number()
  } else if (type.flags & ts.TypeFlags.String) {
    return z.string()
  } else if (type.flags & ts.TypeFlags.Boolean) {
    return z.boolean()
  } else if (type.flags & ts.TypeFlags.Null) {
    return z.null()
  } else if (type.flags & ts.TypeFlags.Undefined) {
    return z.undefined()
  } else if (type.flags & ts.TypeFlags.Any) {
    return z.any()
  } else if (type.isUnion()) {
    const schemas = type.types.map((t) => typeToZodSchema(t, checker))
    return z.union(schemas as [z.ZodTypeAny, z.ZodTypeAny])
  } else if (type.isIntersection()) {
    const schemas = type.types.map((t) => typeToZodSchema(t, checker))
    return z.intersection(schemas[0], schemas[1]) // Simplified for two types
  } else if (type.getSymbol()?.getName() === 'Array') {
    const elementType = (type as ts.TypeReference).typeArguments?.[0]
    if (elementType) {
      return z.array(typeToZodSchema(elementType, checker))
    }
    return z.array(z.any())
  } else if (type.getSymbol()?.members) {
    const shape: Record<string, z.ZodTypeAny> = {}
    type.getProperties().forEach((prop) => {
      const propType = checker.getTypeOfSymbolAtLocation(prop, prop.valueDeclaration!)
      shape[prop.getName()] = typeToZodSchema(propType, checker)
    })
    return z.object(shape)
  } else {
    return z.any()
  }
}

// fixme. initialize for the filename / project being executed
export const tsc = new EllTSC()

// new EllTSC()
//   .getLMPsInFile(path.resolve("src/example.ts"))
//   .then(console.log);