const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.join(__dirname, "chat.v1.js"), "utf8");

function extractFunction(name) {
    const marker = `function ${name}(`;
    const start = source.indexOf(marker);
    if (start < 0) throw new Error(`Missing function: ${name}`);
    const brace = source.indexOf("{", start);
    let depth = 0;
    let quote = null;
    let regex = false;
    let regexClass = false;
    let lineComment = false;
    let blockComment = false;
    let escaped = false;
    for (let i = brace; i < source.length; i += 1) {
        const char = source[i];
        const next = source[i + 1];
        if (lineComment) {
            if (char === "\n") lineComment = false;
            continue;
        }
        if (blockComment) {
            if (char === "*" && next === "/") {
                blockComment = false;
                i += 1;
            }
            continue;
        }
        if (quote) {
            if (escaped) escaped = false;
            else if (char === "\\") escaped = true;
            else if (char === quote) quote = null;
            continue;
        }
        if (regex) {
            if (escaped) escaped = false;
            else if (char === "\\") escaped = true;
            else if (char === "[") regexClass = true;
            else if (char === "]") regexClass = false;
            else if (char === "/" && !regexClass) regex = false;
            continue;
        }
        if (char === "/" && next === "/") {
            lineComment = true;
            i += 1;
            continue;
        }
        if (char === "/" && next === "*") {
            blockComment = true;
            i += 1;
            continue;
        }
        if (char === "'" || char === '"' || char === "`") {
            quote = char;
        } else if (char === "/") {
            const before = source.slice(start, i).trimEnd().slice(-1);
            if (!before || "([=,:;!&|?{}\\n".includes(before)) regex = true;
        } else if (char === "{") {
            depth += 1;
        } else if (char === "}") {
            depth -= 1;
            if (depth === 0) return source.slice(start, i + 1);
        }
    }
    throw new Error(`Unclosed function: ${name}`);
}

const context = {};
vm.createContext(context);
vm.runInContext(
    [
        extractFunction("normalizeDetectText"),
        extractFunction("wantsWordExport"),
        extractFunction("wantsImageGeneration"),
    ].join("\n"),
    context,
);

const imageCases = [
    ["帮我生成美国国旗", true],
    ["生成美国国旗", true],
    ["generate american flag", true],
    ["生成一张小猫图片", true],
    ["帮我识别这张照片", false],
    ["帮我分析这张图片", false],
    ["写一份会议纪要", false],
];
const wordCases = [
    ["导出 Word", true],
    ["把这个转成 docx", true],
    ["给我一份 Word 文档", true],
    ["帮我生成美国国旗", false],
    ["写一份会议纪要", false],
];

for (const [text, expected] of imageCases) {
    const actual = context.wantsImageGeneration(text);
    if (actual !== expected) {
        throw new Error(`wantsImageGeneration(${JSON.stringify(text)})=${actual}, expected ${expected}`);
    }
}
for (const [text, expected] of wordCases) {
    const actual = context.wantsWordExport(text);
    if (actual !== expected) {
        throw new Error(`wantsWordExport(${JSON.stringify(text)})=${actual}, expected ${expected}`);
    }
}

console.log(`TomGPT intent tests passed (${imageCases.length + wordCases.length} cases)`);
