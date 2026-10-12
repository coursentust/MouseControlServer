from flask import Flask, request, jsonify, render_template, Response
from simple_websocket import Server, ConnectionClosed
import json
import sys
import ctypes
import pyautogui
from pandas.io.clipboard import clipboard_get, clipboard_set

pyautogui.PAUSE = 0  # default sleeps 0.1s after every call, which makes the touchpad lag

if sys.platform == "win32":
    from ctypes import wintypes

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

    class INPUT(ctypes.Structure):
        # MOUSEINPUT is the biggest member of the INPUT union, so it alone gives the right size
        _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT)]

    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_ABSOLUTE = 0x8000

def cursor_to(x, y):
    # pyautogui.moveTo uses SetCursorPos, which Windows doesn't count as mouse input, so a hidden cursor
    # (hide pointer while typing, after touch input, no mouse plugged in) stays hidden.
    # SendInput is a real mouse move and makes the cursor show again.
    if sys.platform != "win32":
        pyautogui.moveTo(x, y)
        return
    w, h = pyautogui.size()
    # absolute position is 0..65535 over the primary screen; no Windows pointer acceleration applied
    mi = MOUSEINPUT(dx=(x * 65536 + w - 1) // w, dy=(y * 65536 + h - 1) // h,
                    dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)
    inp = INPUT(type=INPUT_MOUSE, mi=mi)
    if ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) != 1:
        pyautogui.moveTo(x, y)  # SendInput blocked (e.g. an admin window is focused), fall back

app = Flask(__name__)

SCALE = 10
clients = set()  # Store connected clients

# API route to move the mouse
@app.route('/up', methods=['GET'])
def up():
    global SCALE
    try:
        x,y = pyautogui.position()
        y -= 1*int(SCALE)
        if x is not None and y is not None:
            X,Y = pyautogui.size()
            y = min(y,Y)
            cursor_to(x, y)
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/down', methods=['GET'])
def down():
    global SCALE
    try:
        x,y = pyautogui.position()
        y += 1*int(SCALE)
        if x is not None and y is not None:
            X,Y = pyautogui.size()
            y = min(y,Y)
            cursor_to(x, y)
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/left', methods=['GET'])
def left():
    global SCALE
    try:
        x,y = pyautogui.position()
        x -= 1*int(SCALE)
        if x is not None and y is not None:
            X,Y = pyautogui.size()
            x = min(x,X)
            cursor_to(x, y)
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/right', methods=['GET'])
def right():
    global SCALE
    try:
        x,y = pyautogui.position()
        x += 1*int(SCALE)
        if x is not None and y is not None:
            X,Y = pyautogui.size()
            x = min(x,X)
            cursor_to(x, y)
            response = jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"})
            response.headers["Connection"] = "keep-alive"
            response.headers["Keep-Alive"] = "timeout=10, max=100"
            return response, 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/scale', methods=['POST'])
def scale():
    global SCALE
    try:
        data = request.get_json()
        s = data.get('s')
        if s is not None:
            X,Y = pyautogui.size()
            if int(s) > X//4:
                return jsonify({"status": "error", "scale":f"{SCALE}", "window size":f"{pyautogui.size()}"}), 400
            SCALE = s
            return jsonify({"status": "success", "scale":f"{SCALE}"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid scale", "scale":f"{SCALE}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "scale":f"{SCALE}"}), 500


def f(xaxis):
    # return 0.02 * math.atan(xaxis)+1
    return  0.5 * (3.1415 / 4) * (xaxis * (1.0593068 + 0.1449821 * xaxis**2)) / (1 + 1.2723328 * xaxis**2) + 1
maxX, maxY = pyautogui.size()[0] -2, pyautogui.size()[1] -2
remX, remY, remScroll = 0.0, 0.0, 0.0  # sub-pixel leftovers, so slow moves are not rounded away

def apply_move(df_x, df_y):
    global remX, remY
    if -2.5 > df_x or df_x > 2.5 : df_x *= f(abs(df_x))
    if -2.5 > df_y or df_y > 2.5 : df_y *= f(abs(df_y))

    df_x, df_y = df_x + remX, df_y + remY
    ix, iy = int(df_x), int(df_y)
    remX, remY = df_x - ix, df_y - iy
    cur_x, cur_y = pyautogui.position()
    if ix == 0 and iy == 0:
        return cur_x, cur_y

    newX, newY = min(max(cur_x + ix, 1), maxX), min(max(cur_y + iy, 1), maxY)
    cursor_to(newX, newY)
    return newX, newY

def apply_scroll(y):
    global remScroll
    y += remScroll
    iy = int(y)
    remScroll = y - iy
    if iy != 0:
        pyautogui.scroll(iy)
    return iy

@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    try:
        data = request.get_json()
        df_x = data.get('x')
        df_y = data.get('y')
        if df_x is not None and df_y is not None:
            newX, newY = apply_move(float(df_x), float(df_y))
            return jsonify({"status": "success", "message": f"Mouse moved to ({newX}, {newY})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/scroll', methods=['POST'])
def scroll():
    try:
        data = request.get_json()
        y = data.get('y')
        if y is not None:
            iy = apply_scroll(float(y))
            return jsonify({"status": "success", "message": f"scroll ({iy})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid scroll"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def apply_click(button):
    pyautogui.click(button="right" if button == "right" else "left")

@app.route('/click_mouse', methods=['POST','GET'])
def click_mouse():
    try:
        data = request.get_json(silent=True) or {}
        apply_click(data.get('button'))
        return jsonify({"status": "success", "message": "Mouse clicked"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_position', methods=['GET'])
def get_position():
    try:
        x, y = pyautogui.position()
        return jsonify({"status": "success", "position": {"x": x, "y": y}}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/sendkey', methods=['POST'])
def sendkey():
    try:
        data = request.get_json()
        key = data.get('k')
        hotkey = data.get('hk')
        if key is not None:
            pyautogui.press(key)
        elif hotkey is not None:
            pyautogui.hotkey(hotkey)
        else:
            return jsonify({"status": "error", "message": "Invalid key"}), 400
        return jsonify({"status": "success", "message": f"press ({key},{hotkey})"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/sendtext', methods=['POST'])
def sendtext():
    try:
        data = request.get_json()
        text = data.get('text')
        if text is None:
            return jsonify({"status": "error", "message": "Invalid text"}), 400

        clipboard_set(text)
        return jsonify({"status": "success", "message": f"set clipboard ({text})"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
   return render_template("MouseControl_index.html")

@app.before_request
def log_request():
    client_ip = request.remote_addr
    #print(f"New request from: {client_ip}, Client Port: {request.environ['REMOTE_PORT']}")

class WebSocketDone(Response):
    # the websocket already used the connection, tell Werkzeug not to write an HTTP response
    def __call__(self, *args, **kwargs):
        raise ConnectionError()

# touchpad events over the browser's built-in WebSocket, same as /move_mouse, /scroll, /click_mouse
# without HTTP overhead. One message per frame: {"t": "move"|"scroll"|"click", ...}
@app.route('/ws', websocket=True)  # without websocket=True Werkzeug rejects the upgrade request with 400
def ws():
    client_ip = request.remote_addr
    sock = Server.accept(request.environ, ping_interval=25)  # ping so a phone that drops off is noticed
    clients.add(client_ip)
    print(f"Client {client_ip} connected. Total connections: {len(clients)}")
    try:
        while True:
            data = sock.receive()
            try:
                data = json.loads(data)
                t = data.get("t")
                if t == "move":
                    apply_move(float(data["x"]), float(data["y"]))
                elif t == "scroll":
                    apply_scroll(float(data["y"]))
                elif t == "click":
                    apply_click(data.get("button"))
            except Exception as e:
                print(f"ws message {data} failed: {e}")
    except ConnectionClosed:
        pass
    finally:
        clients.discard(client_ip)
        print(f"Client {client_ip} disconnected. Total connections: {len(clients)}")
    return WebSocketDone()

if __name__ == '__main__':
    # Command: python MouseControlServer.py
    # Run the Flask app on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)