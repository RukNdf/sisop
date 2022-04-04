# Tutorial distro -Linux Web Server
## TP1 Laborátório de Sistemas Operacionais
Victor Scherer Putrich e Lucca Dornelles Cezar

Tabela de conteúdos
=================
<!--ts-->
   * [Sobre](#Sobre)
   * [Instalação Buildroot](#Instalação-Buildroot)
   * [Instalação de Dependênicas e Pacotes](#Instalação-de-Dependências-e-Pacotes)
   * [Configuração de Rede](#Configuração-de-Rede)
   * [Python Web Service](#Python-Web-Service)
   * [Execução Web Service](#Execução-Web-Service)
<!--te-->


# Sobre
 Tutorial de Distribuição Linux capaz de executar um servidor WEB escrito em Python ou C/C++.
 O servidor (kernel) hospeda uma página acessada pela máquina host contendo as seguintes informações sobre o sistema:
 
* Data e hora do sistema;
* Uptime (tempo de funcionamento sem reinicialização do sistema) em segundos;
* Modelo do processador e velocidade;
* Capacidade ocupada do processador (%);
* Quantidade de memória RAM total e usada (MB);
* Versão do sistema;
* Lista de processos em execução (pid e nome).

# Instalação-Buildroot
Criamos uma pasta no diretório Home com o nome 'linuxDistro', faça o download da versão 2022.02 do Buildroot, decompacte o arquivo e renomeio o diretório criar para buildroot/  

```
mkdir linuxdistro
cd linuxdistro
wget --no-check-certificate https://buildroot.org/downloads/buildroot-2022.02.tar.gz
tar -zxvf buildroot-2022.02.tar.gz
mv buildroot-2022.02/ buildroot/
```
# Instalação-de-Dependências-e-Pacotes

Nesta distribuição, usaremos um WEB Server escrito em Python3 que faz uso da biblioteca *psutil*. Adicione o pacote do interpretador e da biblioteca no buildroot:  

```
make linux-menuconfig
```

* *Target packet -->  Interpreter Languages and Scripting -->  <\*> Python3*
* *Target packet -->  Interpreter Languages and Scripting --> External Python Modules -->  <\*> Python-PSUtil*  

> Voce pode fazer a instalação do psutil usando o pip, mas deve adicioná-lo no buildroot também em External Python Modules.

Além disso também precisaremos do driver de rede Intel Ethernet e1000:  

* *Device Drivers  ---> Network device support  --->  Ethernet driver support  ---> <\*> Intel(R) PRO/1000 Gigabit Ethernet support*


Depois de salvar as alterações recompile a distribuição com os comandos:
```
make clean
make linux-menuconfig
``` 

# Configuração-de-Rede
Nesta etapa iremos estabelecer a conexão entre a nossa máquina host e a distro que estamos montado.  

## Configuração Máquina Host
Para que seja possível montarmos um Web Server, precisamos estabelecer um canal de comunicação entre a máquina host e o servidor. Para tal, primeiramente usaremos o script **qemu-ifup** descrito a seguir que cria uma interface de comunicação por parte do cliente.  


```
#!/bin/sh
set -x

switch=br0

if [ -n "$1" ];then
        ip tuntap add $1 mode tap user `whoami`		#create tap network interface
        ip link set $1 up				#bring interface tap up
        sleep 0.5s					#wait the interface come up.
        sysctl -w net.ipv4.ip_forward=1                 # allow forwarding of IPv4
	route add -host 192.168.1.10 dev $1 		# add route to the client
        exit 0
else
        echo "Error: no interface specified"
        exit 1
fi
```

Dentro do diretório do *(buildroot/)*, criaremos uma pasta chamada *custom-scripts*, para colocar todos os scripts usados neste tutorial e jogaremos o arquivo *qemu-ifup* lá dentro.  

*Não se esqueça de dar permissão ao arquivo criado*  

```
chmod +x custom-scripts/qemu-ifup
```

## Emulando com QEMU
Para fazer a emulação da máquina guest, ligaremos o nosso sistema operacional sempre executando o script *qemu-ifup* com o comando:  

```
sudo qemu-system-i386 --device e1000,netdev=eth0,mac=aa:bb:cc:dd:ee:ff \
	--netdev tap,id=eth0,script=custom-scripts/qemu-ifup \
	--kernel output/images/bzImage \
	--hda output/images/rootfs.ext2 \
	--nographic \
	--append "console=ttyS0 root=/dev/sda"
```

## Configuração Máquina Guest
Agora devemos configurar a rede do nosso sistema, definiremos para a nossa máquina o ip 192.168.1.10, adicionaremos uma rota para o ip da máquina host e também a deixaremos como o nosso Gateway padrão.  

Para evitar que seja necessário fazer essa configuração toda vez que ligarmos nosso sistema, usaremos o script **S41network-config** que faz essas configurações para nós e iremos configurar para que o sistemo o execute toda vez que for inicializado.   

Colocaremos o script na pasta *custom-scripts*.

```
#!/bin/sh
#
# Configuring host communication.
#

case "$1" in
  start)
	printf "Configuring host communication."
	
	/sbin/ifconfig eth0 192.168.1.10 up
	/sbin/route add -host <IP-DO-HOST> dev eth0
	/sbin/route add default gw <IP-DO-HOST>
	[ $? = 0 ] && echo "OK" || echo "FAIL"
	;;
  stop)
	printf "Shutdown host communication. "
	/sbin/route del default
	/sbin/ifdown -a
	[ $? = 0 ] && echo "OK" || echo "FAIL"
	;;
  restart|reload)
	"$0" stop
	"$0" start
	;;
  *)
	echo "Usage: $0 {start|stop|restart}"
	exit 1
esac

exit $?
```

> Substitua os campos < IP-DO-HOST > pelo IP real.  
> Você pode descobrir o IP da sua máquina usando o comando *ifconfig* no terminal.  

No mesmo diretório copie e cole o código do script *pre-build.sh* a seguir:  

```
#!/bin/sh

cp $BASE_DIR/../custom-scripts/S41network-config $BASE_DIR/target/etc/init.d
chmod +x $BASE_DIR/target/etc/init.d/S41network-config
chmod +x custom-scripts/pre-build.sh
```

De permissão de administrador para o arquivo:

```
chmod +x custom-scripts/pre-build.sh
```

Agora iremos configurar a nossa distribuição para executar o script *pre-build.sh* toda vez que for inicializado:  

```
make menuconfig
```

* *System configuration ---> (custom-scripts/pre-build.sh) Custom scripts to run befor creating filesystem images*  

```
make
sudo qemu-system-i386 --device e1000,netdev=eth0,mac=aa:bb:cc:dd:ee:ff \
	--netdev tap,id=eth0,script=custom-scripts/qemu-ifup \
	--kernel output/images/bzImage \
	--hda output/images/rootfs.ext2 --nographic \
	--append "console=ttyS0 root=/dev/sda" 
```

> você pode testar a conexão fazendo um ping para o IP da máquina host.  

# Python-Web-Service
	
O código do web service encontra-se neste mesmo repositório no link:   <https://github.com/RukNdf/sisop/blob/main/f/simple_http_server.py>.

Coloque este código no diretório *buildroot/output/target/usr/bin/*.
	
> **OBS:** Para que o kernel execute o programa, você precisa ter instalado o interpretador de Python3 e o pacote PSUtil.
	
Adicione mais um script chamado *S52Wakeup* que será sempre executado ao ligarmos a nosso sistema operacional, este script roda o programa *simple_http_server.py*:  

```
#!/bin/sh

#echo"TESTE"
#python /usr/bin/simple_http_server.py
case "$1" in
	start)
		python3 /usr/bin/simple_http_server.py
		;;
	stop)
		exit 1
		;;
	*)
		exit 1
		;;
esac

exit 0	
```
	
Para isso, coloque o script acima no diretório */buildroot/output/target//etc/init.d/* e em seguida dê permissão de administrador ao arquivo adicionado:  

```
chmod +x /etc/init.d/S51Wakeup
```

## Funcionamento simple_http_server
O script python utiliza as funções da biblioteca http.server para abrir um socket no guest e receber pedidos HTTP. Ao receber um pedido o código html é gerado e retornado também pelo protocolo HTTP. 

Para que o servidor possa ser acessado pela máquina host é necessário que a variável *HOST_NAME* aponte para o IP do guest (que já vem pre configurado para 192.168.1.10) e a variável *PORT_NUMBER* aponte para uma porta disponível.

Para gerar o código html o programa utiliza funções internas, bibliotecas python, e arquivos do próprio linux.


A data e hora é obtida a partir da biblioteca *time*, que retorna a informação já formatada.
````
import time
s.wfile.write(bytes("<h1>"+time.ctime(time.time())+".</h1>", "utf-8"))
````
Informações do sistema são obtidos a partir do comando *uname* do linux e as informações da cpu são obtidas a partir do arquivo */proc/cpuinfo*.

Como o arquivo *cpuinfo* contém varias outras informações sobre o sistema é necessário iterar pelas linhas procurando apenas o modelo da CPU. 
````
osn = os.uname()
cpu = ""
with open('/proc/cpuinfo', 'r') as file:
    for line in file:
	if "model name" in line:
	    cpu = line.split(':')[1].strip()
	    break
s.wfile.write(bytes("<p><b>&nbsp&nbsp&nbsp"+osn[0]+" " + osn[2] + "</b><br> version " + osn[3] + "<br>" + cpu + "</p>", "utf-8"))	
````
O uptime do computador é obtido a partir do arquivo */proc/uptime*. A função *split()* é necessária para remover qualquer informação extra após o tempo de execução. 
````
with open('/proc/uptime', 'r') as f:
	uptime_seconds = float(f.readline().split()[0])
````
A biblioteca *psutil* disponibiliza várias informações sobre os processos do sistema, incluindo toda a lista de processos e o seu uso de memória. 

A função *virtual_memory()* retorna uma lista de valores, como o tamanho total da memoria em bytes e a porcentagem em uso, que são extraídos e formatados. 

A função *process_iter()* nos permite iterar pela lista de processos do sistema e montar uma tabela html com os IDs e nomes de todos os processos em execução.
````
mem = psutil.virtual_memory()
s.wfile.write(bytes("<p>RAM: "+str(int(mem[0]/1048576))+"MB | " + str(int(mem[3]/1048576)) + "MB used (" + str(round(mem[2],2)) + "%) </p>", "utf-8"))	

s.wfile.write(bytes("<table border = \"1\">", "utf-8"))
s.wfile.write(bytes("<tr><th><b>PID</b></th>", "utf-8"))
s.wfile.write(bytes("<th><b>NAME</b></th></tr>", "utf-8"))
for p in psutil.process_iter(attrs=["pid", "name"]):
    s.wfile.write(bytes("<tr>", "utf-8"))
    s.wfile.write(bytes("<td align=right>" + str(p.pid) + "&nbsp</td>", "utf-8"))
    s.wfile.write(bytes("<td>&nbsp" + p.name() + "</td>", "utf-8"))
    s.wfile.write(bytes("</tr>", "utf-8"))
s.wfile.write(bytes("</table>", "utf-8"))
````
As valores de uso da CPU são obtidos a partir do programa *cpustat*. 

A função *getcpuload()* retorna um dicionário com os nomes das cpus (sendo o primeiro valor o total e os subsequentes os cores individuais) e seu respectivo uso. Os nomes das cpus e os valores de uso são salvos separadamente para que possam gerar uma tabela horizontal, com os nomes acima do respectivo valor. 
````
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
````

# Execução-Web-Service


Depois de seguir todos os passos está na hora de executar o servidor e nos conectarmos a ele com a máquina host.  
Primeira, vamos ligar o nosso servidor:

## Servidor
Para ativarmos o servidor, precisamos inicializar o sistema:

```
make
sudo qemu-system-i386 --device e1000,netdev=eth0,mac=aa:bb:cc:dd:ee:ff \
	--netdev tap,id=eth0,script=custom-scripts/qemu-ifup \
	--kernel output/images/bzImage \
	--hda output/images/rootfs.ext2 --nographic \
	--append "console=ttyS0 root=/dev/sda" 
```
Ao ligar, o terminal deve conter algo como:  
Fri Apr  1 17:27:35 2022 Server Starts - 192.168.1.10:8000

## Cliente

Agora abriremos o nosso navegador e acessaremos o servidor através do ip 192.168.1.10 porta 8000.
> http://192.168.1.10:8000

Deve aparecer uma página semelhante a esta:

<img src="https://github.com/RukNdf/sisop/blob/main/cliente.png" width="516"/>

> Note que sempre que atualizar a páginas alguns campos alteram seu valor dinamicamente.


FIM.




