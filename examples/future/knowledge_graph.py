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


import ell

@ell.complex(model="gpt-4o-2024-08-06", response_format=KnowledgeGraph)
def update_knowledge_graph(cur_state: KnowledgeGraph, inp: str, i: int, num_iterations: int):
    return [
        ell.system("""You are an iterative knowledge graph builder.
        You are given the current state of the graph, and you must append the nodes and edges
        to it Do not procide any duplcates and try to reuse nodes as much as possible."""),
        ell.user(f"""Extract any new nodes and edges from the following:
        # Part {i}/{num_iterations} of the input:

        {inp}"""),
        ell.user(f"""Here is the current state of the graph:
        {cur_state.model_dump_json(indent=2)}""")
    ]

def generate_graph(input: List[str]) -> KnowledgeGraph:
    cur_state = KnowledgeGraph()  
    num_iterations = len(input)
    for i, inp in enumerate(input):
        new_updates = update_knowledge_graph(cur_state, inp, i, num_iterations).parsed
        cur_state = cur_state.update(new_updates)  
        cur_state.draw(prefix=f"iteration_{i}")
    return cur_state

        


if __name__ == "__main__":
    ell.init(verbose=True, store='./logdir', autocommit=True)
    generate_graph(["This is a test", "This is another test", "This is a third test"])

# Compare to: Original instructor example.
# def generate_graph(input: List[str]) -> KnowledgeGraph:
#     cur_state = KnowledgeGraph()  
#     num_iterations = len(input)
#     for i, inp in enumerate(input):
#         new_updates = client.chat.completions.create(
#             model="gpt-3.5-turbo-16k",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": """You are an iterative knowledge graph builder.
#                     You are given the current state of the graph, and you must append the nodes and edges
#                     to it Do not procide any duplcates and try to reuse nodes as much as possible.""",
#                 },
#                 {
#                     "role": "user",
#                     "content": f"""Extract any new nodes and edges from the following:
#                     # Part {i}/{num_iterations} of the input:

#                     {inp}""",
#                 },
#                 {
#                     "role": "user",
#                     "content": f"""Here is the current state of the graph:
#                     {cur_state.model_dump_json(indent=2)}""",
#                 },  
#             ],
#             response_model=KnowledgeGraph,
#         )  # type: ignore

#         # Update the current state
#         cur_state = cur_state.update(new_updates)  
#         cur_state.draw(prefix=f"iteration_{i}")
#     return cur_state



# Bonus: Generate with a chat history.
# XXX: This illustrates the need for a dedicated chat type in ell.
# @ell.complex(model="gpt-4o-2024-08-06", response_format=KnowledgeGraph)
# def update_knowledge_graph_with_chat_history(cur_state: KnowledgeGraph, inp: str, i: int, num_iterations: int, chat_history):
#     return [
#         ell.system("""You are an iterative knowledge graph builder.
#         You are given the current state of the graph, and you must append the nodes and edges
#         to it Do not procide any duplcates and try to reuse nodes as much as possible."""),
#         *chat_history,
#         ell.user(f"""Extract any new nodes and edges from the following:
#         # Part {i}/{num_iterations} of the input:

#         {inp}"""),
#         ell.user(f"""Here is the current state of the graph:
#         {cur_state.model_dump_json(indent=2)}""")
#     ]

# def generate_graph_with_chat_history(input: List[str]) -> KnowledgeGraph:
#     chat_history = []
#     cur_state = KnowledgeGraph()
#     num_iterations = len(input)
#     for i, inp in enumerate(input):
#         new_updates = update_knowledge_graph_with_chat_history(cur_state, inp, i, num_iterations, chat_history)
#         cur_state = cur_state.update(new_updates.parsed)  
#         chat_history.append(new_updates)
#         cur_state.draw(prefix=f"iteration_{i}")
#     return cur_state