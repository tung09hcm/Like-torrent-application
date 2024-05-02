from flask import Flask, request, jsonify # require pip install Flask
from collections import defaultdict

app = Flask(__name__)

# Dictionary để lưu trữ thông tin về các peers
# Sử dụng defaultdict để tự động tạo một danh sách mới nếu chưa có
torrent_peers = defaultdict(list)
torrent_names = {}
number_of_piece = {}  # lưu số lượng piece của mỗi file đc chia sẻ




@app.route("/announce", methods=["GET"])
def announce():
    # Lấy các thông tin từ yêu cầu HTTP
    info_hash = request.args.get("info_hash")
    peer_id = request.args.get("peer_id")
    ip = request.remote_addr  # Địa chỉ IP của peer
    port = int(request.args.get("port"))
    event = request.args.get("event", "started")
    name = request.args.get("name")
    info_hash_num = request.args.get("info_hash_num")

    if not info_hash or not peer_id or not port:
        return jsonify({"error": "Missing required parameters"}), 400

    # Thông tin của peer
    new_peer = {
        "peer_id": peer_id,
        "ip": ip,
        "port": port,
    }

    # Cập nhật danh sách các peers
    torrent_peers[info_hash].append(new_peer)
    if name and info_hash:
        torrent_names[name] = info_hash
        number_of_piece[name] = info_hash_num 

    # Tạo danh sách các peers cho phản hồi
    # peer_list = [{"ip": p["ip"], "port": p["port"], "peer_id": p["peer_id"]} for p in torrent_peers[info_hash]]

    # Trả lại phản hồi theo định dạng Bittorrent
    # return jsonify({"interval": 1800, "peers": peer_list})
    return jsonify({"Tracker message": "Connection successful"}) 
@app.route("/stop", methods=["GET"])
def stop():
    peer_id = request.args.get("peer_id")
    for info_hash, peers in torrent_peers.items():
        # Loại bỏ các peer có peer_id tương ứng
        torrent_peers[info_hash] = [p for p in peers if p["peer_id"] != peer_id]
    return jsonify({"status": "success", "message": f"Peer with ID {peer_id} has been removed."})
@app.route("/list_file", methods=["GET"])
def list_file():
    file_list = [{"name": k, "info_hash": v} for k, v in torrent_names.items()]
    return jsonify({"files": file_list})
@app.route("/list_peer", methods=["GET"])
def list_peer():    
    file_name = request.args.get("name")
    # Kiểm tra nếu `file_name` được cung cấp
    if not file_name:
        return jsonify({"error": "Missing file_name parameter"}), 400
    # Tìm `info_hash` dựa trên `file_name`
    info_hash = torrent_names.get(file_name)
    # Nếu không tìm thấy `info_hash`, trả về lỗi
    if not info_hash:
        return jsonify({"error": "File not found"}), 404
    # Lấy danh sách các peer từ `torrent_peers`
    peers = torrent_peers.get(info_hash, [])

    # Tạo danh sách phản hồi bao gồm các thông tin về các peer
    peer_list = [{"peer_id": p["peer_id"], "ip": p["ip"], "port": p["port"]} for p in peers]

    # Trả về danh sách các peer
    return jsonify({"file_name": file_name, "peers": peer_list})
@app.route("/get_infohash",methods=["GET"])
def get_infohash():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    if name not in torrent_names:
        return jsonify({"error": "File not found"}), 404
    infohash = torrent_names[name]
    return jsonify({"info_hash": infohash})
@app.route("/get_infohash_num", methods=["GET"])
def get_infohash_num():
    info_hash_num = request.args.get("name")
    if not info_hash_num:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    if info_hash_num not in number_of_piece:
        return jsonify({"error": "File not found"}), 404
    number = number_of_piece[info_hash_num]
    return jsonify({"number_of_piece": number})

if __name__ == "__main__":
    # Khởi động server Flask
    app.run(debug=True, host="0.0.0.0", port=8080)
