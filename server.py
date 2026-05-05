import http.server
import socketserver
import sqlite3
from urllib.parse import parse_qs

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, middle_name TEXT, last_name TEXT, 
         department TEXT, programme TEXT, username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

# --- HTML FILE READER ---
def get_page(filename, replacements=None):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            if replacements:
                for key, value in replacements.items():
                    content = content.replace(f'{{{{ {key} }}}}', str(value))
            return content
    except FileNotFoundError:
        return f"<h1>Error: {filename} not found. Please ensure it is in the same folder.</h1>"

# --- SERVER LOGIC ---
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

        # 1. HANDLE SIGNUP
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
                self.wfile.write(b"<script>alert('Account Verified Successfully!'); window.location='/login';</script>")
            except Exception as e:
                self.wfile.write(f"Error: Username already exists. Details: {e}".encode())

        # 2. HANDLE LOGIN
        elif self.path == '/login':
            u_in = post_data.get('username', [''])[0]
            p_in = post_data.get('password', [''])[0]
            
            conn = sqlite3.connect('database.db')
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, p_in)).fetchone()
            conn.close()
            
            if user:
                # user[1]=First Name, user[2]=Middle Name user[3]=Last Name, user[5]=Programme
                data = {
                    'first_name': user[1], 
                    'middle_name': user[2],
                    'last_name': user[3], 
                    'programme': user[5],
                    'cgpa_res': ''
                }
                self.wfile.write(get_page('calculator.html', data).encode())
            else:
                self.wfile.write(b"<script>alert('Invalid Credentials'); window.location='/login';</script>")

        # 3. HANDLE CALCULATION
        elif self.path == '/calculator':
            grades = post_data.get('grade', [])
            units = post_data.get('unit', [])
            
            total_pts = 0
            total_uts = 0
            for g, u in zip(grades, units):
                if g and u:
                    total_pts += float(g) * float(u)
                    total_uts += float(u)
            
            cgpa = round(total_pts / total_uts, 2) if total_uts > 0 else 0.00
            
            # This is the "Mature Result" HTML we discussed
            res_box = f'''
            <div class="result-display">
                <p>CONSOLIDATED PERFORMANCE INDEX</p>
                <h3 class="result-value">{cgpa}</h3>
                <div class="academic-standing">VERIFIED ACADEMIC RECORD</div>
            </div>
            '''
            # Sending result back to the design
            data = {
                'first_name': 'STUDENT', 
                'last_name': 'PROFILE', 
                'programme': 'CONSOLIDATED REPORT',
                'cgpa_res': res_box
            }
            self.wfile.write(get_page('calculator.html', data).encode())

# --- RUN SERVER ---
if __name__ == '__main__':
    init_db()
    PORT = 8000
    import os
    port = int(os.environ.get("PORT", 8000)) # Uses Render's port or 8000 locally
    with socketserver.TCPServer(("", port), AdexgoldHandler) as httpd:
        print(f"Server active at port {port}")
        httpd.serve_forever()

