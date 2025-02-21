from flask import Flask
import os
import datetime
import psutil
import subprocess

app = Flask(__name__)

@app.route('/htop')
def htop():
    # Get system username (fallback to 'codespace' if not found)
    system_username = os.getenv("USER", "codespace")

    # Get current time in IST
    ist_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    formatted_time = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")

    # Get system uptime
    uptime_output = subprocess.check_output("uptime", shell=True).decode("utf-8").strip()

    # Get memory details
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    mem_total = round(mem.total / (1024 * 1024), 1)  # Convert to MB
    mem_used = round(mem.used / (1024 * 1024), 1)
    mem_available = round(mem.available / (1024 * 1024), 1)

    swap_total = round(swap.total / (1024 * 1024), 1)
    swap_used = round(swap.used / (1024 * 1024), 1)
    swap_free = round(swap.free / (1024 * 1024), 1)

    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Get process list
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'nice', 'memory_percent', 'status', 'create_time', 'num_threads', 'username']):
        try:
            pid = proc.info['pid']
            user = proc.info.get('username', "unknown")  # Fix KeyError
            pr = proc.info['nice']
            vsize = proc.info['memory_info'].vms // 1024  # Virtual memory (KB)
            rss = proc.info['memory_info'].rss // 1024  # Resident memory (KB)
            cpu = proc.info['cpu_percent']
            mem_usage = round(proc.info['memory_percent'], 1)

            # Calculate SHR (shared memory in MiB)
            shr = round(proc.info['memory_info'].shared / (1024 * 1024), 1) if hasattr(proc.info['memory_info'], 'shared') else 0

            # Calculate process run time
            start_time = datetime.datetime.fromtimestamp(proc.info['create_time'])
            runtime = datetime.datetime.now() - start_time
            runtime_str = str(runtime).split(".")[0]  # Remove milliseconds

            # Append process info
            process_list.append({
                'PID': pid,
                'USER': user,
                'PR': pr,
                'VIRT': vsize,
                'RES': rss,
                'CPU%': cpu,
                'MEM%': mem_usage,
                'NI': pr,
                'SHR': shr,
                'S': proc.info['status'],
                'Time': runtime_str,
                'Command': proc.info['name']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by CPU usage and limit to 20 processes
    process_list = sorted(process_list, key=lambda x: x['CPU%'], reverse=True)[:20]

    # Format output like htop
    top_output = f"""
    <html>
    <body>
        <h1>HTOP Information</h1>
        <p><strong>Name:</strong> sample_name</p>
        <p><strong>User:</strong> {system_username}</p>
        <p><strong>Server Time (IST):</strong> {formatted_time}</p>
        <h2>TOP output:</h2>
        <pre>
Top: {uptime_output}
Tasks: {len(process_list)} total, {psutil.cpu_count()} CPUs
%Cpu(s): {cpu_usage}% used
MiB Mem : {mem_total} total, {mem_used} used, {mem_available} avail Mem
MiB Swap: {swap_total} total, {swap_used} used, {swap_free} free

PID    USER    PR    VIRT    RES    %CPU  %MEM  NI  SHR  S    Time+COMMAND
{"-"*80}
""" + "\n".join(f"{p['PID']:>6} {p['USER'][:8]:<8} {p['PR']:>3} {p['VIRT']:>8} {p['RES']:>8} {p['CPU%']:>4.1f} {p['MEM%']:>5.1f} {p['NI']:>3} {p['SHR']:>5.1f} {p['S']:<5} {p['Time']:>8} {p['Command'][:20]:<20}" for p in process_list) + """
        </pre>
    </body>
    </html>
    """

    return top_output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)