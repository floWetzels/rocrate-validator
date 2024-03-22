from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Union

from rdflib import RDF, Graph, Namespace, URIRef
from rdflib.term import Node

from ...constants import SHACL_NS
from .utils import inject_attributes

# set up logging
logger = logging.getLogger(__name__)


class ShapeProperty:

    # define default values
    name: str = None
    description: str = None
    group: str = None
    defaultValue: str = None
    order: int = 0

    def __init__(self,
                 shape: Shape,
                 shape_property_node: Node):

        # store the shape
        self._shape = shape
        # store the node
        self._node = shape_property_node

        # TODO: refactor moving URIRef to constants

        # create a graph for the shape property
        shapes_graph = shape.shapes_graph
        shape_property_graph = Graph()
        shape_property_graph += shapes_graph.triples((shape.node, None, None))
        shape_property_graph += shapes_graph.triples((shape_property_node, None, None))
        # remove dangling properties
        for s, p, o in shape_property_graph:
            logger.debug(f"Processing {p} of property graph {shape_property_node}")
            if p == URIRef("http://www.w3.org/ns/shacl#property") and o != shape_property_node:
                shape_property_graph.remove((s, p, o))
        # add BNodes
        for s, p, o in shape_property_graph:
            shape_property_graph += shapes_graph.triples((o, None, None))

        # Use the triples method to get all triples that are part of a list
        RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        first_predicate = RDF.first
        rest_predicate = RDF.rest
        shape_property_graph += shapes_graph.triples((None, first_predicate, None))
        shape_property_graph += shapes_graph.triples((None, rest_predicate, None))
        for _, _, object in shape_property_graph:
            shape_property_graph += shapes_graph.triples((object, None, None))

        # store the graph
        self._shape_property_graph = shape_property_graph

        # inject attributes of the shape property to the object
        inject_attributes(shape_property_graph, self)

    @property
    def shape(self):
        return self._shape

    @property
    def node(self):
        return self._node

    @property
    def shape_property_graph(self):
        return self._shape_property_graph

    def compare_shape(self, other_model):
        return self.shape == other_model.shape

    def compare_name(self, other_model):
        return self.name == other_model.name


class Shape:

    # define default values
    name: str = None
    description: str = None

    def __init__(self, node: Node, shapes_graph: Graph):

        # store the shape node
        self._node = node
        # store the shapes graph
        self._shapes_graph = shapes_graph
        # initialize the properties
        self._properties = []

        # create a graph for the shape
        logger.debug("Initializing graph for the shape: %s" % node)
        shape_graph = Graph()
        shape_graph += shapes_graph.triples((node, None, None))

        # inject attributes of the shape to the object
        inject_attributes(shape_graph, self)

        # Define the property predicate
        predicate = URIRef(SHACL_NS + "property")

        # Use the triples method to get all triples with the particular predicate
        first_triples = shape_graph.triples((None, predicate, None))

        # For each triple from the first call, get all triples whose subject is the object of the first triple
        for _, _, object in first_triples:
            shape_graph += shapes_graph.triples((object, None, None))
            self._properties.append(ShapeProperty(self, object))

        # store the graph
        self._shape_graph = shape_graph

    @property
    def node(self):
        """Return the node of the shape"""
        return self._node

    @property
    def shape_graph(self):
        """Return the subgraph of the shape"""
        return self._shape_graph

    @property
    def shapes_graph(self):
        """Return the graph of the shapes which contains the shape"""
        return self._shapes_graph

    @property
    def properties(self):
        """Return the properties of the shape"""
        return self._properties.copy()

    def get_properties(self) -> List[ShapeProperty]:
        """Return the properties of the shape"""
        return self._properties.copy()

    def get_property(self, name) -> ShapeProperty:
        """Return the property of the shape with the given name"""
        for prop in self._properties:
            if prop.name == name:
                return prop
        return None

    def __str__(self):
        return f"{self.name}: {self.description}"

    def __repr__(self):
        return f"Shape({self.name})"

    def __eq__(self, other):
        if not isinstance(other, Shape):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @classmethod
    def load(cls, shapes_path: Union[str, Path], publicID: str = None) -> Dict[str, Shape]:
        """
        Load the shapes from the graph
        """
        shapes_graph = Graph()
        shapes_graph.parse(shapes_path, format="turtle", publicID=publicID)
        logger.debug("Shapes graph: %s" % shapes_graph)

        # extract shapeNode triples from the shapes_graph
        shapeNode = URIRef(SHACL_NS + "NodeShape")
        shapes_nodes = shapes_graph.triples((None, RDF.type, shapeNode))
        logger.debug("Shapes nodes: %s" % shapes_nodes)
        # create a shape object for each shape node
        shapes: Dict[str, Shape] = {}
        for shape_node, _, _ in shapes_nodes:
            logger.debug(f"Processing Shape Node: {shape_node}")
            shape = Shape(shape_node, shapes_graph)
            shapes[str(shape).replace(publicID, "")] = shape

        return shapes


class ViolationShape:

    def __init__(self, shape_node: Node, graph: Graph) -> None:
        # check the input
        assert isinstance(shape_node, Node), "Invalid shape node"
        assert isinstance(graph, Graph), "Invalid graph"

        # store the input
        self._shape_node = shape_node
        self._graph = graph

        # create a graph for the shape
        shape_graph = Graph()
        shape_graph += graph.triples((shape_node, None, None))
        self.shape_graph = shape_graph

        # serialize the graph in json-ld
        shape_json = shape_graph.serialize(format="json-ld")
        shape_obj = json.loads(shape_json)
        logger.debug("Shape JSON: %s" % shape_obj)
        try:
            self.shape_json = shape_obj[0]
        except Exception as e:
            logger.error("Error parsing shape JSON: %s" % e)
            # if logger.isEnabledFor(logging.DEBUG):
            #     logger.exception(e)
            # raise e
            pass

    @property
    def node(self) -> Node:
        return self._shape_node

    @property
    def graph(self) -> Graph:
        return self._graph

    @property
    def name(self):
        return self.shape_json[f'{SHACL_NS}name'][0]['@value']

    @property
    def description(self):
        return self.shape_json[f'{SHACL_NS}description'][0]['@value']

    @property
    def path(self):
        return self.shape_json[f'{SHACL_NS}path'][0]['@id']

    @property
    def nodeKind(self):
        nodeKind = self.shape_json.get(f'{SHACL_NS}nodeKind', None)
        if nodeKind:
            return nodeKind[0]['@id']
        return None
