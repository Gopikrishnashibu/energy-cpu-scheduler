# app.py — Flask Web Server

from flask import Flask, render_template, request, jsonify
from scheduler import DVFSScheduler

app = Flask(__name__)

DEFAULT_TASKS = {
    'light': [
        {'pid': 101, 'name': 'UI_Render',  'burst': 8,  'priority': 'high', 'power': 2.1},
        {'pid': 102, 'name': 'NetIO',      'burst': 5,  'priority': 'low',  'power': 0.8},
        {'pid': 103, 'name': 'Sensor',     'burst': 3,  'priority': 'med',  'power': 0.5},
        {'pid': 104, 'name': 'BgSync',     'burst': 6,  'priority': 'low',  'power': 1.2},
    ],
    'medium': [
        {'pid': 101, 'name': 'UI_Render',  'burst': 8,  'priority': 'high', 'power': 2.1},
        {'pid': 102, 'name': 'NetIO',      'burst': 5,  'priority': 'low',  'power': 0.8},
        {'pid': 103, 'name': 'Sensor',     'burst': 3,  'priority': 'med',  'power': 0.5},
        {'pid': 104, 'name': 'BgSync',     'burst': 6,  'priority': 'low',  'power': 1.2},
        {'pid': 105, 'name': 'ML_Infer',   'burst': 12, 'priority': 'high', 'power': 3.4},
        {'pid': 106, 'name': 'AudioProc',  'burst': 4,  'priority': 'med',  'power': 0.9},
    ],
    'heavy': [
        {'pid': 101, 'name': 'UI_Render',  'burst': 8,  'priority': 'high', 'power': 2.1},
        {'pid': 102, 'name': 'NetIO',      'burst': 5,  'priority': 'low',  'power': 0.8},
        {'pid': 103, 'name': 'Sensor',     'burst': 3,  'priority': 'med',  'power': 0.5},
        {'pid': 104, 'name': 'BgSync',     'burst': 6,  'priority': 'low',  'power': 1.2},
        {'pid': 105, 'name': 'ML_Infer',   'burst': 12, 'priority': 'high', 'power': 3.4},
        {'pid': 106, 'name': 'AudioProc',  'burst': 4,  'priority': 'med',  'power': 0.9},
        {'pid': 107, 'name': 'GpuTask',    'burst': 10, 'priority': 'high', 'power': 4.1},
        {'pid': 108, 'name': 'FileIndex',  'burst': 7,  'priority': 'low',  'power': 1.0},
    ],
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    algorithm     = data.get('algorithm', 'dvfs')
    workload      = data.get('workload', 'medium')
    thermal_limit = int(data.get('thermal_limit', 80))
    custom_tasks  = data.get('custom_tasks', None)

    tasks = custom_tasks if custom_tasks else DEFAULT_TASKS.get(workload, DEFAULT_TASKS['medium'])

    scheduler = DVFSScheduler(thermal_limit=thermal_limit)
    result = scheduler.schedule(tasks, algorithm=algorithm)
    return jsonify(result)
    print(result['log'])

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)