from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Ví dụ: Hàm mã hóa văn bản ---
@app.route('/encode', methods=['POST'])
def encode():
    # Lấy dữ liệu JSON từ yêu cầu của ứng dụng
    data = request.json
    text_to_encode = data.get('text', '')

    # --- Đây là nơi bạn đặt LOGIC XỬ LÝ PHỨC TẠP bằng Python ---
    # Ví dụ đơn giản: đảo ngược chuỗi
    encoded_text = text_to_encode[::-1]

    # Trả về kết quả dưới dạng JSON
    return jsonify({'encoded_text': encoded_text})

if __name__ == '__main__':
    # Chạy server, cho phép kết nối từ bất kỳ đâu
    app.run(host='0.0.0.0', port=5000)