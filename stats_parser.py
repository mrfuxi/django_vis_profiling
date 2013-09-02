import copy
import pstats
import networkx as nx


def pstats_to_json(stats):
    """
    Transforms pstats to structure JSON structure
    """

    if isinstance(stats, str):
        stats = pstats.Stats(stats)

    elif not isinstance(stats, pstats.Stats):
        raise TypeError("Stats object can be either file name or pstats.Stats. Given: %s" % type(stats))

    json_data = travers_stats(stats.stats)

    pie_data = prepare_graph_data(json_data)
    calls = create_call_structure(json_data)

    graphs = {
        "pie": pie_data,
        "bars": json_data.values(),
        "calls": calls,
    }

    return graphs, stats.total_tt


def tuple_to_key(data, force_simple=False):
    """
    Creates key/label for entry from stats
    """

    (source, line, method) = data

    if force_simple:
        return method

    if line == 0 or source == "~":
        return method

    return "%s:%i(%s)" % (source, line, method)


def travers_stats(data):
    """
    Converts stats into structure compatible with JSON
    """

    if isinstance(data, dict):
        return dict(map(travers_stats, data.iteritems()))

    elif isinstance(data, (tuple, list)) and len(data) == 2:
        key, values = data

        labels = ("ncalls", "pcalls", "tottime", "cumtime", "parents")
        values = dict(zip(labels, map(travers_stats, values)))
        values["short_name"] = tuple_to_key(key, force_simple=True)
        values["name"] = tuple_to_key(key, force_simple=False)

        return (tuple_to_key(key, force_simple=False), values)

    return data


def prepare_graph_data(json_data):
    graph = nx.DiGraph()

    attr_labels = ("ncalls", "pcalls", "tottime", "cumtime", "short_name")

    for k, v in json_data.iteritems():
        graph.add_node(k, attr_dict={al: v[al] for al in attr_labels})

        for pk, pv in v.get("parents", {}).iteritems():
            graph.add_edge(pk, k, attr_dict=pv)

    for cycle in nx.simple_cycles(graph):
        if len(cycle) == 2:
            u, v = cycle[0], cycle[1]
        else:
            u, v = cycle[0], cycle[0]

        if graph.has_edge(u, v):
            graph.remove_edge(u, v)

    root_nodes = map(lambda (n, d): n, filter(lambda (n, d): d == 0,  graph.in_degree_iter()))

    def build_chart(node):
        if isinstance(node, (tuple, list)):
            name = "root"
            nodes = map(build_chart, node)
            data = {"cumtime": sum(map(lambda n: json_data[n].get("cumtime", 0), node))}
            #data = None
        else:
            name = node
            data = {al: json_data[node][al] for al in attr_labels}
            nodes = [build_chart(edge[1]) for edge in graph.out_edges_iter(node)]

        new_node = dict([("name", name),
                         ("children", nodes)])

        if data:
            new_node.update(data)
            if "tottime" in data:
                new_node["value"] = data["tottime"]

        if nodes and data:
            inline_node = copy.deepcopy(new_node)
            inline_node["name"] = "(inline) %s" % name
            inline_node["inline"] = "1"
            del inline_node["children"]

            nodes.append(inline_node)

        if not nodes:
            del new_node["children"]

        return new_node

    graph_data = build_chart(root_nodes)

    return graph_data


def create_call_structure(json_data):
    nodes = copy.deepcopy(json_data.values())
    nodes = sorted(nodes, key=lambda n: n.get("cumtime", 0), reverse=True)

    links = []
    ids = {}
    for i, node in enumerate(nodes):
        ids[node["name"]] = i
        node["id"] = i

        if "parents" in node:
            for parent in node["parents"].itervalues():
                link = {"source": parent["name"],
                        "target": i,
                        }
                links.append(link)
            del node["parents"]

    for link in links:
        link["value"] = nodes[link["target"]]["cumtime"]
        link["source"] = ids[link["source"]]

    calls = {"nodes": nodes,
             "links": links,
             }

    return calls
