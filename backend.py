import sys
import os
import json
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

# Import the local agent (with memory and SQLite/FAISS connected)
from local_agent import agent_executor

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
        
    def generate():
        try:
            # Stream intermediate steps and final output
            for chunk in agent_executor.stream({"input": user_message}):
                if "actions" in chunk:
                    for action in chunk["actions"]:
                        status_msg = f"⚙️ Thinking... using tool: {action.tool}"
                        data_str = json.dumps({"type": "status", "msg": status_msg})
                        yield f"data: {data_str}\n\n"
                elif "output" in chunk:
                    data_str = json.dumps({"type": "final", "msg": chunk['output']})
                    yield f"data: {data_str}\n\n"
        except Exception as e:
            error_str = json.dumps({"type": "error", "msg": str(e)})
            yield f"data: {error_str}\n\n"

    return Response(generate(), mimetype='text/event-stream')

import sqlite3
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    db_path = 'data/tickets.db'
    if not os.path.exists(db_path):
        return jsonify({'error': 'Database not found'}), 404
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tickets")
        total_tickets = cursor.fetchone()[0]
        
        cursor.execute("SELECT type, COUNT(*) FROM tickets WHERE type IS NOT NULL AND type != '' GROUP BY type ORDER BY COUNT(*) DESC LIMIT 5")
        type_data = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
        
        cursor.execute("SELECT priority, COUNT(*) FROM tickets WHERE priority IS NOT NULL AND priority != '' GROUP BY priority ORDER BY COUNT(*) DESC")
        priority_data = [{"label": row[0], "value": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total_tickets': total_tickets,
            'type_data': type_data,
            'priority_data': priority_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask Server at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)
