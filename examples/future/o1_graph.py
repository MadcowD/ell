""""
Example originally from Instructor docs https://python.useinstructor.com/examples/knowledge_graph/
All rights reserved to the original author.
"""

from graphviz import Digraph
from pydantic import BaseModel, Field
from typing import List, Optional


class Node(BaseModel):
    id: int
    label: str
    color: str


class Edge(BaseModel):
    source: int
    target: int
    label: str
    color: str = Field(description="The color of the edge. Defaults to black.")


class KnowledgeGraph(BaseModel):
    nodes: Optional[List[Node]] = Field(..., default_factory=list)
    edges: Optional[List[Edge]] = Field(..., default_factory=list)

    def update(self, other: "KnowledgeGraph") -> "KnowledgeGraph":
        """Updates the current graph with the other graph, deduplicating nodes and edges."""
        # Create dictionaries to store unique nodes and edges
        unique_nodes = {node.id: node for node in self.nodes}
        unique_edges = {(edge.source, edge.target, edge.label): edge for edge in self.edges}

        # Update with nodes and edges from the other graph
        for node in other.nodes:
            unique_nodes[node.id] = node
        for edge in other.edges:
            unique_edges[(edge.source, edge.target, edge.label)] = edge

        return KnowledgeGraph(
            nodes=list(unique_nodes.values()),
            edges=list(unique_edges.values()),
        )

    def draw(self, prefix: str = None):
        dot = Digraph(comment="Knowledge Graph")

        for node in self.nodes:  
            dot.node(str(node.id), node.label, color=node.color)

        for edge in self.edges:  
            dot.edge(
                str(edge.source), str(edge.target), label=edge.label, color=edge.color
            )
        dot.render(prefix, format="png", view=True)


import ell2a

@ell2a.simple(model="o1-mini")
def update_knowledge_graph(cur_state: KnowledgeGraph, inp: str, i: int, num_iterations: int):
    return [
        ell2a.user(f"""You are an iterative code base knowledge graph builder. You are trying to build the most useful represnetaiton about how thigns in the codebase interact with eachother.
                It is important that your graph is semantically meaningful The edges should not just be has method etc. A knowledge graph woild best convey that to someone learning the system for the first time & doesn't know programming.

                You are given the current state of the graph, and you must append the nodes and edges   to it Do not procide any duplcates and try to reuse nodes as much as possible. Extract any new nodes and edges from the following:
                Here is the current state of the graph:
                {cur_state.model_dump_json(indent=2)}
                You will produce an update to the graph that that will overwtite nodes and add edges (you cannot remove them.) 
                Answer only in this JSON format:
                {KnowledgeGraph.model_json_schema()}
                Do not wrap your JSON update in back ticks (```)
                Do not include any other text.
                """),
        ell2a.user(f"""
        # Part {i}/{num_iterations} of the source code:

        {inp}"""),
    ]

def generate_graph(input: List[str]) -> KnowledgeGraph:
    cur_state = KnowledgeGraph()  
    num_iterations = len(input)
    for i, inp in enumerate(input):
        new_updates = update_knowledge_graph(cur_state, inp, i, num_iterations)
        # Try to parse it
        new_updates = new_updates.replace("```json", '"')
        new_updates = new_updates.replace("```", '"')
        new_updates = KnowledgeGraph.model_validate_json(new_updates)
        cur_state = cur_state.update(new_updates)  
        cur_state.draw(prefix=f"iteration_{i}")
    return cur_state

        


if __name__ == "__main__":
    ell2a.init(verbose=True, store='./logdir', autocommit=True)
    generate_graph([
        """
        class User:
            def __init__(self, name, email):
                self.name = name
                self.email = email
            
            def send_email(self, message):
                # Send email logic here
                pass

        class Order:
            def __init__(self, user, items):
                self.user = user
                self.items = items
            
            def process(self):
                # Order processing logic
                self.user.send_email("Your order has been processed.")
        """,
        """
        class Product:
            def __init__(self, name, price):
                self.name = name
                self.price = price

        class ShoppingCart:
            def __init__(self):
                self.items = []
            
            def add_item(self, product, quantity):
                self.items.append((product, quantity))
            
            def calculate_total(self):
                return sum(product.price * quantity for product, quantity in self.items)
        """,
        """
        class PaymentProcessor:
            @staticmethod
            def process_payment(order, amount):
                # Payment processing logic
                pass

        class OrderManager:
            @staticmethod
            def create_order(user, cart):
                order = Order(user, cart.items)
                total = cart.calculate_total()
                PaymentProcessor.process_payment(order, total)
                order.process()
        """
    ])

