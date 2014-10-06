
from unittest import main as run_tests
from unittest import TestCase

class Graph(object):
	def __init__(self):
		self.nodes = {}

	def add(self, node):
		self.nodes[node.name] = node

	def query_from(self, node_name):
		return Query(self, node_name)

	def find(self, node_name):
		return self.nodes[node_name]

class Query(object):

	ALL_RELATIONSHIPS = "*"
	SEARCH_FORWARDS = "forwards"
	SEARCH_BACKWARDS = "backwards"

	def __init__(self, graph, from_node_name):
		self.from_node_name = from_node_name
		self.relationship_type = Query.ALL_RELATIONSHIPS
		self.search_direction = Query.SEARCH_FORWARDS
		self.graph = graph
		self.to_type = Node.ALL_TYPE

	def related_by(self, relationship_type, reverse = False):
		self.relationship_type = relationship_type
		if(reverse):
			self.search_direction = Query.SEARCH_BACKWARDS
		return self

	def to_node_type(self, type):
		self.to_type = type
		return self

	def execute(self):
		from_node = self.graph.find(self.from_node_name)
		node_relationships = self._node_relationships(from_node)
		return list(map(self._relationship_to_node, filter(self._filter, node_relationships)))

	def execute_sub_query(self, callback):
		previous_results = self.execute()
		new_results = set([])
		for node in previous_results:
			query = Query(self.graph, node.name)
			callback(query)
			results = query.execute()
			new_results.update(set(results))
		return list(filter(lambda node: node.name != self.from_node_name, new_results))

	def _filter(self, rel):
		return (rel[0] == self.relationship_type or rel[0] == Query.ALL_RELATIONSHIPS) and rel[1].type == self.to_type
	
	def _node_relationships(self, node):
		if(self.search_direction == Query.SEARCH_FORWARDS):
			return node.from_relationships
		else:
			return node.to_relationships

	def _relationship_to_node(self, rel):
		return rel[1]


class Node(object):

	ALL_TYPE = "*"

	def __init__(self, name, type = None, callback = None):
		self.name = name
		self.from_relationships = []
		self.to_relationships = []
		self.type = type or Node.ALL_TYPE
		self._callback = callback
		self._changed()

	def add_relationship(self, relationship, to_node):
		self.from_relationships.append((relationship, to_node))
		to_node.to_relationships.append((relationship, self))
		self._changed()
		to_node._changed()

	def _changed(self):
		if(self._callback is not None):
			self._callback(self)

class NodeFactory:

	def __init__(self, callback):
		self._callback = callback

	def create(self, name, type=None):
		return Node(name, type=type, callback=self._callback)

class TestMe(TestCase):
	
	def test_can_add_node_to_graph(self):
		graph = Graph()
		node = Node("John Cleese")
		graph.add(node)
		self.assertTrue(node.name in graph.nodes)

	def test_can_add_relationship_to_nodes(self):
		graph = Graph()
		john_cleese = Node("John Cleese")
		life_of_brian = Node("The Life of Brian")
		graph.add(john_cleese)
		graph.add(life_of_brian)
		john_cleese.add_relationship("Acted In", life_of_brian)
		john_cleese_acted_in = graph \
								.query_from("John Cleese") \
								.related_by("Acted In") \
								.execute()
		self.assertEqual(john_cleese_acted_in, [life_of_brian])

	def test_can_query_backwards(self):
		graph = Graph()
		john_cleese = Node("John Cleese")
		life_of_brian = Node("The Life of Brian")
		michael_palin = Node("Michael Palin")
		graph.add(john_cleese)
		graph.add(life_of_brian)
		graph.add(michael_palin)
		john_cleese.add_relationship("Acted In", life_of_brian)
		michael_palin.add_relationship("Acted In", life_of_brian)
		actors_in_lob = graph \
							.query_from("The Life of Brian") \
							.related_by("Acted In", reverse=True) \
							.execute()
		self.assertEqual(actors_in_lob, [john_cleese, michael_palin])

	def test_can_filter_to_by_label(self):
		graph = Graph()
		john_cleese = Node("John Cleese")
		life_of_brian = Node("The Life of Brian", type = "Film")
		fawlty_towers = Node("Fawlty Towers", type = "TV Show")
		graph.add(john_cleese)
		graph.add(life_of_brian)
		graph.add(fawlty_towers)
		john_cleese.add_relationship("Acted In", life_of_brian)
		john_cleese.add_relationship("Acted In", fawlty_towers)
		actors_in_lob = graph \
							.query_from("John Cleese") \
							.related_by("Acted In") \
							.to_node_type("TV Show") \
							.execute()
		self.assertEqual(actors_in_lob, [fawlty_towers])

	def test_can_find_multi_setp_queries(self):
		graph = Graph()
		john_cleese = Node("John Cleese")
		life_of_brian = Node("The Life of Brian")
		michael_palin = Node("Michael Palin")
		graph.add(john_cleese)
		graph.add(life_of_brian)
		graph.add(michael_palin)
		john_cleese.add_relationship("Acted In", life_of_brian)
		michael_palin.add_relationship("Acted In", life_of_brian)
		in_things_with_john_cleese = graph \
						.query_from("John Cleese") \
						.related_by("Acted In") \
						.execute_sub_query(lambda query: query.related_by("Acted In", reverse=True)) \

		self.assertEqual(in_things_with_john_cleese, [michael_palin])

	def test_can_get_node_changed_events_on_created(self):
		self.created_node = None
		def node_callback(new_node):
			self.created_node = new_node
		new_node = NodeFactory(node_callback).create("Dead Parrot")
		self.assertEqual(self.created_node, new_node)

	def test_can_get_node_changed_events_on_changed(self):
		self.changed_node = []
		self.calls = 0
		def node_callback(new_node):
			self.calls += 1
			self.changed_nodes.append(new_node)
		dead_parrot = NodeFactory(node_callback).create("Dead Parrot")
		Node("Michael Palin").add_relationship("Acted In", dead_parrot)

		self.assertEqual(self.calls, 2)
		self.assertEqual(self.changed_node[0], dead_parrot)
		self.assertEqual(self.changed_node[1], dead_parrot)


if __name__ == "__main__":
	run_tests()