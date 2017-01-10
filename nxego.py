"""
Python module including:
- KRS API requesting logic
- NetworkX graph creation logic
"""

import os
import networkx as nx
from networkx.readwrite import json_graph
import requests
import json


def search_people(query):
    """
    GET request from KRS API
    search people with given name nad last name
    return list of dicts of people to choose
    """

    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby.json?conditions[q]='+query)
    j = r.json()

    people = []
    count = 1
    for person in j['Dataobject']:
        people.append({'no':count,'id':person['id'], 'name':person['data']['krs_osoby.imiona']+' '+person['data']['krs_osoby.nazwisko'],
                       'date_of_birth':person['data']['krs_osoby.data_urodzenia']})
        count = count + 1

    # print('Wyszukane osoby: ')
    # for person in people:
    #     print(str(person['no']) + '\t' + person['name'] + ' ' + person['date_of_birth'] + '\n')

    return people  # lista słowników


def create_graph(person_no, people):
    """
    Choose person's id
    GET request from KRS API
    Create NetworkX Graph from person's JSON data
    Dump JSON graph data into /template subfolder
    """

    person_id = people[person_no-1]['id'] # choose person id
    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby/' + person_id + '.json?layers[]=graph')
    person_json = r.json()


    G = nx.Graph()
    # create nodes
    for node in person_json['layers']['graph']['nodes']:
        # person node
        if 'osoba' in node['id']:
            # ego person node
            if person_json['id'] in node['id']:
                G.add_node(node['id'], name=node['data']['imiona'] + ' ' + node['data']['nazwisko'],
                           group='ego', attributes=node['data'])
            # other person node
            else:
                G.add_node(node['id'], name=node['data']['imiona'] + ' ' + node['data']['nazwisko'],
                           group='osoba', attributes=node['data'])
        # institution node
        elif 'podmiot' in node['id']:
            G.add_node(node['id'], name=node['data']['nazwa'], attributes=node['data'],
                       group='podmiot')

    # create edges
    for edge in person_json['layers']['graph']['relationships']:
        G.add_edge(edge['start'], edge['end'], relation=edge['type'])

    # dump G graph to JSON file
    d = json_graph.node_link_data(G)
    json.dump(d, open(os.getcwd()+'/static/ego.json', 'w'))

