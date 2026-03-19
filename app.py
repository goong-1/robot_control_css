import threading
import time
import random
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# 현재 폴더(robot_m) 안에 robot_logs.db를 만듭니다!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///robot_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- [DB 테이블 구조] ---
class RobotLog(db.Model):
    __tablename__ = 'robot_log'
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50))
    battery = db.Column(db.Float)
    cpu = db.Column(db.Float)
    latency_ctrl = db.Column(db.Integer)
    latency_robot = db.Column(db.Integer)
    status = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.now)

# --- [로봇 시뮬레이터 (Mock)] ---
class RobotMockManager:
    def __init__(self):
        self.state = {
            "robot_id": "SEONGSU_03",
            "status": "moving",
            "battery_percent": 98.0,
            "battery_voltage": 49.0,
            "cpu_usage": 2.0,
            "memory_usage": 33.0,
            "latency_total": 55,
            "latency_robot": 93
        }
        self.running = True
        self.thread = threading.Thread(target=self._update_mock_data, daemon=True)
        self.thread.start()

    def _update_mock_data(self):
        while self.running:
            time.sleep(1) 
            if self.state["status"] == "moving":
                if self.state["battery_percent"] > 0:
                    self.state["battery_percent"] -= random.uniform(0.01, 0.5)
            
            self.state["cpu_usage"] = round(random.uniform(1.0, 15.0), 1)
            self.state["memory_usage"] = round(random.uniform(30.0, 35.0), 1)
            self.state["latency_total"] = int(random.uniform(40, 80))
            self.state["latency_robot"] = int(random.uniform(80, 120))

    def get_state(self):
        state_copy = self.state.copy()
        state_copy["battery_percent"] = round(state_copy["battery_percent"], 1)
        return state_copy

robot_manager = RobotMockManager()

# --- [API 라우터: 프론트엔드와 소통하는 창구] ---
@app.route('/')
def dashboard():
    # templates 폴더 안의 dashboard.html을 띄워줍니다!
    return render_template('dashboard.html')

@app.route('/api/robot_stats')
def get_robot_stats():
    current_state = robot_manager.get_state()

    # DB에 현재 상태 기록 (히스토리)
    new_log = RobotLog(
        robot_id=current_state['robot_id'],
        battery=current_state['battery_percent'],
        cpu=current_state['cpu_usage'],
        latency_ctrl=current_state['latency_total'],
        latency_robot=current_state['latency_robot'],
        status=current_state['status']
    )
    db.session.add(new_log)
    db.session.commit()

    # 프론트엔드(존2, 존4)로 데이터 쏴주기
    return jsonify({
        "status": "success",
        "zone2": {
            "on_count": 14,
            "off_count": 0,
            "battery_percent": current_state['battery_percent'],
            "voltage": current_state['battery_voltage'],
            "cpu_usage": current_state['cpu_usage'],
            "memory_usage": current_state['memory_usage']
        },
        "zone4": {
            "control_latency": current_state['latency_total'],
            "robot_latency": current_state['latency_robot']
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)