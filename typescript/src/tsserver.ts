import * as cp from "child_process";
import * as path from "path";
import ts from "typescript";

const tsServerPath = require.resolve("typescript/lib/tsserver.js");

class TSServer {
  private process: cp.ChildProcess;
  private messageId = 0;
  private responseCallbacks: Map<number, (response: any) => void> = new Map();

  constructor() {
    this.process = cp.fork(
      tsServerPath,
      ["--useInferredProjectPerProjectRoot"],
      { detached: false, stdio: ["pipe", "pipe", "pipe", "ipc"] }
    );

    console.log("tsServerPath", tsServerPath, this.process);
    this.process.on("error", (error: any) => {
      console.error("tsServer process error", error);
    });
    this.process.on("disconnect", () => {
      console.log("tsServer process disconnected");
    });
    this.process.on("exit", (code: number, signal: NodeJS.Signals | null) => {
      console.log(
        "tsServer process exited with code",
        code,
        "and signal",
        signal
      );
    });
    this.process.on("message", (message: any) => {
      const callback = this.responseCallbacks.get(message.request_seq);
      if (callback) {
        callback(message);
        this.responseCallbacks.delete(message.request_seq);
      }
    });
  }

  async sendRequest(command: string, args: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const id = ++this.messageId;
      const timeout = setTimeout(() => {
        reject(
          new Error(`Request ${id} (${command}) timed out after 10 seconds`)
        );
        this.responseCallbacks.delete(id);
      }, 10000);

      this.responseCallbacks.set(id, (response) => {
        clearTimeout(timeout);
        resolve(response);
      });

      console.log(`Sending request ${id}: ${command}`);
      this.process.send({ seq: id, type: "request", command, arguments: args });
    });
  }

  async getFunctionSource(
    filePath: string,
    line: number,
    column: number
  ): Promise<string | null> {
    const response = await this.sendRequest("definition", {
      file: filePath,
      line,
      offset: column,
    });

    if (response.body && response.body.length > 0) {
      const def = response.body[0];
      const fileContents = await this.sendRequest("open", { file: def.file });
      return fileContents.body.sourceFile.text.slice(def.start, def.end);
    }

    return null;
  }
  async getAST(filePath: string): Promise<ts.SourceFile> {
    const response = await this.sendRequest("getAST", { file: filePath });
    return response.body;
  }
  async getLMPsInFile(filePath: string): Promise<string[]> {
    const ast = await this.getAST(filePath);
    let ellImportIdentifier: string | null = null;
    const lmpMatches: string[] = [];
    const ELL_LIB_NAME = "./ell" || "ell-ai";
    console.log("ELL_LIB_NAME", ELL_LIB_NAME);

    function visit(node: ts.Node) {
      if (ts.isImportDeclaration(node)) {
        if (
          ts.isStringLiteral(node.moduleSpecifier) &&
          node.moduleSpecifier.text === ELL_LIB_NAME
        ) {
          if (node.importClause) {
            if (node.importClause.name) {
              // Default import
              ellImportIdentifier = node.importClause.name.text;
            } else if (node.importClause.namedBindings) {
              if (ts.isNamedImports(node.importClause.namedBindings)) {
                // Named imports
                node.importClause.namedBindings.elements.forEach((element) => {
                  if (
                    element.propertyName?.text === "lm" ||
                    element.name.text === "lm"
                  ) {
                    ellImportIdentifier = element.name.text;
                  }
                });
              } else if (
                ts.isNamespaceImport(node.importClause.namedBindings)
              ) {
                // Namespace import
                ellImportIdentifier = node.importClause.namedBindings.name.text;
              }
            }
          }
        }
      } else if (ts.isCallExpression(node)) {
        if (
          ts.isPropertyAccessExpression(node.expression) &&
          node.expression.name.text === "lm" &&
          node.expression.expression.getText() === ellImportIdentifier
        ) {
          if (node.arguments.length > 0) {
            lmpMatches.push(node.arguments[0].getText());
          }
        }
      }

      ts.forEachChild(node, visit);
    }

    visit(ast);
    return lmpMatches;
  }
}

const LMP_FUNCTION_EXPORT_NAMES = ["simple", "complex"];
const ELL_MODULE_IDENTIFIER = "./ell" || "ell-ai";



/**
 * Get all import declarations in a source file
 * @param sourceFile 
 * @returns 
 */
const getAllImportDeclarations = (sourceFile: ts.SourceFile): ts.ImportDeclaration[] => {
  const importDeclarations: ts.ImportDeclaration[] = [];

  const visit = (statements: ts.Statement[] | ts.NodeArray<ts.Statement>) => {
    statements.forEach((statement) => {
      if (ts.isImportDeclaration(statement)) {
        importDeclarations.push(statement);
      }
    });
  };
  visit(sourceFile.statements);
  return importDeclarations;
};

/**
 * True if the source file imports `ell-ai`
 * @param sourceFile 
 * @returns 
 */
const hasEllImport = (sourceFile: ts.SourceFile): boolean => {
  const importDecls = getAllImportDeclarations(sourceFile);
  return importDecls.some((decl) => ts.isStringLiteral(decl.moduleSpecifier) && decl.moduleSpecifier.text === ELL_MODULE_IDENTIFIER);
};

interface EllTSC {
  getAST(filePath: string): Promise<ts.SourceFile | undefined>;
  getLMPsInFile(filePath: string): Promise<LMP[]>;
  getFunctionSource(
    filePath: string,
    line: number,
    column: number
  ): Promise<string | null>;
}

type LMPType = "simple" | "complex";
type LMP = { lmpType: LMPType; config: string; fn: string };

class EllTSC implements EllTSC {
  private program: ts.Program;
  constructor(rootDir: string = process.cwd()) {
    const configPath = ts.findConfigFile(
      rootDir,
      ts.sys.fileExists,
      "tsconfig.json"
    );
    if (!configPath) {
      throw new Error("Could not find a valid 'tsconfig.json'.");
    }

    const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
    const parsedCommandLine = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      path.dirname(configPath)
    );

    this.program = ts.createProgram({
      rootNames: parsedCommandLine.fileNames,
      options: parsedCommandLine.options,
      projectReferences: parsedCommandLine.projectReferences,
    });
  }

  async getAST(filePath: string): Promise<ts.SourceFile | undefined> {
    return this.program.getSourceFile(filePath);
  }

  async getLMPsInFile(filePath: string): Promise<LMP[]> {
    const sourceFile = await this.getAST(filePath);
    if (!sourceFile) {
      console.log(
        "available files",
        this.program.getSourceFiles().map((f) => f.fileName)
      );
      throw new Error("Could not get AST for file " + filePath);
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
    let ellModuleImportIdentifier: string | null = null;

    const lmps: LMP[] = [];
    const lmpTypeToAlias: Record<LMPType, string> = {
      simple: "simple",
      complex: "complex",
    };
    const aliasToLMPType: Record<string, LMPType> = {
      simple: "simple",
      complex: "complex",
    };

    function visit(node: ts.Node) {
      if (ts.isImportDeclaration(node)) {
        if (
          ts.isStringLiteral(node.moduleSpecifier) &&
          node.moduleSpecifier.text === ELL_MODULE_IDENTIFIER
        ) {
          if (node.importClause) {
            if (node.importClause.name) {
              // Default import
              ellModuleImportIdentifier = node.importClause.name.text;
            } else if (node.importClause.namedBindings) {
              if (ts.isNamedImports(node.importClause.namedBindings)) {
                // Named imports
                node.importClause.namedBindings.elements.forEach((element) => {
                  // We're using an alias bound to 'name' for something
                  if (element.propertyName) {
                    if (element.propertyName.text === "default") {
                      // default import
                      ellModuleImportIdentifier = element.name.text;
                    } else if (
                      // If it's one of the lmp functions
                      LMP_FUNCTION_EXPORT_NAMES.includes( element.propertyName.text)
                    ) {
                      // Store the alias for future use
                      const alias = element.name.text;
                      const lmpType = element.propertyName.text as LMPType;
                      lmpTypeToAlias[lmpType] = alias;
                      aliasToLMPType[alias] = lmpType;
                    }
                  }
                });
              } else if (
                ts.isNamespaceImport(node.importClause.namedBindings)
              ) {
                // Namespace import
                // todo. match on property access
                // import * as ell from "ell-ai";
                // ell.simple
                ellModuleImportIdentifier =
                  node.importClause.namedBindings.name.text;
              }
            }
          }
        }
      } else if (ts.isCallExpression(node)) {
        // Bare function call
        // mySimpleAlias()
        // myComplexAlias()
        if (ts.isIdentifier(node.expression)) {
          if (Object.keys(aliasToLMPType).includes(node.expression.text)) {
            if (node.arguments.length > 0) {
              const lmpFnConfig = node.arguments[0];
              const lmpFn = node.arguments[1];
              lmps.push({
                lmpType: aliasToLMPType[node.expression.text],
                config: lmpFnConfig.getText(sourceFile),
                fn: lmpFn.getText(sourceFile),
              });
            }
          }
        }
        // Method/property access 
        // myEll.mySimpleAlias()
        if (
          ts.isPropertyAccessExpression(node.expression) &&
          Object.keys(aliasToLMPType).includes(node.expression.name.text) &&
          node.expression.expression.getText() === ellModuleImportIdentifier
        ) {
          if (node.arguments.length > 0) {
            lmps.push({
              lmpType: aliasToLMPType[node.expression.name.text],
              config: node.arguments[0].getText(sourceFile),
              fn: node.arguments[1].getText(sourceFile),
            });
          }
        }
      }

      ts.forEachChild(node, visit);
    }

    visit(sourceFile);

    return lmps;
  }
}

new EllTSC()
  .getLMPsInFile(path.resolve("src/ell-example.ts"))
  .then(console.log);
