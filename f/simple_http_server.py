import time
import http.server #BaseHTTPServer
import cpustat
import psutil
import os

#HOST_NAME = '0.0.0.0' # !!!REMEMBER TO CHANGE THIS!!!
HOST_NAME = '192.168.1.10' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8000
cpul = cpustat.GetCpuLoad()

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds

def miltoS(mil):
    n = int(mil)
    n/1000
    return str(n)

def cpug():
    pass


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write(bytes("<html><head><title>Server status</title></head>", "utf-8"))
        s.wfile.write(bytes("<h1>"+time.ctime(time.time())+".</h1>", "utf-8"))

        osn = os.uname()
        cpu = ""
        with open('/proc/cpuinfo', 'r') as file:
            for line in file:
                if "model name" in line:
                    cpu = line.split(':')[1].strip()
                    break
        s.wfile.write(bytes("<p><b>&nbsp&nbsp&nbsp"+osn[0]+" " + osn[2] + "</b><br> version " + osn[3] + "<br>" + cpu + "</p>", "utf-8"))	
	

        s.wfile.write(bytes("<p>Uptime: "+miltoS(get_uptime())+"s</p>", "utf-8"))	

        mem = psutil.virtual_memory()
        s.wfile.write(bytes("<p>RAM: "+str(int(mem[0]/1048576))+"MB | " + str(int(mem[3]/1048576)) + "MB used (" + str(round(mem[2],2)) + "%) </p>", "utf-8"))	


        k = []
        v = []
        dic = cpul.getcpuload()
        for key in dic:
            k += [key]
            v += [dic[key]]
        k[0] = "<b>"+k[0]+"</b>"
        s.wfile.write(bytes("<table border = \"1\">", "utf-8"))
        s.wfile.write(bytes("<tr>", "utf-8"))
        for key in k:
            s.wfile.write(bytes("<td align=center>" + key + "</td>", "utf-8"))
        s.wfile.write(bytes("</tr>", "utf-8"))
        s.wfile.write(bytes("<tr>", "utf-8"))
        for value in v:
            s.wfile.write(bytes("<td align=center>" + str(round(value,2)) + "%</td>", "utf-8"))
        s.wfile.write(bytes("</tr></table>", "utf-8"))

        
        s.wfile.write(bytes("<br><br><br>", "utf-8"))


        s.wfile.write(bytes("<table border = \"1\">", "utf-8"))
        s.wfile.write(bytes("<tr><th><b>PID</b></th>", "utf-8"))
        s.wfile.write(bytes("<th><b>NAME</b></th></tr>", "utf-8"))
        for p in psutil.process_iter(attrs=["pid", "name"]):
            s.wfile.write(bytes("<tr>", "utf-8"))
            s.wfile.write(bytes("<td align=right>" + str(p.pid) + "&nbsp</td>", "utf-8"))
            s.wfile.write(bytes("<td>&nbsp" + p.name() + "</td>", "utf-8"))
            s.wfile.write(bytes("</tr>", "utf-8"))
        s.wfile.write(bytes("</table>", "utf-8"))

        s.wfile.write(bytes("</body></html>", "utf-8"))


if __name__ == '__main__':
    server_class = http.server.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        self.server_close()
        print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

