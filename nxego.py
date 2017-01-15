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
import datetime

CHILDREN_AGE_DIFFERENCE_RANGE = range(20, 35)
SPOUSE_AGE_DIFFERENCE_RANGE = range(0, 5)

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

    person = people[person_no-1]
    person_id = person['id'] # choose person id
    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby/' + person_id + '.json?layers[]=graph')
    person_json = r.json()

    people_ids = []

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
                people_ids.append(node['id'])
                G.add_node(node['id'], name=node['data']['imiona'] + ' ' + node['data']['nazwisko'],
                           group='osoba', attributes=node['data'])
        # institution node
        elif 'podmiot' in node['id']:
            G.add_node(node['id'], name=node['data']['nazwa'], attributes=node['data'],
                       group='podmiot')

    # create edges
    for edge in person_json['layers']['graph']['relationships']:
        G.add_edge(edge['start'], edge['end'], relation=edge['type'])

    relatives = get_relatives(people_ids, person_json['data']['krs_osoby.nazwisko'], person['id'])
    add_relatives_to_graph(relatives, person_json, G)

    # dump G graph to JSON file
    d = json_graph.node_link_data(G)
    json.dump(d, open(os.getcwd()+'/static/ego.json', 'w'), indent=4, separators=(',', ': '))


def get_relatives(people, ego_name, ego_id):

    relatives = []

    people_ids = list(map(lambda person_id: person_id.replace('osoba', ''), people))
    for id in people_ids:
        new_relatives = get_related_people_from_ego(id, ego_name, ego_id)
        relatives.extend(new_relatives)

    return relatives


def get_related_people_from_ego(person_id, ego_name, ego_id):

    r = requests.get('https://api-v3.mojepanstwo.pl/dane/krs_osoby/' + person_id + '.json?layers[]=graph')
    person_json = r.json()

    relatives = []

    for person in person_json['layers']['graph']['nodes']:
        id = person['id'].replace('osoba', '')
        if 'osoba' in person['id'] and id != ego_id:
            if match_names(ego_name, person['data']['nazwisko']):
                relatives.append(person)

    return relatives


def match_names(ego_name, person_name):
    if (ego_name == person_name or has_similar_names(ego_name, person_name) or
        name_contains(ego_name, person_name) or name_contains(person_name, ego_name)):
        return True
    else:
        return False


def has_similar_names(a, b):
    return a[:-1] == b[:-1]

def name_contains(name, other_name):
    if name[:-1].endswith(other_name[:-1]):
        return True
    else:
        return False

def add_relatives_to_graph(relatives, person, graph):

    person_graph_id = person['layers']['graph']['root']

    for relative in relatives:

        person_gender = person['data']['krs_osoby.plec']
        relative_gender = relative['data']['plec']
        person_birth_date = person['data']['krs_osoby.data_urodzenia']
        relative_birth_date = relative['data']['data_urodzenia']

        age_difference = get_age_difference(person_birth_date, relative_birth_date)

        #is spouse
        if abs(age_difference) in SPOUSE_AGE_DIFFERENCE_RANGE and person_gender != relative_gender:
            graph.add_node(relative['id'], name=relative['data']['imiona'] + ' ' + relative['data']['nazwisko'],
                       group='rodzina', attributes=relative['data'])
            graph.add_edge(person_graph_id, relative['id'], relation='MOŻLIWE MAŁŻEŃSTWO')
        #is child
        elif abs(age_difference) in CHILDREN_AGE_DIFFERENCE_RANGE:

            graph.add_node(relative['id'], name=relative['data']['imiona'] + ' ' + relative['data']['nazwisko'],
                       group='rodzina', attributes=relative['data'])

            if age_difference < 0:
                graph.add_edge(person_graph_id, relative['id'], relation='MOŻLIWE DZIECKO')
            else:
                graph.add_edge(person_graph_id, relative['id'], relation='MOŻLIWY RODZIC')


def get_age_difference(birthdate_1, birthdate_2):

    year1 = extract_birth_year(birthdate_1)
    year2 = extract_birth_year(birthdate_2)

    return year1 - year2


def extract_birth_year(birth_string):
    date = datetime.datetime.strptime(birth_string, '%Y-%m-%d').date()
    return date.year