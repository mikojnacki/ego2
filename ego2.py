"""
Flask app module - server logic
"""

import sys
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import nxego


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_query', methods=['POST'])
def get_query():
    query = request.form['query']
    return redirect(url_for('show_list', query=query))


@app.route('/show_list')
def show_list():
    global _people
    query = request.args['query']
    people = nxego.search_people(query)
    _people = people # save result to global variable
    return render_template('list.html', query=query, people=people)


@app.route('/get_person', methods=['POST'])
def get_person():
    person_no = request.form['user_id']
    return redirect(url_for('draw_graph', person_no=person_no))


@app.route('/draw_graph')
def draw_graph():
    global _people
    person_no = int(request.args['person_no'])
    nxego.create_graph(person_no, _people) # all NetworkX logic here
    print("dwa")
    return redirect(url_for('static', filename='ego.html'))


def main():
    global _people # global variable that stores nxego.search_people(query)
    app.run()

if __name__ == '__main__':
    try:
        main()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
