from flask import Flask, request, jsonify, render_template
import pyautogui
from pandas.io.clipboard import clipboard_get, clipboard_set

app = Flask(__name__)

SCALE = 10

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
            pyautogui.moveTo(x, y)
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
            pyautogui.moveTo(x, y)
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
            pyautogui.moveTo(x, y)
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/right', methods=['GET'])
def right():
    global SCALE
    print(SCALE)
    try:
        x,y = pyautogui.position()
        x += 1*int(SCALE)
        print(x)
        if x is not None and y is not None:
            X,Y = pyautogui.size()
            x = min(x,X)
            pyautogui.moveTo(x, y)
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})"}), 200
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


@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    try:
        data = request.get_json()
        x = data.get('x')
        y = data.get('y')
        cur_x, cur_y = pyautogui.position()
        if x is not None and y is not None:
            pyautogui.moveTo( cur_x + x, cur_y + y )
            return jsonify({"status": "success", "message": f"Mouse moved to ({x}, {y})   {pyautogui.position()}"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid coordinates"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/scroll', methods=['POST'])
def scroll():
    try:
        data = request.get_json()
        y = data.get('y')
        if y is not None:
            pyautogui.scroll(int(y))
            return jsonify({"status": "success", "message": f"scroll ({y})"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid scroll"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/click_mouse', methods=['POST','GET'])
def click_mouse():
    try:
        pyautogui.click()
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
        k = data.get('k')
        if k is None:
            return jsonify({"status": "error", "message": "Invalid key"}), 400

        pyautogui.press(k)
        return jsonify({"status": "success", "message": f"press ({k})"}), 200
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


if __name__ == '__main__':
    # Command: python MouseControlServer.py
    # Run the Flask app on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)
