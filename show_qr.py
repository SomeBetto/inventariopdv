import qrcode
import socket

def get_local_ip():
    try:
        # Create a temporary socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_qr():
    ip = get_local_ip()
    url = f"http://{ip}:5000"
    
    print("\n" + "="*40)
    print("  ESCANEAME PARA CONECTARTE")
    print("="*40)
    print(f"URL: {url}")
    print("="*40 + "\n")
    
    qr = qrcode.QRCode(version=1, box_size=1, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    # Use print_ascii for console compatibility. 
    # invert=True helps with some dark backgrounds in Windows Terminal/CMD
    qr.print_ascii(invert=True)
    
    print("\n" + "="*40)
    print("Asegúrate de estar en la misma red Wi-Fi.")
    print("="*40 + "\n")

if __name__ == "__main__":
    generate_qr()
