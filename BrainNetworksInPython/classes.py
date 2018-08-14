import numpy as np
import networkx as nx
import pandas as pd
from BrainNetworksInPython.make_graphs import assign_node_names, \
    assign_node_centroids, anatomical_copy, threshold_graph, \
    weighted_graph_from_matrix, anatomical_node_attributes, \
    anatomical_graph_attributes, get_random_graphs, is_nodal_match, \
    is_anatomical_match
from BrainNetworksInPython.graph_measures import assign_interhem, \
    shortest_path, participation_coefficient, assign_nodal_distance, \
    calc_nodal_partition, calculate_global_measures, small_coefficient


class BrainNetwork(nx.classes.graph.Graph):
    def __init__(self,
                 network=None,
                 parcellation=None,
                 centroids=None,):
        '''
        Lightweight subclass of networkx.classes.graph.Graph
        FILL
        '''
        # ============== Create graph ================
        nx.classes.graph.Graph.__init__(self)
        if network is not None:
            if isinstance(network, nx.classes.graph.Graph):
                # Copy graph
                self.__dict__.update(network.__dict__)

            else:
                # Create weighted graph from a dataframe or
                # numpy array
                if isinstance(network, pd.DataFrame):
                    M = network.values
                elif isinstance(network, np.ndarray):
                    M = network
                network = weighted_graph_from_matrix(M, create_using=self)

        # ===== Give anatomical labels to nodes ======
        if parcellation is not None:
            # assign parcellation names to nodes
            assign_node_names(self,
                              parcellation,)
        if centroids is not None:
            # assign centroids to nodes
            assign_node_centroids(self, centroids)
        # Tell BrainNetwork class which attributes to consider "anatomical"
        # and therefore preserve when copying or creating new graphs
        self.set_anatomical_node_attributes = anatomical_node_attributes
        self.set_anatomical_graph_attributes = anatomical_graph_attributes

    def threshold(self, cost, mst=True):
        '''
        Returns a new graph G FILL
        '''
        return threshold_graph(self, cost, mst=True)

    def partition(self):
        '''
        FILL
        '''
        if 'partition' not in self.graph:
            nodal_partition, module_partition = calc_nodal_partition(self)
            nx.set_node_attributes(self, nodal_partition, name='module')
            self.graph['partition'] = module_partition
        return self.graph['partition']

    def calculate_nodal_measures(
            self,
            force=False,
            measure_list=None,
            additional_measures=None):
        '''
        Calculate nodal measures of BrainNetwork en masse.
        Returns nothing, but stores nodal measures as nodal attributes
        which can be accessed using brainnetwork.export_nodal_measures()

        By default calculates:
        * nodal_partition
        * degree
        * closeness
        * betweenness
        * shortest_path_length
        * clustering
        * participation_coefficient
        * interhem
        * interhem_proportion
        * total_dist *(euclidean length of adjacent eges)*
        * average_dist *(euclidean length of adjacent eges)*

        You can pass a list of these keys to measure_list to specify which
        of the default measures you want to calculate.
        You can also pass a dictionary of `measure name: measure method` pairs
        to measure_dict, where `measure method` is a function that take a graph
        as input and returns a dictionary keyed by the nodes of G. These
        measures will be calculated by applying `measure_method` to
        brainnetwork and added to the nodal attributes.

        Setting `force=True` will cause recalculate any measures that already
        exist in the nodal attributes. Default behaviour is not to recalculate.
        '''

        # ==== SET UP ================================
        # If you haven't created the nodal partition
        # then calculate it here
        self.partition()
        # ==== DESCRIBE MEASURES =====================
        nodal_measure_dict = {
            "degree": (lambda x: dict(nx.degree(x))),
            "closeness": nx.closeness_centrality,
            "betweenness": nx.betweenness_centrality,
            "shortest_path_length": nx.betweenness_centrality,
            "clustering": nx.clustering,
            "participation_coefficient": (lambda x: participation_coefficient(
                                            x,
                                            x.graph['partition']))
            }

        if measure_list is not None:
            nodal_measure_dict = {key: value
                                  for key, value in nodal_measure_dict.items()
                                  if key in measure_list}
        if additional_measures is not None:
            nodal_measure_dict.update(additional_measures)

        # ==== CALCULATE MEASURES ====================

        def calc_nodal_measure(self, measure, method, force=False):
            if (not nx.get_node_attributes(self, name=measure)) or force:
                nx.set_node_attributes(self,
                                       name=measure,
                                       values=method(self))

        for measure, method in nodal_measure_dict.items():
            calc_nodal_measure(self, measure, method, force=force)

        # ---- Euclidean distance and ------
        # ---- interhem proportion --------
        if self.graph.get('centroids'):
            if ((measure_list is None) or ('nodal_distance' in measure_list)):
                assign_nodal_distance(self)
            if ((measure_list is None) or ('interhem' in measure_list)):
                assign_interhem(self)

    def export_nodal_measures(self, columns=None, as_dict=False):
        '''
        Returns the node attribute data from G as a pandas dataframe.
        '''
        if columns is not None:
            nodal_dict = {x: {u: v for u, v in y.items() if u in columns}
                          for x, y in self._node.items()}
        else:
            nodal_dict = self._node
        if as_dict:
            return nodal_dict
        df = pd.DataFrame(nodal_dict).transpose()
        return df

    def calculate_rich_club(self, force=False):
        '''
        FILL
        '''
        if ('rich_club' not in self.graph) or force:
            self.graph['rich_club'] = nx.rich_club_coefficient(
                                        self, normalized=False)
        return self.graph['rich_club']

    def calculate_global_measures(self, force=False, seed=None):
        '''
        FILL
        '''
        if ('global_measures' not in self.graph) or force:
            global_measures = calculate_global_measures(
                self, partition=dict(self.nodes(data="module")))
            self.graph['global_measures'] = global_measures
        else:
            global_measures = calculate_global_measures(
                self,
                partition=dict(self.nodes(data="module")),
                existing_global_measures=self.graph['global_measures'])
            self.graph['global_measures'].update(global_measures)
        return self.graph['global_measures']

    def anatomical_copy(self):
        '''
        FILL
        '''
        return anatomical_copy(self,
                               nodal_keys=self.anatomical_node_attributes,
                               graph_keys=self.anatomical_graph_attributes)

    def set_anatomical_node_attributes(self, names):
        '''
        Set the list of node attribute keys that are to be considered
        anatomical. These will be preserved when creating anatomical graph
        copies.
        '''
        self.anatomical_node_attributes = names

    def anatomical_graph_attributes(self, names):
        '''
        Set the list of graph attribute keys that are to be considered
        anatomical. These will be preserved when creating anatomical graph
        copies.
        '''
        self.anatomical_graph_attributes = names


class GraphBundle(dict):
    '''
    FILL
    '''
    def __init__(self, graph_list, name_list):
        '''
        FILL
        '''
        dict.__init__(self)
        self.add_graphs(graph_list, name_list)

    def add_graphs(self, graph_list, name_list=None):
        if name_list is None:
            name_list = [len(self) + i for i in range(len(graph_list))]
        elif len(name_list) != len(graph_list):
            raise
        for graph in graph_list:
            if not isinstance(graph, BrainNetwork):
                graph = BrainNetwork(graph)
        self.update({a: b for a, b in zip(name_list, graph_list)})

    def apply(self, graph_function):
        '''
        FILL
        '''
        global_dict = {}
        for name, graph in self.items():
            global_dict[name] = graph_function(graph)
        return global_dict

    def report_global_measures(self, as_dict=False):
        '''
        FILL
        '''
        global_dict = self.apply(lambda x: x.calculate_global_measures())
        if as_dict:
            return global_dict
        else:
            return pd.DataFrame.from_dict(global_dict).transpose()

    def report_rich_club(self, as_dict=False):
        '''
        FILL
        '''
        rc_dict = self.apply(lambda x: x.calculate_rich_club())
        if as_dict:
            return rc_dict
        else:
            return pd.DataFrame.from_dict(rc_dict).transpose()

    def create_random_graphs(self, key, n, name_list=None, name_scheme="_R"):
        '''
        FILL
        '''
        if name_list is None:
            # Choose q to be the smallest integer that is larger than all
            # integers already naming a random graph in brainnetwork
            q = len(self)
            while (key + name_scheme + str(q) not in self) and (q > 0):
                q -= 1
            name_list = [key + name_scheme + str(i) for i in range(q+1, q+1+n)]
        self.add_graphs(get_random_graphs(self[key], n=n), name_list=name_list)

    def report_small_world(self, graph_name):
        '''
        Calculate the small coefficient of graph_name relative to
        graph in GraphBundle.

        Returns a dictionary mapping graph_names to small coefficients.

        graph_name should be a key for a graph in GraphBundle.
        '''
        small_world_dict = self.apply(
            lambda x: small_coefficient(self['graph_name'], x))
        return small_world_dict

    def nodal_matches(self):
        '''
        Returns True if all graphs have the same node set
        '''
        H = list(self.values())[0]
        return (False not in [is_nodal_match(H, G) for G in self.values()])

    def anatomical_matches(self,
                           nodal_keys=anatomical_node_attributes(),
                           graph_keys=anatomical_graph_attributes()):
        '''
        Returns False if graphs are not all pairwise anatomical matches
        as defined in make_graphs.is_anatomical_match.
        '''
        H = list(self.values())[0]
        return (False not in
                [is_anatomical_match(
                    H,
                    G,
                    nodal_keys=nodal_keys,
                    graph_keys=graph_keys)
                 for G in self.values()])
