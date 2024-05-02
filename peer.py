import requests 
import os
import random
import hashlib
import bencodepy
import threading
import socket
import json
# các mảnh ở đây có kích thước là 16 Kb
available_file = {} # 1 từ điển vs khóa là infohash bên trong là đường dẫn đến file đó 

def listen_for_peers(self_socket):
    # dính th này thì chỉ có xác nhận handshake mà thôi
    # chỉ kết nối vs 1 peer duy nhất
    
    while True:
        client_socket, client_address = self_socket.accept()
        ip, port = client_address
        """
        
        address = str(ip) +":"+ str(port)
        others_peer[address] = client_socket
        """
        # print(f"Peer connected: {client_address}")
        handshake = client_socket.recv(68)
        pstr = handshake[1:20]
        if pstr != b"BitTorrent protocol":
            print("Handshake không hợp lệ: Chuỗi giao thức sai")
            client_socket.close()
            continue
        # Kiểm tra info_hash
        received_info_hash = handshake[28:48].hex()
        if received_info_hash not in available_file:
            print("Handshake thất bại: Info hash không tồn tại trong từ điển")
            client_socket.close()
            continue
        else: 
            peerid = handshake[48:]
            print(f"Handshake thành công với peer {client_address} - Peer ID: {peerid}")
            file_name = available_file[received_info_hash]
            # gửi handshake đến bên kia
            
            bt_protocol = b"BitTorrent protocol"                                # 19 bytes
            protocol_length = len(bt_protocol).to_bytes(1, "big")               # 1 byte
            reserved = b"\x00" * 8                                              # 8 bytes
            sha1 = bytes.fromhex(received_info_hash)                            # 20 bytes - 40 for hexa
            peerid = peer_id.encode("utf-8")                                    # 20 bytes
            if len(peerid) < 20:
                peerid += b"\x00" * (20 - len(peerid))
            payload = protocol_length + bt_protocol + reserved + sha1 + peerid

            if client_socket:
                client_socket.send(payload)
                print("gửi handshake thành công")
            else:
                print(f"Không tìm thấy client {ip}")
                client_socket.close()
                return
                # do here

            # lúc này mình gửi bitfield
            print("filename dòng 64: ", file_name)
            data = read_torrent_file(file_name + ".torrent")[0] # -> lỗi ????
            pieces = data["info"]["pieces"]
            if len(pieces) % 20 == 0:
                info_hash_num = len(pieces) / 20
            else:
                info_hash_num = (len(pieces) // 20) + 1

            bitfield = b"\x01" * int(info_hash_num)
            client_socket.send(bitfield)

            # lúc này mình chờ tin nhắn interested của bên yêu cầu
            data = client_socket.recv(1024)
            if data.decode() == "Interested":
                print("Client is interested")
                client_socket.send(("Unchoke").encode())
                print("Send unchoke message successful")
            else: 
                print("Not Interested Message")
                client_address.close()
                break

            pieces = create_pieces_local(file_name)

            while True:
                # lúc này mình chờ tin nhắn yêu cầu mã piece của file
                # client_socket là kênh giao tiếp
                data = client_socket.recv(1024)
                if not data:
                    continue

                if(data.decode() == "Stop"):
                    client_socket.close()
                    break
                print("message: ", data.decode())
                request = json.loads(data.decode())
                index = request.get("index", -1)
                if 0 <= index < len(pieces):
                    piece_data = pieces[index]
                    client_socket.send(piece_data)
                else:
                    client_socket.send(("ERROR").encode())
def create_handshake(info_hash, peer_id, ip_address):
    print("tín hiệu vào hàm create_handshake")
    peer_ip, peer_port = ip_address.split(":")
    
    print("peer_ip: ", peer_ip)
    print("peer_port: ", peer_port)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_port_new = int(peer_port) + 1
    peer_port_new = str(peer_port_new)
    sock = socket.create_connection((peer_ip, peer_port_new))

    bt_protocol = b"BitTorrent protocol"                    # 19 bytes
    protocol_length = len(bt_protocol).to_bytes(1, "big")   # 1 byte
    reserved = b"\x00" * 8                                  # 8 bytes
    sha1 = bytes.fromhex(info_hash)                         # 20 bytes - 40 for hexa
    peerid = peer_id.encode("utf-8")                        # 20 bytes
    if len(peerid) < 20:
        peerid += b"\x00" * (20 - len(peerid))
    payload = protocol_length + bt_protocol + reserved + sha1 + peerid

    sock.send(payload)
    # nhận handshake 
    received = sock.recv(68)
    pstr = received[1:20]
    if pstr != b"BitTorrent protocol":
        print("Handshake không hợp lệ: Chuỗi giao thức sai")
        sock.close()
        return
    elif pstr == b"BitTorrent protocol":
        print("Giao thức đúng")
    received_info_hash = received[28:48].hex()
    if received_info_hash != info_hash:
        print("Khác info_hash dòng 118")
        sock.close()
        return
    elif received_info_hash == info_hash:
        print("trùng infohash dòng 121")

    # Nhận bitfield -> error in this ko nhận đc về true true mà là mảng rỗng lỗi ở dòng 64
    data = sock.recv(1024)
    bitfield_array = [byte == 1 for byte in data]
    print("Received data:", data)
    print("Bitfield array:", bitfield_array)

    
    # create handshake chỉ thêm 1 địa chỉ đã xác nhận kết nối vào thôi
    sock.send(("Interested").encode())
    data = sock.recv(1024)
    if(data.decode() == "Unchoke"):
        # từ đây mới bắt đầu yêu cầu piece đc
        return sock
    else: 
        print("No Unchoke message from provider")
        return sock
def create_pieces_local(file_path):
    piece_size = 16384
    pieces = []
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(piece_size)
            if not piece:
                break
            pieces.append(piece)
    return pieces
def assemble_file(piece_list, output_file_path):
    output_dir = os.path.dirname(output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(output_file_path, 'wb') as f:  # Mở tệp tin đầu ra ở chế độ nhị phân
        for piece in piece_list:
            f.write(piece)
def decode_bencode(bencoded_value):
    if chr(bencoded_value[0]).isdigit():
        first_colon_index = bencoded_value.find(b":")
        if first_colon_index == -1:
            raise ValueError("Invalid encoded value")
        string_len = int(bencoded_value[:first_colon_index])
        matched_value = bencoded_value[
            first_colon_index
            + 1 : string_len
            + 1
            + +len(bencoded_value[:first_colon_index])
        ]
        return (
            matched_value,
            bencoded_value[string_len + 1 + len(bencoded_value[:first_colon_index]) :],
        )
    if chr(bencoded_value[0]).startswith("i"):
        e_index = bencoded_value.find(b"e")
        number_value = bencoded_value[1:e_index]
        return int(number_value), bencoded_value[len(number_value) + 2 :]
    if chr(bencoded_value[0]) == "l":
        list_string = bencoded_value[1:]
        deciphered_list, leftover_string = decode_bencode_list_rec([], list_string)
        return deciphered_list, leftover_string
        # strip last letter for list, should be the e
    if chr(bencoded_value[0] == "d"):
        dictionary_string = bencoded_value[1:-1]
        output_dict = {}
        current_key = None
        while dictionary_string:
            matched_value, dictionary_string = decode_bencode(dictionary_string)
            if isinstance(matched_value, bytes):
                try:
                    matched_value = matched_value.decode()
                except UnicodeDecodeError:
                    matched_value = matched_value
            if current_key:
                output_dict[current_key] = matched_value
                current_key = None
            else:
                current_key = matched_value
        dictionary_string = dictionary_string[1:]
        return output_dict, dictionary_string
    else:
        raise NotImplementedError("Only strings are supported at the moment")
def decode_bencode_list_rec(bencoded_list, bencoded_string):
    if len(bencoded_string) <= 1:
        return bencoded_list, bencoded_string
    corrected_string = bencoded_string
    if bencoded_string.startswith(b"e"):
        return bencoded_list, bencoded_string[1:]
    output, leftover = decode_bencode(corrected_string)
    bencoded_list.append(output)
    return decode_bencode_list_rec(bencoded_list, leftover)
def _calculate_peer_id():
    """
    Calculate and return a unique Peer ID.

    The `peer id` is a 20 byte long identifier. This implementation use the
    Azureus style `-PC1000-<random-characters>`.

    Read more:
        https://wiki.theory.org/BitTorrentSpecification#peer_id
    """
    return '-PC0001-' + ''.join(
        [str(random.randint(0, 9)) for _ in range(12)])
def create_pieces(data, piece_length):
    pieces = []
    # Tạo các mẩu với độ dài cố định
    for i in range(0, len(data), piece_length):
        piece = data[i:i + piece_length]
        pieces.append(hashlib.sha1(piece).digest())
    return b''.join(pieces)
def create_torrent(file_path, tracker_url, piece_length=16384):
    # Đọc dữ liệu từ file
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # Tạo thông tin "info" cho file torrent
    file_name = os.path.basename(file_path)
    file_length = len(file_data)

    info = {
        "name": file_name,
        "piece length": piece_length,
        "pieces": create_pieces(file_data, piece_length),
        "length": file_length,
    }

    # Thông tin chính cho torrent
    torrent_data = {
        "announce": tracker_url,
        "info": info,
    }

    # Tạo file torrent và lưu vào đĩa
    torrent_file_path = f"{file_name}.torrent"
    with open(torrent_file_path, 'wb') as torrent_file:
        torrent_file.write(bencodepy.encode(torrent_data))

    print(f"Torrent file created: {torrent_file_path}")
def read_torrent_file(filename):
    with open(filename, "rb") as f:
        data = f.read()
    f.close()
    return decode_bencode(data)
def print_file_info(file_data):
    print("Tracker URL: " + file_data["announce"])
    print("Length: " + str(file_data["info"]["length"]))
    print(
        "Info Hash: "
        + str(hashlib.sha1(bencodepy.encode(file_data["info"])).hexdigest())
    )
    pieces = file_data["info"]["pieces"]
    piece_length = file_data["info"]["piece length"]
    name = file_data["info"]["name"]

    print("File name: " + str(name))
    print("Piece Length: " + str(piece_length))

    if len(pieces) % 20 == 0:
        info_hash_num = len(pieces) / 20
    else:
        info_hash_num = (len(pieces) // 20) + 1
    print("Pieces Hashes:")
    for i in range(int(info_hash_num)):
        extracted_byte = pieces[i * 20 : (i + 1) * 20]
        print(str(extracted_byte.hex()))
def seed(file_path):
    create_torrent(file_path,tracker_url + "/announce")
    data = read_torrent_file(file_path + ".torrent")[0]
    # Kiểm tra file
    print_file_info(data)
    # Thêm file vào từ điển available_file[info_hash] = file_path
    available_file[str(hashlib.sha1(bencodepy.encode(data["info"])).hexdigest())] = file_path
    pieces = data["info"]["pieces"]
    if len(pieces) % 20 == 0:
        info_hash_num = len(pieces) / 20
    else:
        info_hash_num = (len(pieces) // 20) + 1
    # Tạo các tham số yêu cầu HTTP GET
    params = {
        "info_hash": str(hashlib.sha1(bencodepy.encode(data["info"])).hexdigest()),
        "peer_id": peer_id,
        "port": port,
        "uploaded": 0,
        "downloaded": 0,
        "left": 0,  # Số lượng dữ liệu còn lại để tải (ví dụ)
        "compact": 1,
        "no_peer_id": 1,
        "event": "started",  # Sự kiện khi peer bắt đầu kết nối
        "name": str(data["info"]["name"]),
        "info_hash_num": info_hash_num
        }
    response = requests.get(tracker_url + "/announce", params=params)
    # Kiểm tra trạng thái phản hồi
    if response.status_code == 200:
        tracker_response = response.json()
        print(tracker_response)
    else:
        print(f"Lỗi: {response.status_code}")
def list_file():
    try:
        # Gửi yêu cầu GET tới endpoint /list_file
        response = requests.get(tracker_url + "/list_file")

        # Kiểm tra nếu yêu cầu thành công (HTTP status code 200)
        if response.status_code == 200:
            # Chuyển đổi dữ liệu từ định dạng JSON sang Python
            data = response.json()

            # Lấy danh sách các tệp từ khóa 'files' trong dữ liệu
            file_list = data.get("files", [])

            # In danh sách tệp (hoặc thực hiện xử lý khác theo nhu cầu)
            for file_info in file_list:
                print(f"Tên tệp: {file_info['name']}, Info Hash: {file_info['info_hash']}")

            # Trả về danh sách tệp cho các mục đích khác
            return file_list
        else:
            print(f"Lỗi khi gửi yêu cầu. HTTP Status Code: {response.status_code}")
            return []

    except requests.RequestException as e:
        # Xử lý trường hợp có lỗi trong quá trình gửi yêu cầu
        print(f"Lỗi khi gửi yêu cầu: {e}")
        return []
def peer_list(name):
    params={"name": name}
    response = requests.get(tracker_url + "/list_peer",params = params)
    if response.status_code == 200:
        # Chuyển phản hồi thành định dạng JSON
        try:
            data = response.json()
        except ValueError:
            print("Phản hồi không ở định dạng JSON")
            return []

         # Kiểm tra nếu phản hồi chứa "peers"
        if "peers" in data:
            # Lấy danh sách các chuỗi `ip:port`
            peer_list = [f"{peer['ip']}:{peer['port']}" for peer in data["peers"]]

            print(f"Peers for file '{name}':")
            for peer in peer_list:
                print(f"- {peer}")

            return peer_list  # Trả về danh sách các chuỗi `ip:port`
        else:
            print("Phản hồi không chứa trường 'peers'")
            return []
    else:
        print(f"Lỗi khi gửi yêu cầu. HTTP Status Code: {response.status_code}")
def get_infohash(filename):
    params={
        "name": filename
    }
    response = requests.get(tracker_url + "/get_infohash",params = params)
    if response.status_code == 200:
        data = response.json()
        if "info_hash" in data:
            print(data["info_hash"])
            return data["info_hash"]
    else: 
        print(f"Lỗi khi gửi yêu cầu. HTTP Status Code: {response.status_code}")
        return "00" # Tự quy ước đây là output lỗi
def get_number_of_piece(filename):
    params = {"name": filename}
    response = requests.get(tracker_url + "/get_infohash_num",params = params)
    if response.status_code == 200:
        data = response.json()
        if "number_of_piece" in data:
            print("Số lượng piece trong hàm: ", data["number_of_piece"])
            number_of_piece_int = int(float(data["number_of_piece"]))
            return number_of_piece_int
    else: 
        print(f"Lỗi khi gửi yêu cầu. HTTP Status Code: {response.status_code}")
        return 0 # Tự quy ước đây là output lỗi
def request_piece(sock, index):
    try:
        # Gửi yêu cầu
        request = {"index": index}
        sock.sendall(json.dumps(request).encode())
        
        # Nhận phản hồi từ máy chủ
        data = sock.recv(262144)  # Nhận dữ liệu phản hồi
        # Kiểm tra dữ liệu nhận được
        print("số byte nhận đc : ", len(data))
        return data
    except ConnectionError as e:
        print(f"Connection error: {e}")
        return None
def clear_terminal():
    if os.name == 'nt':  # Windows
        os.system('cls')  # Lệnh xóa terminal trên Windows
    else:  # Linux, macOS, và các hệ điều hành khác
        os.system('clear')  # Lệnh xóa terminal trên Linux/macOS
def available_command():
    print("Available Commands: ")
    print("+ seed <file or file_path>               # seed file to tracker")
    print("+ download <file_name>                   # download <file_name> to downloads directory")
    print("+ end                                    # disconnect from tracker")
    print("+ list                                   # list available files")
    print("+ number_of_piece <file_name>            # get number of piece in <file_name>")
    print("+ peerlist <file_name>                   # get list of seeder for <file_name>")
    print("+ clear                                  # xóa nội dung trên terminal")

def main():
    available_command()
    while True:
        
        # lắng nghe kết nối từ peer khác nếu có
        listener_thread = threading.Thread(target=listen_for_peers, args=(peer_socket,))
        listener_thread.start()
        
        COMMAND = input("")
        argument = COMMAND.split()
        if(len(argument) <= 0):
            print("Invalid command")
            return
        command = argument[0]
        if(command == "seed"):
            if(len(argument) != 2):
                print("Invalid seed command")
            else:
                file_path = argument[1]
                thread = threading.Thread(target=seed, args=(file_path,))
                thread.start()
        elif(command == "end"):
            if(len(argument) != 1):
                print("Invalid list commmand")
            else:
                params = {"peer_id": peer_id}
                if(len(argument) != 1):
                    print("Invalid seed command")
                    response = requests.get(tracker_url + "/stop",params=params)
                    if response.status_code == 200: 
                        json_response = response.json()
                        status = json_response.get("status")
                        message = json_response.get("message")

                        print("Status:", status)
                        print("Message:", message)
                    return
                response = requests.get(tracker_url + "/stop",params=params)
                if response.status_code == 200: 
                    json_response = response.json()
                status = json_response.get("status")
                message = json_response.get("message")

                print("Status:", status)
                print("Message:", message)
                return
        elif(command == "list"):
            if(len(argument) != 1):
                print("Invalid list commmand")
            else:
                thread = threading.Thread(target=list_file)
                thread.start()
        elif(command == "download"):
            if(len(argument) != 2):
                print("Invalid list commmand")
            else:
                name = argument[1]
                # lấy infohash và peerlist của file đó để thực hiện bắt tay
                info_hash = get_infohash(name) # vẫn ở dạng hex
                peerlist = peer_list(name)
                number_of_pieces = int(get_number_of_piece(name))
                connection = []
                for ele in peerlist:
                    conn = create_handshake(info_hash,peer_id,ele)
                    connection.append(conn)
                
                print("số lượng peer có thể seed file {name}", len(connection))
                print("số lượng pieces của file {name}: ", number_of_pieces)
                print()
                write = [None] * number_of_pieces
                if number_of_pieces <= len(connection) :
                    for i in range (number_of_pieces):
                        
                        write[i] = request_piece(connection[i],i)

                elif number_of_pieces > len(connection):
                    divide = int(number_of_pieces/len(connection))
                    start_index = 0
                    for i in range(len(connection)):
                        # Tính toán điểm cuối cho seeder này
                        if i == len(connection) - 1:  # Nếu là seeder cuối cùng, nhận các mảnh còn lại
                            end_index = number_of_pieces
                        else:
                            end_index = start_index + divide

                        for j in range(start_index, end_index):
                            
                            write[j] = request_piece(connection[i],j)

                        # Cập nhật điểm bắt đầu cho seeder tiếp theo
                        start_index = end_index

                print("\nget ready .....\n")
                peer_data = []
                for i in range(len(write)):
                    peer_data.append(write[i])

                assemble_file(peer_data,"downloads/" + name)
                for i in range(len(connection)):
                    connection[i].send(("Stop").encode())

                # Download thành công tự động seed lên server
                seed("downloads/" + name)

        elif(command == "number_of_piece"):
            if(len(argument) != 2):
                print("Invalid list commmand")
            else:
                result = get_number_of_piece(argument[1])
                print("số lượng pieces: ", result)
        elif(command == "peerlist"):
            if(len(argument) != 2):
                print("Invalid list commmand")
            else:
                name = argument[1]
                peerlist = peer_list(name)
                print(peerlist)       
        elif(command == "clear"):
            if(len(argument) != 1):
                print("Invalid clear command")
            else:
                clear_terminal()
        else:
            print("Invalid command")
            available_command()
        

if __name__ == "__main__":

    tracker_url = "http://localhost:8080"
    port = 6881 # cổng giao tiếp vs tracker
    port1 = 6882 # cổng giao tiếp vs các peer khác
    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    peer_socket.bind((host,port1))
    peer_socket.listen(10)
    peer_id = _calculate_peer_id()
    
    main()
