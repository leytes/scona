import numpy as np
import networkx as nx
import pandas as pd
from BrainNetworksInPython.make_graphs import assign_node_names, \
    assign_node_centroids, anatomical_copy, threshold_graph, \
    weighted_graph_from_matrix, get_random_graphs
from BrainNetworksInPython.graph_measures import assign_interhem, \
    shortest_path, participation_coefficient, assign_nodal_distance, \
    calc_nodal_partition, calculate_global_measures, small_coefficient


class BrainNetwork(nx.classes.graph.Graph):
    def __init__(self,
                 network=None,
                 parcellation=None,
                 centroids=None,
                 names_308_style=False):
        '''
        Lightweight subclass of networkx.classes.graph.Graph
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
                network = weighted_graph_from_matrix(M)
                self.__dict__.update(network.__dict__)

        # ===== Give anatomical labels to nodes ======
        if parcellation is not None:
            # assign parcellation names to nodes
            assign_node_names(self,
                              parcellation,
                              names_308_style=names_308_style)
        if centroids is not None:
            # assign centroids to nodes
            assign_node_centroids(self, centroids)

    def threshold(self, cost, mst=True):
        '''
        FILL
        '''
        return threshold_graph(self, cost, mst=True)

    def partition(self):
        '''
        FILL
        '''
        if 'partition' not in self.graph:
            nodal_partition, module_partition = calc_nodal_partition(self)
            nx.set_node_attributes('module', nodal_partition)
            self.graph['partition'] = module_partition
        return self.graph['partition']

    def calculate_nodal_measures(self):
        '''
        Calculates
        '''

        # ==== SET UP ======================
        # If you haven't passed the nodal partition
        # then calculate it here
        self.partition()

        # ==== MEASURES ====================
        # ---- Degree ----------------------
        nx.set_node_attributes('degree', dict(self.degree))
        # ---- Closeness -------------------
        nx.set_node_attributes('closeness', nx.closeness_centrality(self))
        # ---- Betweenness -----------------
        nx.set_node_attributes('betweenness', nx.betweenness_centrality(self))
        # ---- Shortest path length --------
        nx.set_node_attributes('shortest_path_length',
                               shortest_path(self))
        # ---- Clustering ------------------
        nx.set_node_attributes('clustering', nx.clustering(self))
        # ---- Participation coefficent ----
        nx.set_node_attributes('participation_coefficient',
                               participation_coefficient(
                                self,
                                self.graph['partition']), )

        # ---- Euclidean distance and ------
        # ---- interhem proportion --------
        if self.graph.get('centroids'):
            assign_nodal_distance(self)
            assign_interhem(self)

    def export_nodal_measures(self, columns=None, index='name'):
        '''
        Returns the node attribute data from G as a pandas dataframe.
        '''
        df = pd.DataFrame(self._node, columns=columns).transpose()
        return df.set_index(index)

    def calculate_rich_club(self, force=False):
        '''
        FILL
        '''
        if ('rich_club' not in self.graph) or force:
            self.graph['rich_club'] = nx.rich_club_coefficient(
                                        self, normalized=False)
        return self.graph['rich_club']

    def calculate_global_measures(self, force=False):
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
        return anatomical_copy(self)


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

    def create_random_graphs(self, key, n, name_list=None):
        '''
        FILL
        '''
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
