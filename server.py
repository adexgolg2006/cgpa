import http.server
import socketserver
import sqlite3
import os  # Required for Render Deployment
from urllib.parse import parse_qs

# ==========================================
# 1. DATABASE LAYER
# ==========================================
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         first_name TEXT, middle_name TEXT, last_name TEXT, 
         department TEXT, programme TEXT, 
         username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

# ==========================================
# 2. TEMPLATE ENGINE
# ==========================================
def get_page(filename, replacements=None):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            if replacements:
                for key, value in replacements.items():
                    content = content.replace(f'{{{{ {key} }}}}', str(value))
            return content
    except FileNotFoundError:
        return f"<h1>Error: {filename} not found.</h1>"

# ==========================================
# 3. REQUEST HANDLER
# ==========================================
class AdexgoldHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if self.path == '/' or self.path == '/login':
            self.wfile.write(get_page('login.html').encode())
        elif self.path == '/signup':
            self.wfile.write(get_page('signup.html').encode())
        else:
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(content_length).decode('utf-8'))
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # --- REGISTRATION LOGIC ---
        if self.path == '/signup':
            try:
                conn = sqlite3.connect('database.db')
                conn.execute("INSERT INTO users (first_name, middle_name, last_name, department, programme, username, password) VALUES (?,?,?,?,?,?,?)",
                    (post_data.get('first_name',[''])[0], post_data.get('middle_name',[''])[0], 
                     post_data.get('last_name',[''])[0], post_data.get('department',[''])[0], 
                     post_data.get('programme',[''])[0], post_data.get('username',[''])[0], 
                     post_data.get('password',[''])[0]))
                conn.commit()
                conn.close()
                self.wfile.write(b"<script>alert('Account Verified!'); window.location='/login';</script>")
            except:
                self.wfile.write(b"Error: Username taken.")

        # --- LOGIN LOGIC ---
        elif self.path == '/login':
            u_in = post_data.get('username', [''])[0]
            p_in = post_data.get('password', [''])[0]
            
            conn = sqlite3.connect('database.db')
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, p_in)).fetchone()
            conn.close()
            
            if user:
                data = {
                    'first_name': user[1], 
                    'last_name': user[3], 
                    'programme': user[5],
                    'department': user[4],
                    'cgpa_res': ''
                }
                self.wfile.write(get_page('calculator.html', data).encode())
            else:
                self.wfile.write(b"Invalid Login.")

        # --- CGPA CALCULATION LOGIC ---
        elif self.path == '/calculator':
            scores = post_data.get('score', [])
            units = post_data.get('unit', [])
            
            total_points = 0
            total_units = 0
            
            for s, u in zip(scores, units):
                if s and u:
                    val_score = float(s)
                    val_unit = float(u)
                    
                    if val_score >= 70: point = 5
                    elif val_score >= 60: point = 4
                    elif val_score >= 50: point = 3
                    elif val_score >= 45: point = 2
                    elif val_score >= 40: point = 1
                    else: point = 0
                    
                    total_points += (point * val_unit)
                    total_units += val_unit
            
            cgpa = round(total_points / total_units, 2) if total_units > 0 else 0.00
            
            res_html = f'''
            <div class="result-display">
                <p>CONSOLIDATED PERFORMANCE INDEX</p>
                <h3 class="result-value">{cgpa:.2f}</h3>
                <div class="academic-standing">TOTAL UNITS: {int(total_units)} | TOTAL POINTS: {int(total_points)}</div>
            </div>
            '''
            
            data = {
                'first_name': 'AUTHENTICATED', 
                'last_name': 'STUDENT', 
                'programme': 'OFFICIAL TRANSCRIPT',
                'department': 'ACADEMIC RECORD',
                'cgpa_res': res_html
            }
            self.wfile.write(get_page('calculator.html', data).encode())

# ==========================================
# 4. EXECUTION & DEPLOYMENT (RENDER FIX)
# ==========================================
if __name__ == '__main__':
    init_db()
    # PORT LOGIC: Tells the app to use Render's dynamic port
    port = int(os.environ.get("PORT", 8000)) 
    with socketserver.TCPServer(("", port), AdexgoldHandler) as httpd:
        print(f"Adexgold Server online at port {port}")
        httpd.serve_forever()
