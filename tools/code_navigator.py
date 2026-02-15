#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    import tree_sitter
    from tree_sitter import Language, Parser
except ImportError:
    print("Error: tree-sitter not installed", file=sys.stderr)
    sys.exit(1)

EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}

def get_parser(lang_name: str) -> Parser:
    parser = Parser()
    try:
        if lang_name == "python":
            import tree_sitter_python
            lang = tree_sitter_python.language()
        elif lang_name == "javascript":
            import tree_sitter_javascript
            lang = tree_sitter_javascript.language()
        elif lang_name == "go":
            import tree_sitter_go
            lang = tree_sitter_go.language()
        elif lang_name == "c":
            import tree_sitter_c
            lang = tree_sitter_c.language()
        elif lang_name == "cpp":
            import tree_sitter_cpp
            lang = tree_sitter_cpp.language()
        else:
            return None
        
        parser.set_language(lang)
        return parser
    except ImportError:
        return None

def extract_definitions(file_path: Path, lang_name: str) -> List[Dict[str, Any]]:
    parser = get_parser(lang_name)
    if not parser:
        return []

    try:
        with open(file_path, "rb") as f:
            content = f.read()
    except Exception as e:
        return [{"error": str(e)}]

    tree = parser.parse(content)
    root_node = tree.root_node
    
    definitions = []
        
    if lang_name == "python":
        query = tree.language.query("""
            (function_definition
                name: (identifier) @func.name) @func.def
            (class_definition
                name: (identifier) @class.name) @class.def
        """)
    elif lang_name == "javascript":
        query = tree.language.query("""
            (function_declaration
                name: (identifier) @func.name) @func.def
            (class_declaration
                name: (identifier) @class.name) @class.def
        """)
    elif lang_name == "go":
        query = tree.language.query("""
            (function_declaration
                name: (identifier) @func.name) @func.def
            (type_declaration 
                (type_spec 
                    name: (type_identifier) @class.name)) @class.def
        """)
    else:
        # Fallback/TODO for C/Cpp
        return []

    captures = query.captures(root_node)
    
    for node, tag in captures:
        if tag.endswith(".name"):
            def_type = "function" if "func" in tag else "class"
            definitions.append({
                "type": def_type,
                "name": content[node.start_byte:node.end_byte].decode("utf-8"),
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1
            })

    return definitions

def scan_directory(path: Path) -> Dict[str, Any]:
    structure = {}
    for root, _, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            if any(str(file_path).endswith(ext) for ext in EXT_TO_LANG):
                ext = file_path.suffix
                lang = EXT_TO_LANG.get(ext)
                if lang:
                    defs = extract_definitions(file_path, lang)
                    if defs:
                        structure[str(file_path)] = defs
    return structure

def main():
    parser = argparse.ArgumentParser(description="Navigate codebase structure using tree-sitter")
    parser.add_argument("path", help="Path to file or directory to analyze")
    args = parser.parse_args()

    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: {target_path} does not exist", file=sys.stderr)
        sys.exit(1)

    if target_path.is_file():
        ext = target_path.suffix
        lang = EXT_TO_LANG.get(ext)
        if lang:
            result = {str(target_path): extract_definitions(target_path, lang)}
            print(json.dumps(result, indent=2))
        else:
            print(f"Unsupported file extension: {ext}", file=sys.stderr)
    else:
        result = scan_directory(target_path)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
