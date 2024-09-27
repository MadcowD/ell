import json
from typing import List, Optional
import ell
from pydantic import BaseModel, Field
import re

@ell.simple(model="gpt-4-turbo-preview", response_format={"type": "json_object"})
def create_person_json(description: str):
    """
    Generate a JSON object describing a person based on the given description.
    """
    return (
        f"Based on the description '{description}', create a JSON object for a Person."
    )


@ell.simple(
    model="gpt-4o-2024-08-06",
    response_format={
    "type": "json_schema",
    "json_schema": {
            "name": "ui",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "The type of the UI component",
                        "enum": ["div", "button", "header", "section", "field", "form"],
                    },
                    "label": {
                        "type": "string",
                        "description": "The label of the UI component, used for buttons or form fields",
                    },
                    "children": {
                        "type": "array",
                        "description": "Nested UI components",
                        "items": {"$ref": "#"},
                    },
                    "attributes": {
                        "type": "array",
                        "description": "Arbitrary attributes for the UI component, suitable for any element",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The name of the attribute, for example onClick or className",
                                },
                                "value": {
                                    "type": "string",
                                    "description": "The value of the attribute",
                                },
                            },
                            "required": ["name", "value"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["type", "label", "children", "attributes"],
                "additionalProperties": False,
            },
        },
    },
)
def generate_ui_json(description: str):
    """
    Generate a JSON object describing a UI based on the given description,
    conforming to the UI schema.
    Don't use class names use hard coded styles.
    Be sure to fill out all the details.
    """
    return f"Based on the description '{description}', create a JSON object for a UI that conforms to the provided schema."


def parse_style(style_str):
    return dict(item.split(":") for item in style_str.split(";") if item)

def print_ascii_ui(ui_component, indent=0, width=60):
    def center(text, width):
        return text.center(width)

    def hr(width, char='-'):
        return char * width

    def render_component(component, indent, width):
        component_type = component['type'].lower()
        label = component['label']
        style = next((attr['value'] for attr in component.get('attributes', []) if attr['name'] == 'style'), '')
        
        if component_type == 'div':
            print(f"{' ' * indent}{label}")
        elif component_type == 'header':
            print(center(f"=== {label.upper()} ===", width))
        elif component_type == 'button':
            print(center(f"[ {label} ]", width))
        elif component_type == 'section':
            print(f"{' ' * indent}{hr(width - indent, '-')}")
            print(f"{' ' * indent}{label.upper()}")
            print(f"{' ' * indent}{hr(width - indent, '-')}")
        elif component_type == 'field':
            print(f"{' ' * indent}{label}: ___________________")
        
        for child in component.get('children', []):
            render_component(child, indent + 2, width)

    print(hr(width, '='))
    render_component(ui_component, 0, width)
    print(hr(width, '='))

ell.init(verbose=True, store="./logdir")

if __name__ == "__main__":
    description = "A 28-year-old named Alex who loves hiking and painting, with a preference for the color blue."
    result = json.loads(create_person_json(description))

    ui_result = json.loads(generate_ui_json("Facebook page for " + description))
    print("\nRendered UI representation:")
    print_ascii_ui(ui_result)
    print()  # Add an extra newline for better readability
