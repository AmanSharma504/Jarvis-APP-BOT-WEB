#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import urllib.parse
import ssl
import math
import site
import ast

# Create resilient SSL context for macOS python without certifi installed
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Ensure OpenJarvis and user site-packages are on sys.path dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../OpenJarvis/src"))

user_site = site.getusersitepackages()
if isinstance(user_site, str) and os.path.exists(user_site) and user_site not in sys.path:
    sys.path.append(user_site)

# Fallback for Python 3.14 user-site if not picked up by default
py314_site = os.path.expanduser("~/Library/Python/3.14/lib/python/site-packages")
if os.path.exists(py314_site) and py314_site not in sys.path:
    sys.path.append(py314_site)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def handle_weather(city="Delhi"):
    clean_city = str(city).strip() or "Delhi"
    try:
        url = f"https://wttr.in/{urllib.parse.quote(clean_city)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Jarvis Assistant)"})
        with urllib.request.urlopen(req, timeout=6.0, context=ssl_context) as res:
            data = json.loads(res.read().decode("utf-8"))
            current = data.get("current_condition", [{}])[0]
            temp = current.get("temp_C", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "")
            humidity = current.get("humidity", "")
            return {
                "city": clean_city,
                "temperature": f"{temp}°C",
                "condition": desc,
                "humidity": f"{humidity}%",
                "source": "OpenJarvis Weather Connector"
            }
    except Exception as e:
        # Fallback to secondary endpoint if wttr format=j1 fails
        try:
            url_alt = f"https://wttr.in/{urllib.parse.quote(clean_city)}?format=%C+%t+%h"
            req_alt = urllib.request.Request(url_alt, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_alt, timeout=4.0, context=ssl_context) as res_alt:
                raw_text = res_alt.read().decode("utf-8").strip()
                return {
                    "city": clean_city,
                    "condition": raw_text,
                    "source": "OpenJarvis Weather Connector (Fallback)"
                }
        except Exception as e2:
            return {"error": f"Weather fetch failed: {str(e2)}"}

def handle_calc(expr):
    clean_expr = str(expr).strip()
    if not clean_expr:
        return {"error": "Empty expression provided"}
    
    if len(clean_expr) > 200:
        return {"error": "Expression exceeds maximum length (200 characters)"}

    # Whitelisted safe math functions
    safe_funcs = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    safe_funcs.update({"abs": abs, "round": round, "max": max, "min": min, "pow": pow})

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ZeroDivisionError("integer division by zero")
                return left // right
            elif isinstance(node.op, ast.Mod):
                if right == 0:
                    raise ZeroDivisionError("modulo by zero")
                return left % right
            elif isinstance(node.op, ast.Pow):
                if abs(right) > 1000 or (isinstance(left, (int, float)) and abs(left) > 1000 and right > 100):
                    raise ValueError("Exponentiation values too large to evaluate safely")
                return left ** right
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only standard named functions are allowed")
            func_name = node.func.id
            if func_name not in safe_funcs:
                raise ValueError(f"Function '{func_name}' is not permitted")
            func = safe_funcs[func_name]
            args = [eval_node(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.Name):
            if node.id in safe_funcs and isinstance(safe_funcs[node.id], (int, float)):
                return safe_funcs[node.id]
            raise ValueError(f"Identifier '{node.id}' is undefined or not a numeric constant")
        else:
            raise ValueError(f"Unsupported syntax structure: {type(node).__name__}")

    try:
        parsed = ast.parse(clean_expr, mode='eval')
        result = eval_node(parsed)
        return {"expression": clean_expr, "result": result, "engine": "OpenJarvis Calculator (Hardened AST)"}
    except Exception as e:
        return {"error": f"Evaluation error: {str(e)}"}

def handle_status():
    try:
        import openjarvis
        version = getattr(openjarvis, "__version__", "0.3.0-dev")
        path = getattr(openjarvis, "__file__", "integrated")
    except Exception:
        version = "0.3.0-dev"
        path = "integrated"

    return {
        "status": "online",
        "openjarvis_version": version,
        "openjarvis_path": path,
        "python_version": sys.version.split()[0],
        "active_connectors": ["weather", "calculator", "system", "openrouter_bridge"]
    }

def parse_args():
    args = sys.argv[1:]
    if not args:
        return "status", ""

    action = ""
    param = ""
    skip_next = False

    for i, a in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if a in ("--action", "-a") and i + 1 < len(args):
            action = args[i + 1]
            skip_next = True
        elif a in ("--param", "-p", "--query", "-q") and i + 1 < len(args):
            param = args[i + 1]
            skip_next = True
        elif a.startswith("--action="):
            action = a.split("=", 1)[1]
        elif a.startswith("--param="):
            param = a.split("=", 1)[1]
        elif not action:
            action = a
        elif not param:
            param = a

    return action.lower().strip(), param.strip()

def main():
    cmd, arg = parse_args()

    if cmd in ("weather", "mausam", "मौसम"):
        print(json.dumps(handle_weather(arg or "Delhi")))
    elif cmd in ("calc", "calculator", "math", "गणित"):
        print(json.dumps(handle_calc(arg)))
    elif cmd in ("status", "info"):
        print(json.dumps(handle_status()))
    else:
        print(json.dumps({"error": f"Unknown action: {cmd}"}))

if __name__ == "__main__":
    main()
