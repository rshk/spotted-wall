"""
:author: samu
:created: 3/5/13 4:28 PM
"""

from flask import Flask, render_template, request, redirect, url_for


class MyFlask(Flask):
    spotted_wall = None  # Will be fitted in other thread..
    pass

app = MyFlask(__name__)


@app.route("/")
def index():
    spotted_wall = app.spotted_wall
    return render_template(
        'index.jinja',
        messages=spotted_wall.list_messages())


@app.route('/add', methods=['GET', 'POST'])
def add_message():
    if request.method == 'POST':
        spotted_wall = app.spotted_wall
        spotted_wall.add_message(request.form['message'])
        return redirect(url_for('index'))
    return render_template('add.jinja')
