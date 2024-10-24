import json
import subprocess
from pathlib import Path
from typing import List
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
import logging
from docutils.nodes import make_id, Node
import random
import string


logger = logging.getLogger(__name__)


class TypeScriptAutomodule(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        module_name = self.arguments[0]
        root_path = self.env.config.typescript_root_path
        if root_path is None:
            raise ValueError("typescript_root_path is not set")

        parsed_data = parse_typescript_module(module_name, root_path)
        if parsed_data:
            doc_nodes = generate_docs(parsed_data)
            print(doc_nodes)
            logger.debug(f"Generated {len(doc_nodes)} nodes for {module_name}")
            return doc_nodes
        logger.warning(f"No parsed data for {module_name}")
        return []


def parse_typescript_module(module_name, root_path):
    ts_file = Path(root_path) / f"{module_name}.ts"
    print(f"Parsing TypeScript file: {ts_file}")
    if not ts_file.exists():
        logger.warning(f"TypeScript file not found: {ts_file}")
        return None

    try:
        # Use a Node.js script to parse the TypeScript file
        result = subprocess.run(
            ['node', 'src/parse_typescript.js', str(ts_file)],
            # Changed to False to prevent exception
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            logger.error(f"Error parsing TypeScript file. Exit code: {
                         result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return None
        # print(f"Result: {result.stdout}")
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Exception while parsing TypeScript file: {e}")
        return None


def validate_doc_structure(doc_nodes: List[nodes.Node]) -> None:
    for node in doc_nodes:
        if not isinstance(node, (nodes.section, nodes.paragraph)):
            logger.warning(f"Unexpected top-level node type: {type(node)}")
        if isinstance(node, nodes.section):
            if not node['ids']:
                logger.warning(f"Section node missing IDs: {
                               node.astext()[:50]}...")
            if not isinstance(node[0], nodes.title):
                logger.warning(f"Section missing title: {node['ids']}")


def generate_random_id() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


def generate_docs(parsed_data: dict) -> List[nodes.Node]:
    logger.debug("Starting generate_docs")
    doc_nodes: List[nodes.Node] = []

    # Module documentation
    module_section = nodes.section()
    module_section['ids'] = [generate_random_id() for _ in range(100)]
    module_section += nodes.title(
        text=f"Module: {parsed_data.get('name', 'Unknown')}")

    if parsed_data.get('documentation'):
        module_section += nodes.paragraph(text=parsed_data['documentation'])

    doc_nodes.append(module_section)
    logger.debug(f"Added module section with {len(module_section['ids'])} IDs")

    # Functions
    if parsed_data.get('functions'):
        functions_section = nodes.section()
        functions_section['ids'] = [generate_random_id()]
        functions_section += nodes.title(text="Functions")
        for func in parsed_data['functions']:
            func_section = nodes.section()
            func_section['ids'] = [generate_random_id()]
            func_section += nodes.title(text=func.get('name',
                                        'Unnamed function'))
            if func.get('documentation'):
                func_section += nodes.paragraph(text=func['documentation'])

            parameters = nodes.bullet_list()
            for param in func.get('parameters', []):
                param_item = nodes.list_item()
                param_item += nodes.strong(text=f"{param['name']}: ")
                param_item += nodes.inline(text=param['type'])
                if param.get('documentation'):
                    param_item += nodes.inline(
                        text=f" - {param['documentation']}")
                parameters += param_item

            if parameters.children:
                func_section += nodes.paragraph(text="Parameters:")
                func_section += parameters

            if func.get('returnType'):
                func_section += nodes.paragraph(
                    text=f"Returns: {func['returnType']}")

            functions_section += func_section

        if functions_section.children:
            doc_nodes.append(functions_section)
            logger.debug(f"Added functions section with {len(
                functions_section.children)} children and {len(functions_section['ids'])} IDs")

    # Classes
    if parsed_data.get('classes'):
        classes_section = nodes.section()
        classes_section['ids'] = [generate_random_id()]
        classes_section += nodes.title(text="Classes")
        for cls in parsed_data['classes']:
            class_section = nodes.section()
            class_section['ids'] = [generate_random_id()]
            class_section += nodes.title(text=cls.get('name', 'Unnamed class'))
            if cls.get('documentation'):
                class_section += nodes.paragraph(text=cls['documentation'])

            # Properties
            if cls.get('properties'):
                props_section = nodes.section()
                props_section['ids'] = [generate_random_id()]
                props_section += nodes.title(text="Properties")
                for prop in cls['properties']:
                    prop_item = nodes.paragraph()
                    prop_item += nodes.strong(text=f"{prop['name']}: ")
                    prop_item += nodes.inline(text=prop['type'])
                    if prop.get('documentation'):
                        prop_item += nodes.inline(
                            text=f" - {prop['documentation']}")
                    props_section += prop_item
                class_section += props_section

            # Methods
            if cls.get('methods'):
                methods_section = nodes.section()
                methods_section['ids'] = [generate_random_id()]
                methods_section += nodes.title(text="Methods")
                for method in cls['methods']:
                    method_section = nodes.section()
                    method_section['ids'] = [generate_random_id()]
                    method_section += nodes.title(text=method['name'])
                    if method.get('documentation'):
                        method_section += nodes.paragraph(
                            text=method['documentation'])

                    parameters = nodes.bullet_list()
                    for param in method.get('parameters', []):
                        param_item = nodes.list_item()
                        param_item += nodes.strong(text=f"{param['name']}: ")
                        param_item += nodes.inline(text=param['type'])
                        if param.get('documentation'):
                            param_item += nodes.inline(
                                text=f" - {param['documentation']}")
                        parameters += param_item

                    if parameters.children:
                        method_section += nodes.paragraph(text="Parameters:")
                        method_section += parameters

                    if method.get('returnType'):
                        method_section += nodes.paragraph(
                            text=f"Returns: {method['returnType']}")

                    methods_section += method_section

                class_section += methods_section

            classes_section += class_section

        if classes_section.children:
            doc_nodes.append(classes_section)
            logger.debug(f"Added classes section with {
                         len(classes_section.children)} children and {len(classes_section['ids'])} IDs")

    # Interfaces
    if parsed_data.get('interfaces'):
        interfaces_section = nodes.section()
        interfaces_section['ids'] = [generate_random_id()]
        interfaces_section += nodes.title(text="Interfaces")
        for interface in parsed_data['interfaces']:
            interface_section = nodes.section()
            interface_section['ids'] = [generate_random_id()]
            interface_section += nodes.title(
                text=interface.get('name', 'Unnamed interface'))
            if interface.get('documentation'):
                interface_section += nodes.paragraph(
                    text=interface['documentation'])

            # Properties
            if interface.get('properties'):
                props_section = nodes.section()
                props_section['ids'] = [generate_random_id()]
                props_section += nodes.title(text="Properties")
                for prop in interface['properties']:
                    prop_item = nodes.paragraph()
                    prop_item += nodes.strong(text=f"{prop['name']}: ")
                    prop_item += nodes.inline(text=prop['type'])
                    if prop.get('documentation'):
                        prop_item += nodes.inline(
                            text=f" - {prop['documentation']}")
                    props_section += prop_item
                interface_section += props_section

            interfaces_section += interface_section

        if interfaces_section.children:
            doc_nodes.append(interfaces_section)
            logger.debug(f"Added interfaces section with {len(
                interfaces_section.children)} children and {len(interfaces_section['ids'])} IDs")

    if not doc_nodes:
        placeholder = nodes.paragraph(
            text="No documentation available for this module.")
        placeholder['ids'] = [generate_random_id()]
        doc_nodes.append(placeholder)
        logger.debug("Added placeholder for empty module with 100 IDs")

    logger.debug(f"Finished generate_docs with {
                 len(doc_nodes)} top-level nodes")
    for i, node in enumerate(doc_nodes):
        logger.debug(
            f"Top-level node {i}: type={type(node)}, number of ids={len(node.get('ids', []))}")
        if isinstance(node, nodes.section):
            logger.debug(f"  Section title: {node[0].astext()}")
    return doc_nodes


def setup(app):
    app.add_directive('js:automodule', TypeScriptAutomodule)
    app.add_config_value('typescript_root_path', 'typescript/src', 'env')

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    return {
        'version': '0.1',
        'parallel_read_safe': False,
        'parallel_write_safe': False,
    }
