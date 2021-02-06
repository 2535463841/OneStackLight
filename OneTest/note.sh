Syoa1234

zRb8&y6!

zbw@0210


安装 BC-EC


root
ec123!@#


bcec
bcec@1234




for service in firewalld NetworkManager
do
    sudo systemctl stop $service
    sudo systemctl disable $service
done


sudo yum install iptables*
sudo vi /etc/sysconfig/iptables

-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 10000 -m comment --comment "haproxy monitor" -j ACCEPT
-A INPUT -p tcp -m multiport --dports 3306,4567,4444 -m comment --comment rdb -j ACCEPT
-A INPUT -p tcp -m tcp --dport 3306 -m comment --comment mysql -j ACCEPT
-A INPUT -p tcp -m tcp --dport 4369 -m comment --comment "rabbitmq cluster" -j ACCEPT
-A INPUT -p tcp -m tcp --dport 5672 -m comment --comment rabbitmq -j ACCEPT
-A INPUT -p tcp -m tcp --dport 15672 -m comment --comment "rabbitmq monitor" -j ACCEPT
-A INPUT -p tcp -m tcp --dport 25672 -m comment --comment "rabbitmq monitor" -j ACCEPT
-A INPUT -p tcp -m tcp --dport 41055 -m comment --comment "rabbitmq autoheal" -j ACCEPT
-A INPUT -s 10.10.91.0/24 -p tcp -m tcp --dport 11211 -j ACCEPT -m comment --comment 




sudo rm -rf /etc/localtime
sudo ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

sudo yum install ntp


echo "
driftfile /var/lib/ntp/drift
restrict default nomodify notrap nopeer noquery
restrict 127.0.0.1
restrict ::1
server 127.127.1.0
fudge 127.127.1.0 stratum 0
includefile /etc/ntp/crypto/pw
keys /etc/ntp/keys
disable monitor
" |sudo tee -a /etc/ntp.conf

sudo hwclock --systohc 
sudo systemctl restart ntpd.service
sudo systemctl enable ntpd


# 安装数据库

yum install rsync socat perl perl-Digest-MD5 perl-DBD-MySQL xinetd -y
yum install bcrdb

cp -a /etc/bcrdb/my.cnf.vm /etc/bcrdb/my.cnf
/usr/lib/bcrdb/bin/bcrdbd bootstrap

curl -I 127.0.0.1:33060 -s |grep '200 OK'













