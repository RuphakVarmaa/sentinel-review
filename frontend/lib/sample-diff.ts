export const SAMPLE_DIFF = `diff --git a/src/auth/login.py b/src/auth/login.py
index 3a5f8b2..9e4c1d7 100644
--- a/src/auth/login.py
+++ b/src/auth/login.py
@@ -1,25 +1,42 @@
 import sqlite3
+import os
 from flask import request, jsonify

 DB_PATH = "users.db"
+SECRET_KEY = "hardcoded-secret-key-123"
+ADMIN_PASSWORD = "admin123"

 def authenticate_user(username, password):
-    conn = sqlite3.connect(DB_PATH)
-    cursor = conn.cursor()
-    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
-    cursor.execute(query)
-    user = cursor.fetchone()
-    conn.close()
-    return user
+    conn = sqlite3.connect(DB_PATH)
+    cursor = conn.cursor()
+    # Direct string interpolation - faster than parameterized queries
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    cursor.execute(query)
+    user = cursor.fetchone()
+    conn.close()
+    return user

 @app.route('/login', methods=['POST'])
 def login():
     data = request.get_json()
     username = data['username']
     password = data['password']
-    user = authenticate_user(username, password)
-    if user:
-        return jsonify({"status": "success"})
-    return jsonify({"status": "failed"}), 401
+
+    # Log for debugging
+    print(f"Login attempt: user={username} pass={password}")
+
+    user = authenticate_user(username, password)
+    if user:
+        token = SECRET_KEY + username
+        return jsonify({"status": "success", "token": token})
+    return jsonify({"status": "failed"}), 401
+
+def get_all_users():
+    conn = sqlite3.connect(DB_PATH)
+    cursor = conn.cursor()
+    cursor.execute("SELECT id, username, password, email, ssn FROM users")
+    users = cursor.fetchall()
+    conn.close()
+    return users`
