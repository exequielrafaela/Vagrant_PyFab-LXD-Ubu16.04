from fabric.api import run, sudo, settings, hide, put, cd
from fabric.contrib.files import exists
from termcolor import colored


def lxd():
    with settings(warn_only=True):
        print colored('##################################', 'blue')
        print colored('########### LXD INSTALL ##########', 'blue')
        print colored('##################################', 'blue')

        # Install LXC/LXD if not already installed
        if exists('/usr/bin/lxd', use_sudo=True):
            print colored('##################################', 'blue')
            print colored('##### LDX already Installed ######', 'blue')
            print colored('##################################', 'blue')
        else:
            sudo('sudo apt-get -y install lxd')

        #Add the public LinuxContainers.org image repository by running
        sudo('lxc remote add lxc-org images.linuxcontainers.org')

        #Copy the 32-bit Ubuntu 14.04 container image to your system with the command
        #Copy the 64-bit Centos 7.0 container image to your system with the command
        #https: // images.linuxcontainers.org /
        ubuntu_img = sudo('lxc image list | grep "trusty (i386)"')
        if(ubuntu_img != ""):
            print colored('##############################################', 'blue')
            print colored('#### LXC Ubuntu Trusty IMG already exists ####', 'blue')
            print colored('##############################################', 'blue')
        else:
            sudo('lxc image copy lxc-org:/ubuntu/trusty/i386 local: --alias=trusty32')

        centos_img = sudo('lxc image list | grep "Centos 7"')
        if (centos_img != ""):
            print colored('##############################################', 'blue')
            print colored('#### LXC Centos 7 x64 IMG already exists #####', 'blue')
            print colored('##############################################', 'blue')
        else:
            sudo('lxc image copy lxc-org:/centos/7/amd64 local: --alias=centos764')

        #centos_img = sudo('lxc image list | grep "Centos 6"')
        #if (centos_img != ""):
        #    print colored('##############################################', 'blue')
        #    print colored('#### LXC Centos 6 x64 IMG already exists #####', 'blue')
        #    print colored('##############################################', 'blue')
        #else:
        #   sudo('lxc image copy lxc-org:/centos/6/amd64 local: --alias=centos664')

        print colored('                          ', 'blue')
        print colored('##########################', 'blue')
        print colored('###### LXD PROVISION #####', 'blue')
        print colored('##########################', 'blue')
        #Launch a container based on this image with the command below.
        #This will start a container named "lxd-test-01" based on the "trusty32"
        # image (which is an alias for the image you copied in thre previous step).
        #sudo('lxc launch trusty32 lxd-ubuntu-01')
        #sudo('lxc launch images:centos/7/amd64 my-container')
        sudo('lxc launch centos764 lxd-centos-01')
        sudo('lxc launch centos764 lxd-centos-02')
        sudo('lxc launch centos764 lxd-centos-03')

        sudo('lxc image list')

        #Virtual Switch/Bridge Configuration
        #sudo('dpkg-reconfigure -p medium lxd')
        lxd_bridge = sudo('ip address show | grep lxdbr')
        if (lxd_bridge == ""):
            sudo('dpkg-reconfigure -p medium lxd')
        else:
            print colored('##################################', 'blue')
            print colored('##### NETWORK CONFIGURATION ######', 'blue')
            print colored('##################################', 'blue')
            print(lxd_bridge)

        #List the configured LXD Conteiners
        sudo('lxc list')

        print colored('1) Run file /bin/ls and note the output. (You will use the output for comparison in just a moment.)', 'green')
        print colored('##########################', 'green')
        print colored('2) Open a shell in the 32-bit container you launched in previous step with the command:', 'green')
        print colored('lxc exec lxd-test-01 bash', 'green')
        print colored('##########################', 'green')
        print colored('3) Inside the container, run file /bin/ls and compare the output to the output of the same command you ran', 'green')
        print colored('outside the container. You will see that inside the container the file is reported as a 32-bit ELF executable', 'green')
        print colored('outside the container the same file is listed as a 64-bit ELF executable.', 'green')
        print colored('##########################', 'green')
        print colored('4) Press Ctrl-D to exit the shell in the container.', 'green')
        print colored('##########################', 'green')
        print colored('5) The container is still running, so stop the container with:', 'green')
        print colored('lxc stop lxd-test-01.', 'green')

        print colored('##########################', 'red')

        print colored('Its NOT currently possible to mount NFS in an LXC Contenier', attrs=['bold'])
        print colored('Nothing that LXD can really do about it, nfs in the upstream', attrs=['bold'])
        print colored('kernel would need userns support, after which things will just start working.', attrs=['bold'])
        print colored('##########################', 'red')

        print colored('###########################', 'blue')
        print colored('## JUMPHOST PROVISIONING ##', 'blue')
        print colored('###########################', 'blue')

        sudo('lxc exec lxd-centos-01 -- echo root:toor | chpasswd')
        sudo('lxc exec lxd-centos-01 -- dhclient eth0 -r')
        sudo('lxc exec lxd-centos-01 -- dhclient eth0')
        sudo('lxc exec lxd-centos-01 -- yum clean all')
        sudo('lxc exec lxd-centos-01 -- yum install -y gcc glibc glibc-common gd gd-devel wget')
        sudo('lxc exec lxd-centos-01 -- yum install -y python-devel vim net-tools sudo openssh-server openssh-clients')
        sudo('lxc exec lxd-centos-01 -- yum install -y epel-release ')

        print colored('#########################################', 'blue')
        print colored('####### INSTALLING PYTHON FABRIC ########', 'blue')
        print colored('#########################################', 'blue')
        sudo('lxc exec lxd-centos-01 -- yum install -y python-pip')
        sudo('lxc exec lxd-centos-01 -- pip install --upgrade pip')
        sudo('lxc exec lxd-centos-01 -- pip install fabric')
        sudo('lxc exec lxd-centos-01 -- pip install termcolor')
        sudo('lxc exec lxd-centos-01 -- pip install iptools')

        print colored('#########################################', 'blue')
        print colored('######### INSTALLING SSH SERVER #########', 'blue')
        print colored('#########################################', 'blue')
        sudo('lxc exec lxd-centos-01 -- chkconfig sshd on')
        sudo('lxc exec lxd-centos-01 -- service sshd start')
        lxc_gw_ip = sudo('lxc exec lxd-centos-01 -- ifconfig eth0 | awk \'/inet /{print substr($2,1)}\'')

        print colored('###########################', 'blue')
        print colored('### CLIENT PROVISIONING ###', 'blue')
        print colored('###########################', 'blue')

        for i in range (2,4):
            sudo('lxc exec lxd-centos-0'+str(i)+' -- echo root:toor | chpasswd')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- dhclient eth0 -r')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- dhclient eth0')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- yum clean all')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- yum install -y python-devel vim net-tools sudo openssh-server openssh-clients wget')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- yum install -y epel-release')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- chkconfig sshd on')
            sudo('lxc exec lxd-centos-0'+str(i)+' -- service sshd start')
            lxc_ip_addr = sudo('lxc exec lxd-centos-0'+str(i)+' -- ifconfig eth0 | awk \'/inet /{print substr($2,1)}\'')
            if(i == 2):
                with open("./scripts/out_users_test.txt", "w") as file1:
                    file1.write(lxc_ip_addr+'\n')
                    print(file1)
            elif(i > 2):
                with open("./scripts/out_users_test.txt", "a") as file2:
                    file2.write(lxc_ip_addr+'\n')
                    print(file2)
            else:
                print colored('#########################################', 'blue')
                print colored('### CHECK THE FOR STATEMENT BOUNDRIES ###', 'blue')
                print colored('#########################################', 'blue')

        print colored('#################################################', 'blue')
        print colored('######## SYNC FILES WITH LXD BASTION HOST #######', 'blue')
        print colored('#################################################', 'blue')
        sudo('lxc file push /vagrant/scripts/* lxd-centos-01/root/')
        #sudo lxc file push /vagrant/scripts/* lxd-centos-01/home/ebarrirero/; sudo lxc exec lxd-centos-01 -- chown -R ebarrirero:ebarrirero /home/ebarrirero/

        print colored('##########################', 'blue')
        print colored('##### START FIREWALL #####', 'blue')
        print colored('##########################', 'blue')
        #https://help.ubuntu.com/lts/serverguide/lxc.html#lxc-network
        sudo('iptables -t nat -A PREROUTING -p tcp -i lo --dport 80 -j DNAT --to-destination '+lxc_gw_ip+':80')
        sudo('iptables -t nat -A PREROUTING -p tcp -i eth1 --dport 80 -j DNAT --to-destination '+lxc_gw_ip+':80')
        sudo('iptables -t nat -A PREROUTING -p tcp -i eth0 --dport 80 -j DNAT --to-destination '+lxc_gw_ip+':80')

        #$ sudo iptables -A FORWARD -p tcp -d 10.0.3.201 --dport 80 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT

        sudo('iptables -t nat -A PREROUTING -p tcp -i lo --dport 8338 -j DNAT --to-destination '+lxc_gw_ip+':8338')
        sudo('iptables -t nat -A PREROUTING -p tcp -i eth1 --dport 8338 -j DNAT --to-destination '+lxc_gw_ip+':8338')
        sudo('iptables -t nat -A PREROUTING -p tcp -i eth0 --dport 8338 -j DNAT --to-destination '+lxc_gw_ip+':8338')


        with hide('output'):
            fw = sudo('iptables -t nat -L')
        print colored(fw, 'red')

        print colored('######################################', 'blue')
        print colored('FIREWALL - FILTER TABLE STATUS:   ', 'blue')
        print colored('######################################', 'blue')
        with hide('output'):
            fw = sudo('iptables -L')
        print colored(fw, 'red')

        print colored('##########################', 'blue')
        print colored('## NETWORK CONFIGURATION #', 'blue')
        print colored('##########################', 'blue')
        with hide('output'):
            netconf = sudo('ip addr show')
        print colored(netconf, 'green')
