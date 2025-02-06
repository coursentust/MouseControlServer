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


def f(xaxis):
    # return 0.02 * math.atan(xaxis)+1
    return  0.5 * (3.1415 / 4) * (xaxis * (1.0593068 + 0.1449821 * xaxis**2)) / (1 + 1.2723328 * xaxis**2) + 1
maxX, maxY = pyautogui.size()[0] -2, pyautogui.size()[1] -2
@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    try:
        data = request.get_json()
        df_x = data.get('x')
        df_y = data.get('y')
        if df_x is not None and df_y is not None:
            cur_x, cur_y = pyautogui.position()
            if -2.5 > df_x or df_x > 2.5 : df_x *= f(abs(df_x))
            if -2.5 > df_y or df_y > 2.5 : df_y *= f(abs(df_y))

            newX, newY = cur_x + df_x, cur_y + df_y
            newX, newY = min(max(newX, 1), maxX), min(max(newY, 1), maxY)

            pyautogui.moveTo( newX, newY )
            return jsonify({"status": "success", "message": f"Mouse moved to ({newX}, {newY})   {pyautogui.position()}"}), 200
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


if __name__ == '__main__':
    # Command: python MouseControlServer.py
    # Run the Flask app on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)
