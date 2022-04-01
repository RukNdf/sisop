# Tutorial distro -Linux Web Server
## TP1 Laborátório de Sistemas Operacionais
Tabela de conteúdos
=================
<!--ts-->
   * [Sobre](#Sobre)
   * [Instalação Buildroot](#Instalação-Buildroot)
   * [Configuração de Rede](#Configuração-de-Rede)
<!--te-->


# Sobre
 Tutorial de Distribuição Linux que possua um servidor WEB escrito em Python ou C/C++.
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

# Configuração-de-Rede
## Configuração Máquina Host
Para que seja possível montarmos um Web Server fazendo que o servidor seja a distribuição do Linux gerada anteriormente, precisamos estabelecer um canal de comunicação entre a máquina host e o servidor. Para tal, primeiramente usaremos o script **qemu-ifup** descrito a seguir que cria uma interface de comunicação por parte do cliente.


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

dentro do diretório do buildroot/, criaremos uma pasta chamada *custom-scripts*, para colocar todos os scripts usados neste tutorial e jogaremos o arquivo *qemu-ifup* lá dentro.

*Não se esqueça de dar permissão ao arquivo criado*

```
chmod +x custom-scripts/qemu-ifup
```

## Emulando com QEMU
Para executar a emulação da máquina guest execute no a distruibuição do linux criada no diretório buildroot/ o comando:

```
sudo qemu-system-i386 --device e1000,netdev=eth0,mac=aa:bb:cc:dd:ee:ff \
	--netdev tap,id=eth0,script=custom-scripts/qemu-ifup \
	--kernel output/images/bzImage \
	--hda output/images/rootfs.ext2 \
	--nographic \
	--append "console=ttyS0 root=/dev/sda"
```

## Configuração Máquina Guest
Para que exista comunicação entre o Servidor e o Guest, devemos adicionar a rota de guest dentro servidor. Faremos isso de forma automatizada,
fazendo com que o Kernel execute o scrip **S41network-config** toda vez que for inicializado. Colocaremos o script na pasta *custom-scripts*.

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

> Substitua os campos <IP-DO-HOST> pelo IP real.
> Você pode descobrir o IP da sua máquina usando o comando *ifconfig* no terminal.

No mesmo diretório crie copie código do script *pre-build.sh* a seguir:

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

* System configuration
** (custom-scripts/pre-build.sh) Custom scripts to run befor creating filesystem images

'''
make
sudo qemu-system-i386 --device e1000,netdev=eth0,mac=aa:bb:cc:dd:ee:ff \
	--netdev tap,id=eth0,script=custom-scripts/qemu-ifup \
	--kernel output/images/bzImage \
	--hda output/images/rootfs.ext2 --nographic \
	--append "console=ttyS0 root=/dev/sda" 
'''

