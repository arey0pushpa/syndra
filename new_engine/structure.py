"""
This file allows you to build "structures", which are a syntactic sugar
for asserting that the pregraph or postgraph of a rule has certain properties.
"""

import z3


class Structure(object):
    """Abstract class Structure."""
    def _assert(self, graph, solver):
        raise NotImplementedError("Implement _assert in subclasses.")

    def bound(self, other_structure):
        """Return a new Structure object for this structure bound to another."""
        return Bound(self, other_structure)

    def labeled(self, label):
        """Return a new Structure object for this structure having a label."""
        return Labeled(self, label)

    def with_site(self, other_structure):
        """Return a new Structure object for this structure having another as a site."""
        return WithSite(self, other_structure)


class Agent(Structure):
    """An Agent is a simple structure: one node with a name."""
    def __init__(self, name):
        self.name = name

    def central_node_label(self):
        """Keeps track of the 'central' node in a given structure."""
        return self.name

    def _assert(self, graph, solver):
        """Return a z3 predicate asserting this structure is in `graph`."""
        has = solver.Graph.has(graph)
        node = solver.node_interner.get_node(self.central_node_label())
        has_node = z3.Select(has, node)
        return has_node


class Bound(Structure):
    """This structure represents one structure bound to another structure.
    Do not instantiate this directly; instead use A.bound(B).
    """
    def __init__(self, structure_1, structure_2):
        self.structure_1 = structure_1
        self.structure_2 = structure_2

    def central_node_label(self):
        """Keeps track of the 'central' node in a given structure."""
        return self.structure_1.central_node_label()

    def _assert(self, graph, solver):
        """Return a z3 predicate asserting this structure is in `graph`."""
        links = solver.Graph.links(graph)
        node_1 = solver.node_interner.get_node(self.structure_1.central_node_label())
        node_2 = solver.node_interner.get_node(self.structure_2.central_node_label())
        edge = solver.Edge.edge(node_1, node_2)
        has_link = z3.Select(links, edge)
        return z3.And(has_link,
                      self.structure_1._assert(graph, solver),
                      self.structure_2._assert(graph, solver))


class WithSite(Structure):
    """This is a structure for requiring one structure to have another as a site.
    Do not instantiate this directly; instead use A.with_site(B)."""
    def __init__(self, structure_1, structure_2):
        self.structure_1 = structure_1
        self.structure_2 = structure_2

    def central_node_label(self):
        """Keeps track of the 'central' node in a given structure."""
        return self.structure_1.central_node_label()

    def _assert(self, graph, solver):
        """Return a z3 predicate asserting this structure is in `graph`."""
        parents = solver.Graph.parents(graph)
        node_1 = solver.node_interner.get_node(self.structure_1.central_node_label())
        node_2 = solver.node_interner.get_node(self.structure_2.central_node_label())
        edge = solver.Edge.edge(node_1, node_2)
        has_parent = z3.Select(parents, edge)
        return z3.And(has_parent,
                      self.structure_1._assert(graph, solver),
                      self.structure_2._assert(graph, solver))


class Labeled(Structure):
    """This is a structure for requiring that a structure has a label.
    Do not instantiate this directly; instead use A.labeled(B)."""
    def __init__(self, structure, label):
        self.structure = structure
        self.label = label

    def central_node_label(self):
        """Keeps track of the 'central' node in a given structure."""
        return self.structure.central_node_label()

    def _assert(self, graph, solver):
        """Return a z3 predicate asserting this structure is in `graph`."""
        labelmap = solver.Graph.labelmap(graph)
        node = solver.node_interner.get_node(self.structure.central_node_label())
        labelset = z3.Select(labelmap, node)  # returns a labelset
        label = solver.string_interner.get_int_or_add(self.label)
        label_present = z3.Select(labelset, label) # returns a bool
        return z3.And(label_present,
                      self.structure._assert(graph, solver))


def Label(label_string):
    """Create a label string with prefix 'label_'."""
    # just to make sure nobody gets messy with using strings as labels -- use
    # variables as labels instead, so that Python raises an error if you misspell
    return "label_" + label_string
