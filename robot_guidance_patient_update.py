from pathlib import Path
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
class RobotGuidance(Node):
    def __init__(self):
        super().__init__('robot_guidance')
        self.publisher_ = self.create_publisher(JointTrajectory, '/crane_plus_arm_controller/joint_trajectory', 10)
        self.rooms = {"採血室": int(input("採血室の待ち人数: ")), "心電図室": int(input("心電図室の待ち人数: ")), "胸部X線室": int(input("胸部X線室の待ち人数: "))}
        print("各検査室の待ち人数：", self.rooms)
        patients = {"1001": ["採血室", "心電図室", "胸部X線室"], "1002": ["採血室", "心電図室"], "1003": ["心電図室", "胸部X線室"]}
        patient_id = input("患者IDを入力してください（1001～1003）: ").strip()
        if patient_id not in patients:
            print("登録されていない患者IDです")
            raise ValueError("患者IDが見つかりません")
        self.patient_tests = patients[patient_id]
        print("患者ID:", patient_id, "検査予定:", self.patient_tests)
        completed_records = __import__("json").loads(Path("/home/ubuntu/pai_ws/src/medical_guidance/patient_records.json").read_text(encoding="utf-8"))
        self.completed_tests = completed_records[patient_id]
        print("受診済みの検査:", self.completed_tests)
        self.remaining_tests = [room for room in self.patient_tests if room not in self.completed_tests]
        self.best_room = min(self.remaining_tests, key=self.rooms.get) if self.remaining_tests else None
        if self.best_room is None:
            print("案内できる未受診の検査がありません")
            raise ValueError("未受診の検査なし")
        print("おすすめの検査室：", self.best_room)
        print("待ち人数：", self.rooms[self.best_room], "人")
        self.angles = {"採血室": -0.52, "心電図室": 0.0, "胸部X線室": 0.52}
        self.target_angle = self.angles[self.best_room]
        self.msg = JointTrajectory()
        self.msg.joint_names = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint3', 'crane_plus_joint4']
        self.point = JointTrajectoryPoint()
        self.point.positions = [self.target_angle, 0.0, 0.0, 0.0]
        self.point.time_from_start = Duration(sec=5)
        self.msg.points = [self.point]

def main():
    rclpy.init()
    try:
        while True:
            node = RobotGuidance()
            try:
                while node.publisher_.get_subscription_count() == 0:
                    rclpy.spin_once(node, timeout_sec=0.1)
                rclpy.spin_once(node, timeout_sec=1.0)
                node.publisher_.publish(node.msg)
                rclpy.spin_once(node, timeout_sec=1.0)
            finally:
                node.destroy_node()
            if input("続ける場合はEnter、終了する場合はq: ").strip().lower() == "q":
                break
    except (KeyboardInterrupt, EOFError, ValueError):
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
