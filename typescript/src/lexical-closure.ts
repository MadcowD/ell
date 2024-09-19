// @ts-nocheck
import * as ts from 'typescript';
import * as crypto from 'node:crypto';

const _crypto = require('node:crypto');
const DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$";
const FORBIDDEN_NAMES = ["ell", "lstr"];

interface ClosureResult {
    fullSource: string;
    functionSource: string;
    dependenciesSource: string;
    uses: Set<string>;
}

function lexicalClosure(
    func: Function,
    alreadyClosed: Set<string> = new Set(),
    initialCall: boolean = false,
    recursionStack: string[] = []
): ClosureResult {
    console.log('lexicalClosure', func.name)
    const uses = new Set<string>();
    const funcHash = getFunctionHash(func);

    if (alreadyClosed.has(funcHash)) {
        return { fullSource: "", functionSource: "", dependenciesSource: "", uses: new Set() };
    }

    recursionStack.push(func.name || 'anonymous');
    alreadyClosed.add(funcHash);

    const source = getFunctionSource(func);
    const { globals, frees } = getGlobalsAndFrees(func);
    const { dependencies, imports } = processDependencies(func, globals, frees, alreadyClosed, recursionStack, uses);

    const initialSource = buildInitialSource(imports, dependencies, source);
    const dirtySrc = buildFinalSource(imports, [], dependencies, source);
    const dirtySrcWithoutFunc = buildFinalSource(imports, [], dependencies, "");

    const cleanedSrc = cleanSrc(dirtySrcWithoutFunc);

    const fnHash = generateFunctionHash(source, cleanedSrc, func.name);

    if (!initialCall) {
        uses.add(fnHash);
    }

    return {
        fullSource: dirtySrc,
        functionSource: source,
        dependenciesSource: cleanedSrc,
        uses
    };
}

function getFunctionHash(func: Function): string {
    return _crypto.createHash('md5').update(func.toString()).digest('hex');
}

function getFunctionSource(func: Function): string {
    return func.toString();
}

function getGlobalsAndFrees(func: Function): { globals: Map<string, any>, frees: Map<string, any> } {
    // This is a simplified version, as TypeScript doesn't have direct access to closure variables
    const globals = new Map<string, any>();
    const frees = new Map<string, any>();
    
    // In a real implementation, you'd need to analyze the function's AST
    // to determine which variables are global or free
    
    return { globals, frees };
}

function processDependencies(
    func: Function,
    globals: Map<string, any>,
    frees: Map<string, any>,
    alreadyClosed: Set<string>,
    recursionStack: string[],
    uses: Set<string>
): { dependencies: string[], imports: string[] } {
    const dependencies: string[] = [];
    const imports: string[] = [];

    // Process globals and frees
    for (const [varName, varValue] of [...globals, ...frees]) {
        processVariable(varName, varValue, dependencies, imports, alreadyClosed, recursionStack, uses);
    }

    return { dependencies, imports };
}

function processVariable(
    varName: string,
    varValue: any,
    dependencies: string[],
    imports: string[],
    alreadyClosed: Set<string>,
    recursionStack: string[],
    uses: Set<string>
): void {
    if (typeof varValue === 'function' && !FORBIDDEN_NAMES.includes(varName)) {
        try {
            const { fullSource, uses: depUses } = lexicalClosure(varValue, alreadyClosed, false, [...recursionStack]);
            dependencies.push(fullSource);
            depUses.forEach(use => uses.add(use));
        } catch (e) {
            console.error(`Failed to capture the lexical closure of ${varName}`, e);
        }
    } else if (isImmutableVariable(varValue)) {
        dependencies.push(`const ${varName} = ${JSON.stringify(varValue)};`);
    } else {
        dependencies.push(`// ${varName} = <${typeof varValue} object>`);
    }
}

function isImmutableVariable(value: any): boolean {
    return (
        typeof value === 'number' ||
        typeof value === 'string' ||
        typeof value === 'boolean' ||
        value === null ||
        value === undefined
    );
}

function buildInitialSource(imports: string[], dependencies: string[], source: string): string {
    return `${DELIM}\n${imports.join('\n')}\n${DELIM}\n${dependencies.join('\n')}\n${DELIM}\n${source}\n${DELIM}\n`;
}

function buildFinalSource(imports: string[], moduleSrc: string[], dependencies: string[], source: string): string {
    const separatedDependencies = [...new Set([...imports, ...moduleSrc, ...dependencies, source])];
    return `${DELIM}\n${separatedDependencies.join(`\n${DELIM}\n`)}\n${DELIM}\n`;
}

function cleanSrc(dirtySrc: string): string {
    const sections = dirtySrc.split(DELIM).filter(section => section.trim().length > 0);
    const uniqueSections = [...new Set(sections)];
    
    const imports: string[] = [];
    const otherCode: string[] = [];

    uniqueSections.forEach(section => {
        if (section.startsWith('import ') || section.startsWith('from ')) {
            imports.push(section);
        } else {
            otherCode.push(section);
        }
    });

    const sortedImports = imports.sort().join('\n');
    const finalSrc = `${sortedImports}\n\n${otherCode.join('\n\n')}`;

    return finalSrc.replace(/\n{3,}/g, '\n\n');
}

function generateFunctionHash(source: string, dsrc: string, qualname: string): string {
    const hash = _crypto.createHash('md5').update(`${source}\n${dsrc}\n${qualname}`).digest('hex');
    return `lmp-${hash}`;
}

export function lexicallyClosuredSource(func: Function): [string, string, any, any, Set<string>] {
    const { functionSource, dependenciesSource, uses } = lexicalClosure(func, new Set(), true);
    // Note: In TypeScript, we don't have direct access to closure variables,
    // so the last two elements (globals and frees) are left as 'any'
    const qualname = module.__dirname
    return [functionSource, dependenciesSource, {}, {}, uses];
}

function foo() {
    const myprompt = 'hello'
    const bar = () => {
        console.log('bar');
        return myprompt
    };
    global
    console.log(lexicallyClosuredSource(bar))
    const wrapper = (fn:any)=> {

    }
}
foo()