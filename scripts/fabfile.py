# Fabfile to:
#    - check the credentials for a certain user.
#    - to invoke: fab -f file func()
#    - $ fab -R local gen_key
#    - $ fab -R dev push_key
#    - $ fab -R dev test_key:username
# NOTE: http://docs.fabfile.org/en/1.12/usage/env.html#roles

# Import Fabric's API module#
#from fabric.api import *
from fabric.api import hosts, sudo, settings, hide, env, execute, prompt, run, local, task, put, cd, get
from fabric.contrib.files import append, exists
from termcolor import colored
import os
import sys
import logging
#import apt
import yum
import pwd
import iptools
import getpass

# As a good practice we can log the state of each phase in our script.
#  https://docs.python.org/2.7/howto/logging.html
logging.basicConfig(filename='check_ssh.log', level=logging.DEBUG)
logging.info('LOG STARTS')
#logging.debug('This message should go to the log file')
#logging.warning('And this, too')

# Open the server list file and split the IP o each server.
# http://www.tutorialspoint.com/python/string_split.htm
# with open("./out_users_test.txt", "r") as f:
#    ServerList = [line.split()[0] for line in f]
with open("out_users_test.txt", "r") as f:
    ServerList = [line.split()[0] for line in f]
    print(ServerList)

#with open("./conf/servers/greycom_prd_haproxy.txt", "r") as f:
#    GreyCom_prd_haproxy = [line.split()[0] for line in f]
#    print(GreyCom_prd_haproxy)

# In env.roledefs we define the remote servers. It can be IP Addrs or domain names.
env.roledefs = {
    'local': ['localhost'],
    'dev': ServerList,
    'staging': ['user@staging.example.com'],
    'production': ['user@production.example.com'],
    #'greycom_prd_haproxy': GreyCom_prd_haproxy
}

# Fabric user and pass.
#env.user = "root"
#env.password = "toor"
#env.key_filename = '/home/username/.ssh/id_rsa'
#env.warn_only=True
env.pararel=True
env.shell = "/bin/sh -c"
env.skip_bad_hosts=True
env.timeout=5


def show_help():
    with settings(warn_only=True):
        print ""
        print "Commands list:"
        print ""
        print "mode active                  Change behaviour mode to active"
        print "mode passive                 Change behaviour mode to passive"
        print "mode aggressive              Change behaviour mode to aggressive"
        print ""
        print "verbose on                   Turn verbose mode on (it shows more information)"
        print "verbose off                  Turn verbose mode off"
        print "email on                     Turn e-mail report on"
        print "email off                    Turn e-mail report off"
        print ""
        print "show statistics, stats       Show the statistics of the current instance."
        print ""
        print "clean logs                   Remove all log files"
        print "clean results                Remove all results files"
        print "clean calls                  Remove all the recorded calls"
        print "clean all                    Remove all files"
        print "                             (Use these commands carefully)"
        print ""
        print "hangup all                   Hang up all calls"
        print ""
        print "show warranty                Show the program warrany"
        print "show license                 Show the program license"
        print ""
        print "modify extension             To add or delete an Extension"
        print "restart                      To restart Artemisa"
        print ""
        print "s, q, quit, exit             Exit"

def show_roles():
    for key, value in sorted(env.roledefs.items()):
        print key, value

def command(cmd):
    with settings(warn_only=False):
        run(cmd)

def file_send(localpath,remotepath):
    with settings(warn_only=False):
        put(localpath,remotepath,use_sudo=True)

def file_send_mod(localpath,remotepath,modep):
    with settings(warn_only=False):
        put(localpath,remotepath,mode=modep,use_sudo=True)

def file_send_oldmod(localpath,remotepath):
    with settings(warn_only=False):
        put(localpath,remotepath,mirror_local_mode=True)

def file_get(remotepath, localpath):
    with settings(warn_only=False):
        get(remotepath,localpath+"."+env.host)

def sudo_command(cmd):
    with settings(warn_only=False):
        sudo(cmd)
        #eg : fab sudo_command:"apt-get install geany"

def sudoers_group_centos():
    with settings(warn_only=False):
        sudo('echo "%wheel        ALL=(ALL)       NOPASSWD: ALL" | (EDITOR="tee -a" visudo)')

def apt_package(action,package):
    with settings(warn_only=False):
        hostvm = sudo('hostname')
        if (action =="install"  ):
            aptcache = apt.Cache()
            if aptcache[package].is_installed:
                print colored('###############################################################################', 'yellow')
                print colored(package + ' ALREADY INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'yellow')
                print colored('###############################################################################', 'yellow')
            else:
                print colored('###############################################################################', 'blue')
                print colored(package + ' WILL BE INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'blue')
                print colored('###############################################################################', 'blue')
                sudo('apt-get update')
                sudo('apt-get install '+package)
                aptcachenew = apt.Cache()
                if aptcachenew[package].is_installed:
                    print colored('##################################################################################', 'green')
                    print colored(package + 'SUCCESFULLY INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'green')
                    print colored('##################################################################################', 'green')
                else:
                    print colored('#################################################################################', 'red')
                    print colored(package + 'INSTALLATION PROBLEM in:' + hostvm + '- IP:' + env.host_string, 'red')
                    print colored('#################################################################################', 'red')

        elif (action =="upgrade"  ):
            aptcache = apt.Cache()
            if aptcache[package].is_installed:
                print colored('############################################################################', 'yellow')
                print colored(package + ' TO BE UPGRADED in:' + hostvm + '- IP:' + env.host_string, 'yellow')
                print colored('############################################################################', 'yellow')
                sudo('apt-get update')
                sudo('apt-get install --only-upgrade '+package)
            else:
                print colored('###########################################################################', 'red')
                print colored(package + ' NOT INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'red')
                print colored('###########################################################################', 'red')

        else:
            print colored('############################################################################', 'yellow')
            print colored('Usage eg1: $ fab -R dev apt_package:install,cron', 'red')
            print colored('Usage eg2: $ fab -R dev apt_package:upgrade,gcc', 'red')
            print colored('############################################################################', 'blue')

def yum_package(action, package):
    with settings(warn_only=False):
        hostvm = sudo('hostname')
        if(action =="install"):
            #yumcache = yum.YumBase()
            #print(yumcache.rpmdb.searchNevra(name=package))
            try:
                package_inst = sudo('yum list install '+package)
                print(package_inst)
                #if yumcache.rpmdb.searchNevra(name=package):
                # if not package_inst:
                if (package_inst == "" ):
                    print colored('###############################################################################', 'blue')
                    print colored(package + ' WILL BE INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'blue')
                    print colored('###############################################################################', 'blue')
                    try:
                        sudo('yum install -y '+package)
                        #yumcache = yum.YumBase()
                        #if yumcache.rpmdb.searchNevra(name=package):
                        package_inst = sudo('yum list install ' + package)
                        if (package_inst == ""):
                            print colored('#################################################################################', 'red')
                            print colored(package + ' INSTALLATION PROBLEM in:' + hostvm + '- IP:' + env.host_string, 'red')
                            print colored('#################################################################################', 'red')
                        else:
                            print colored('##################################################################################', 'green')
                            print colored(package + ' SUCCESFULLY INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'green')
                            print colored('##################################################################################', 'green')
                    except:
                            print colored('#################################################################################', 'red')
                            print colored(package + ' INSTALLATION PROBLEM in:' + hostvm + '- IP:' + env.host_string, 'red')
                            print colored('#################################################################################', 'red')
                else:
                    print colored('###############################################################################', 'yellow')
                    print colored(package + ' ALREADY INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'yellow')
                    print colored('###############################################################################', 'yellow')
            except:
                print colored('#################################################################################', 'red')
                print colored(package + ' INSTALLATION PROBLEM in:' + hostvm + '- IP:' + env.host_string, 'red')
                print colored('#################################################################################', 'red')

        elif (action =="upgrade"  ):
            #yumcache = yum.YumBase()
            #print(yumcache.rpmdb.searchNevra(name=package))
            #if yumcache.rpmdb.searchNevra(name=package):
            try:
                package_inst = sudo('yum list install ' + package)
                print(package_inst)
                if (package_inst == ""):
                    print colored('###########################################################################', 'red')
                    print colored(package + ' NOT INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'red')
                    print colored('###########################################################################', 'red')
                else:
                    print colored('############################################################################', 'yellow')
                    print colored(package + ' TO BE UPGRADED in:' + hostvm + '- IP:' + env.host_string, 'yellow')
                    print colored('############################################################################', 'yellow')
                    sudo('yum update -y '+package)
            except:
                print colored('###########################################################################', 'red')
                print colored(package + ' NOT INSTALLED in:' + hostvm + '- IP:' + env.host_string, 'red')
                print colored('###########################################################################', 'red')

        else:
            print colored('############################################################################', 'yellow')
            print colored('Usage eg1: $ fab -R dev yum_package:install,cron', 'red')
            print colored('Usage eg2: $ fab -R dev yum_package:upgrade,gcc', 'red')
            print colored('############################################################################', 'blue')

def user_add_centos(usernamec):
    with settings(warn_only=True):
        #usernamep = prompt("Which USERNAME you like to CREATE & PUSH KEYS?")
        #user_exists = sudo('cat /etc/passwd | grep '+usernamep)
        #user_exists =sudo('grep "^'+usernamep+':" /etc/passwd')
        ##user_exists = sudo('cut -d: -f1 /etc/passwd | grep ' + usernamep)
        #print colored(user_exists, 'green')
        #print(env.host_string)
        #sudo('uname -a')

        try:
        ##if(user_exists != ""):
            user_exists = sudo('cut -d: -f1 /etc/passwd | grep '+usernamec)
            if (user_exists != ""):
                print colored('##############################', 'green')
                print colored('"' + usernamec + '" already exists', 'green')
                print colored('##############################', 'green')
                sudo('gpasswd -a ' + usernamep + ' wheel')
            else:
                print colored('#################################', 'green')
                print colored('"' + usernamec + '" doesnt exists', 'green')
                print colored('WILL BE CREATED', 'green')
                print colored('##################################', 'green')
                sudo('useradd ' + usernamec + ' -m -d /home/' + usernamec)
                #sudo('echo "' + usernamep + ':' + usernamep + '" | chpasswd')
                sudo('gpasswd -a ' + usernamep + ' wheel')
        except:
        ##else:
            #print colored('######################################################', 'green')
            #print colored('"' + usernamec + '" couldnt be created for some reason', 'green')
            #print colored('######################################################', 'green')
            print colored('#################################', 'green')
            print colored('"' + usernamec + '" doesnt exists', 'green')
            print colored('WILL BE CREATED', 'green')
            print colored('##################################', 'green')
            sudo('useradd ' + usernamec + ' -m -d /home/' + usernamec)
            sudo('gpasswd -a ' + usernamec + ' wheel')

def change_pass(usernameu,upass):
    with settings(warn_only=False):
        try:
        ##if(user_exists != ""):
            user_exists = sudo('cut -d: -f1 /etc/passwd | grep '+usernameu)
            if (user_exists != ""):
                print colored('#######################################', 'green')
                print colored('"' + usernameu + '" PASSWORD will be changed', 'green')
                print colored('#######################################', 'green')
                sudo('echo '+usernameu+':'+upass+' | chpasswd')
            else:
                print colored('#################################', 'red')
                print colored('"' + usernameu + '" doesnt exists', 'red')
                print colored('#################################', 'red')
        except:
        ##else:
            print colored('#################################', 'red')
            print colored('"' + usernameu + '" doesnt exists', 'red')
            print colored('##################################', 'red')

def key_gen(usernameg):
    with settings(warn_only=False):
        #usernameg = prompt("Which USERNAME you like to GEN KEYS?")
        #user_exists = sudo('cut -d: -f1 /etc/passwd | grep '+usernameg)
        #user_exists = sudo('cat /etc/passwd | grep ' + usernameg)
        try:
            user_struct = pwd.getpwnam(usernameg)
            user_exists = user_struct.pw_gecos.split (",")[0]
            print colored(user_exists, 'green')
            if (user_exists == "root"):
                print colored('#######################################################', 'blue')
                print colored('ROOT user CANT be changed', 'blue')
                print colored('#######################################################', 'blue')

            elif os.path.exists('/home/'+usernameg+'/.ssh/id_rsa'):
                print colored(str(os.path.exists('/home/'+usernameg+'/.ssh/id_rsa')), 'blue')
                print colored('###########################################', 'blue')
                print colored('username: '+usernameg+' KEYS already EXISTS', 'blue')
                print colored('###########################################', 'blue')
            else:
                print colored('###########################################', 'blue')
                print colored('username: ' + usernameg + ' Creating KEYS', 'blue')
                print colored('###########################################', 'blue')
                sudo("ssh-keygen -t rsa -f /home/" + usernameg + "/.ssh/id_rsa -N ''", user=usernameg)
                # http://unix.stackexchange.com/questions/36540/why-am-i-still-getting-a-password-prompt-with-ssh-with-public-key-authentication
                # sudo('chmod 700 /home/' + usernameg)
                sudo('chmod 755 /home/' + usernameg)
                sudo('chmod 755 /home/' + usernameg + '/.ssh')
                sudo('chmod 600 /home/' + usernameg + '/.ssh/id_rsa')
                sudo('gpasswd -a ' + usernameg + ' wheel')
        except KeyError:
            print colored('User '+usernameg+' does not exist', 'red')
            print colored('#######################################################', 'blue')
            print colored('Consider that we generate user: username pass: username', 'blue')
            print colored('#######################################################', 'blue')

            sudo('useradd ' + usernameg + ' -m -d /home/' + usernameg)
            sudo('echo "' + usernameg + ':' + usernameg + '" | chpasswd')
            sudo("ssh-keygen -t rsa -f /home/" + usernameg + "/.ssh/id_rsa -N ''", user=usernameg)
            # http://unix.stackexchange.com/questions/36540/why-am-i-still-getting-a-password-prompt-with-ssh-with-public-key-authentication
            # sudo('chmod 700 /home/' + usernameg)
            sudo('chmod 755 /home/' + usernameg)
            sudo('chmod 755 /home/' + usernameg + '/.ssh')
            sudo('chmod 600 /home/' + usernameg + '/.ssh/id_rsa')
            sudo('gpasswd -a ' + usernameg + ' wheel')

def key_read_file(key_file):
    with settings(warn_only=False):
        key_file = os.path.expanduser(key_file)
        if not key_file.endswith('pub'):
            raise RuntimeWarning('Trying to push non-public part of key pair')
        with open(key_file) as f:
            return f.read()

def key_append(usernamea):
    with settings(warn_only=False):
        if(usernamea == "root"):
            key_file = '/'+ usernamea+'/.ssh/id_rsa.pub'
            key_text = key_read_file(key_file)
            if exists('/'+usernamea+'/.ssh/authorized_keys', use_sudo=True):
                local('sudo chmod 701 /home/' + usernamea)
                local('sudo chmod 741 /home/' + usernamea + '/.ssh')
                local('sudo chmod 604 /home/' + usernamea + '/.ssh/id_rsa.pub')
                print colored('#########################################', 'blue')
                print colored('##### authorized_keys file exists #######', 'blue')
                print colored('#########################################', 'blue')
                append('/'+usernamea+'/.ssh/authorized_keys', key_text, use_sudo=True)
                sudo('chown -R ' + usernamea + ':' + usernamea + ' /home/' + usernamea + '/.ssh/')
                local('sudo chmod 700 /home/' + usernamea)
                local('sudo chmod 700 /home/' + usernamea + '/.ssh')
                local('sudo chmod 600 /home/' + usernamea + '/.ssh/id_rsa.pub')
            else:
                sudo('mkdir -p /'+usernamea+'/.ssh/')
                sudo('touch /'+usernamea+'/.ssh/authorized_keys')
                append('/'+ usernamea+'/.ssh/authorized_keys', key_text, use_sudo=True)
                sudo('chown -R ' + usernamea + ':' + usernamea + ' /home/' + usernamea + '/.ssh/')
                # put('/home/'+usernamea+'/.ssh/authorized_keys', '/home/'+usernamea+'/.ssh/')
                local('sudo chmod 700 /home/' + usernamea)
                local('sudo chmod 700 /home/' + usernamea + '/.ssh')
                local('sudo chmod 600 /home/' + usernamea + '/.ssh/id_rsa.pub')

        else:
            key_file = '/home/'+usernamea+'/.ssh/id_rsa.pub'
            local('sudo chmod 701 /home/' + usernamea)
            local('sudo chmod 741 /home/' + usernamea + '/.ssh')
            local('sudo chmod 604 /home/' + usernamea + '/.ssh/id_rsa.pub')
            key_text = key_read_file(key_file)
            local('sudo chmod 700 /home/' + usernamea)
            local('sudo chmod 700 /home/' + usernamea + '/.ssh')
            local('sudo chmod 600 /home/' + usernamea + '/.ssh/id_rsa.pub')
            if exists('/home/'+usernamea+'/.ssh/authorized_keys', use_sudo=True):
                print colored('#########################################', 'blue')
                print colored('##### authorized_keys file exists #######', 'blue')
                print colored('#########################################', 'blue')
                append('/home/'+usernamea+'/.ssh/authorized_keys', key_text, use_sudo=True)
                sudo('chown -R ' + usernamea + ':' + usernamea + ' /home/' + usernamea + '/.ssh/')
            else:
                sudo('mkdir -p /home/'+usernamea+'/.ssh/')
                sudo('touch /home/' + usernamea + '/.ssh/authorized_keys')
                append('/home/'+usernamea+'/.ssh/authorized_keys', key_text, use_sudo=True)
                sudo('chown -R ' + usernamea + ':' + usernamea + ' /home/' + usernamea + '/.ssh/')
            #put('/home/'+usernamea+'/.ssh/authorized_keys', '/home/'+usernamea+'/.ssh/')

def key_test(usernamet):
    with settings(warn_only=False):
        # TAKE THE HOME DIR FROM /ETC/PASSWD
        hostvm = sudo('hostname')
        local('sudo chmod 701 /home/' + usernamet)
        local('sudo chmod 741 /home/' + usernamet + '/.ssh')
        local_user=getpass.getuser()
        if (os.path.exists('/home/'+local_user+'/temp/')):
            print colored('##################################', 'blue')
            print colored('##### Directory Exists ###########', 'blue')
            print colored('##################################', 'blue')
        else:
            local('mkdir ~/temp')

        local('sudo cp /home/'+usernamet+'/.ssh/id_rsa ~/temp/id_rsa')
        local('sudo chown -R '+local_user+':'+local_user+' ~/temp/id_rsa')
        local('chmod 600 ~/temp/id_rsa')
        #local('sudo chmod 604 /home/' + usernamet + '/.ssh/id_rsa')

        # FIX DONE! - Must copy the key temporaly with the proper permissions
        # in the home directory of the current user executing fabric to use it.
        # Temporally we comment the line 379 and the script must be run by
        # user that desires to test it keys
        #[ntorres@jumphost fabric]$ ssh -i /home/ntorres/.ssh/id_rsa ntorres@10.0.3.113   Warning: Permanently added '10.0.3.113' (ECDSA) to the list of known hosts.
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        #@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        #Permissions 0604 for '/home/ntorres/.ssh/id_rsa' are too open.
        #It is required that your private key files are NOT accessible by others.
        #This private key will be ignored.
        #bad permissions: ignore key: /home/ntorres/.ssh/id_rsa
        #Permission denied (publickey).
        #NOTE:
        #there is no way to bypass the keyfile permission check with ssh or ssh-add
        #(and you can't trick it with named pipe or such). Besides, you do not actually want to trick ssh,' \
        #' but just to be able to use your key files.

        if (os.path.exists('/home/'+usernamet+'/.ssh/')):
            ssh_test = local('ssh -i ~/temp/id_rsa -o "StrictHostKeyChecking no" -q '+usernamet+'@'+env.host_string+' exit')
            if (ssh_test.succeeded):
                print colored('###################################################', 'blue')
                print colored(usernamet+' WORKED! in:'+hostvm+' IP:'+env.host_string, 'blue')
                print colored('###################################################', 'blue')
                local('sudo chmod 700 /home/'+usernamet)
                local('sudo chmod 700 /home/'+usernamet+'/.ssh')
                #local('sudo chmod 600 /home/'+usernamet+'/.ssh/id_rsa')
                local('sudo rm ~/temp/id_rsa')
        else:
            print colored('###################################################', 'red')
            print colored(usernamet+' FAIL! in:'+hostvm+'- IP:'+env.host_string, 'red')
            print colored('###################################################', 'red')

def ruby_install_centos():
    with settings(warn_only=False):
        # sudo('yum ruby ruby-devel rubygems')
        # yum groupinstall -y development
        # yum groupinstall -y 'development tools'
        sudo('yum groupinstall "Development Tools"')
        sudo('yum install -y git-core zlib zlib-devel gcc-c++ patch readline readline-devel')
        sudo('yum install -y libyaml-devel libffi-devel openssl-devel make bzip2 autoconf automake libtool bison curl sqlite-devel')

        #with cd('/home/'+usernamei+'/'):
        with cd('~'):
            run('gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3')
            run('\curl -sSL https://get.rvm.io | bash -s stable --ruby')
            run('source ~/.rvm/scripts/rvm')
            run('gem install bundler')

def kifezero_install_centos():
    with settings(warn_only=False):
        if exists('/tmp/chefdk-0.17.17-1.el7.x86_64.rpm', use_sudo=True):
            print colored('###################################################', 'blue')
            print colored('##### Chef Development Kit already installed ######', 'blue')
            print colored('####################################################', 'blue')
        else:
            print colored('######################################################', 'red')
            print colored('###### Chef Development Kit will be installed  #######', 'red')
            print colored('######################################################', 'red')
            run('wget -P /tmp/ https://packages.chef.io/stable/el/7/chefdk-0.17.17-1.el7.x86_64.rpm')
            run('rpm -Uvh /tmp/chefdk-0.17.17-1.el7.x86_64.rpm')

        try:
            knifezero_inst = run('chef gem list | grep knife-zero')
            if(knifezero_inst ==""):
                run('chef gem install knife-zero')
            else:
                print colored('##############################################', 'blue')
                print colored('##### knife-zero already installed ###########', 'blue')
                print colored('##############################################', 'blue')

            if exists('/opt/chefdk/embedded/bin/knife', use_sudo=True):
                print colored('###########################################', 'blue')
                print colored('##### Knife-zero correctly installed ######', 'blue')
                print colored('###########################################', 'blue')
            else:
                print colored('###########################################', 'red')
                print colored('###### Check chef-zero installation #######', 'red')
                print colored('###########################################', 'red')
        except:
            run('chef gem install knife-zero')
            if exists('/opt/chefdk/embedded/bin/knife', use_sudo=True):
                print colored('###########################################', 'blue')
                print colored('##### Knife-zero correctly installed ######', 'blue')
                print colored('###########################################', 'blue')
            else:
                print colored('###########################################', 'red')
                print colored('###### Check chef-zero installation #######', 'red')
                print colored('###########################################', 'red')

def kifezero_conf_centos(usernamek):
    with settings(warn_only=False):
        if exists('/home/'+usernamek+'/my_chef_repo', use_sudo=True):
            print colored('#########################################', 'blue')
            print colored('##### Chef repo dir already exists ######', 'blue')
            print colored('#########################################', 'blue')
        else:
            print colored('################################################', 'red')
            print colored('###### Dir my_chef_repo will be created  #######', 'red')
            print colored('################################################', 'red')
            run('mkdir /home/'+usernamek+'/my_chef_repo')

        try:
            knifezero_inst = run('chef gem list | grep knife-zero')
            if(knifezero_inst ==""):
                run('chef gem install knife-zero')
            else:
                print colored('##############################################', 'blue')
                print colored('##### knife-zero already installed ###########', 'blue')
                print colored('##############################################', 'blue')

            if exists('/opt/chefdk/embedded/bin/knife', use_sudo=True):
                print colored('###########################################', 'blue')
                print colored('##### Knife-zero correctly installed ######', 'blue')
                print colored('###########################################', 'blue')
            else:
                print colored('###########################################', 'red')
                print colored('###### Check chef-zero installation #######', 'red')
                print colored('###########################################', 'red')
        except:
            run('chef gem install knife-zero')
            if exists('/opt/chefdk/embedded/bin/knife', use_sudo=True):
                print colored('###########################################', 'blue')
                print colored('##### Knife-zero correctly installed ######', 'blue')
                print colored('###########################################', 'blue')
            else:
                print colored('###########################################', 'red')
                print colored('###### Check chef-zero installation #######', 'red')
                print colored('###########################################', 'red')

def nfs_server_centos7(nfs_dir):
    with settings(warn_only=False):
        sudo('yum install -y nfs-utils libnfsidmap libnfsidmap-devel nfs4-acl-tools')

        if exists('/var/'+nfs_dir, use_sudo=True):
            print colored('###########################################', 'blue')
            print colored('####### Directory already created #########', 'blue')
            print colored('###########################################', 'blue')
        else:
            print colored('###########################################', 'red')
            print colored('###### Creating NFS share Directory #######', 'red')
            print colored('###########################################', 'red')
            sudo('mkdir /var/'+nfs_dir)
            sudo('chmod -R 777 /var/'+nfs_dir+'/')
        try:
            ip_addr=sudo('ifconfig eth0 | awk \'/inet /{print substr($2,1)}\'')
            netmask=sudo('ifconfig eth0 | awk \'/inet /{print substr($4,1)}\'')
            subnet_temp = iptools.ipv4.subnet2block(str(ip_addr) + '/' + str(netmask))
            subnet = subnet_temp[0]
            #sudo('echo "/var/' + nfs_dir + '     ' + subnet + '/' + netmask + '(rw,sync,no_root_squash,no_all_squash)" > /etc/exports')
            sudo('echo "/var/'+nfs_dir+'     *(rw,sync,no_root_squash)" > /etc/exports')
        except:
            ip_addr = sudo('ifconfig enp0s8 | awk \'/inet /{print substr($2,1)}\'')
            etmask = sudo('ifconfig enp0s8 | awk \'/inet /{print substr($4,1)}\'')
            subnet_temp = iptools.ipv4.subnet2block(str(ip_addr) + '/' + str(netmask))
            subnet = subnet_temp[0]
            # sudo('echo "/var/' + nfs_dir + '     ' + subnet + '/' + netmask + '(rw,sync,no_root_squash,no_all_squash)" > /etc/exports')
            sudo('echo "/var/' + nfs_dir + '     *(rw,sync,no_root_squash)" > /etc/exports')

        #sudo('sudo exportfs -a')

        sudo('systemctl enable rpcbind')
        sudo('systemctl start rpcbind')

        sudo('systemctl enable nfs-server')
        sudo('systemctl start nfs-server')

        #sudo firewall-cmd --zone=public --add-service=nfs --permanent
        #sudo firewall-cmd --zone=public --add-service=rpc-bind --permanent
        #sudo firewall-cmd --zone=public --add-service=mountd --permanent
        #sudo firewall-cmd --reload

def cachefs_install(nfs_dir, nfs_server_ip, cachetag="mycache",cachedir="/var/cache/fscache", selinux='False'):
    #fab -R dev cachefs_install:nfsshare,\"172.28.128.3\",mycache-test,/var/cache/fscache-test/
    with settings(warn_only=False):
        ### INSTALL FS-CACHE PACKAGE ###
        sudo('yum install -y cachefilesd')

        ### CHECK IF SELINUX ENFORMENT is ENABLED ###
        print colored('=====================================================' , 'blue')
        print colored('RELOCATING THE CACHE WITH SELINUX ENFORCEMENT ENABLED' , 'blue')
        print colored('=====================================================' , 'blue')
        selinux = bool(strtobool(selinux))
        #setenforce enforcing
        # setenforce permissive
        # sestatus
        try:
            selinux_mode = (sudo('sestatus | grep "Current mode:                   enforcing"'))
            if(selinux_mode != ""):
                selinux=bool(strtobool('True'))
            else:
                selinux=bool(strtobool('False'))
        except:
            selinux_mode = (sudo('sestatus | grep "Current mode:                   permissive"'))
            if (selinux_mode != ""):
                selinux = bool(strtobool('False'))
            else:
                selinux = bool(strtobool('True'))
        #finally:
        #   Peace of code that will be always executed no mater what
        ### END OF SELINUX ENFORMENT is ENABLED CHECK ###

        ### CONFIGURING FS-CACHE SELINUX ###
        ### We'll use the documentation folder to host them ###
        if exists('/etc/cachefilesd.conf', use_sudo=True):
            print colored('#################################', 'yellow')
            print colored('##### CACHEFS conf file OK ######', 'yellow')
            print colored('#################################', 'yellow')

            # ====================
            # RELOCATING THE CACHE
            # ====================
            # By default, the cache is located in /var/cache/fscache, but this may be
            # undesirable.  Unless SELinux is being used in enforcing mode, relocating the
            # cache is trivially a matter of changing the "dir" line in /etc/cachefilesd.

            # However, if SELinux is being used in enforcing mode, then it's not that
            # simple.  The security policy that governs access to the cache must be changed.

            with cd('/usr/share/doc/cachefilesd-*/'):
                if (selinux == False):
                    if exists(cachedir, use_sudo=True):
                        print colored('###########################################', 'yellow')
                        print colored('##### Local Cache Dir already exists ######', 'yellow')
                        print colored('###########################################', 'yellow')
                    else:
                        sudo('mkdir '+cachedir)

                    file_send_mod('/vagrant/scripts/conf/cachefs/cachefilesd.conf', '/etc/cachefilesd.conf', '664')
                    """
                elif(selinux == True):
                    print colored('#######################################', 'red', attrs=['bold'])
                    print colored('########### NOT WORKING YET! ##########', 'red', attrs=['bold'])
                    print colored('#######################################', 'red', attrs=['bold'])

                    # Default policy interface for the CacheFiles userspace management daemon
                    ##/usr/share/selinux/devel/include/contrib/cachefilesd.if
                    sudo('yum install -y checkpolicy selinux-policy*')
                    print colored(sudo('sestatus'), 'cyan', attrs=['bold'])

                    if exists('/usr/share/doc/cachefilesd-*/'+cachetag, use_sudo=True):
                        print colored('##########################################', 'yellow')
                        print colored('##### Conf Cache Dir already exists ######', 'yellow')
                        print colored('##########################################', 'yellow')
                    else:
                        sudo('mkdir '+cachetag)

                    if exists('/usr/share/doc/cachefilesd-*/'+cachetag+'/'+cachetag+'.te', use_sudo=True):
                        print colored('########################################', 'yellow')
                        print colored('##### '+cachetag+'.te file alredy exists', 'yellow')
                        print colored('########################################', 'yellow')
                    else:
                        sudo('touch '+cachetag+'/'+cachetag+'.te')
                        line1='['+cachetag+'.te]'
                        line2='policy_module('+cachetag+',1.0.0)'
                        line3='require { type cachefiles_var_t; }'
                        filename_te = str(cachetag+'/'+cachetag+'.te')
                        append(filename_te, [line1,line2,line3], use_sudo=True, partial=False, escape=True, shell=False)

                    if exists('/usr/share/doc/cachefilesd-*/'+cachetag+'.fc', use_sudo=True):
                        print colored('##########################################', 'yellow')
                        print colored('##### '+cachetag+'.fc file alredy exists'  , 'yellow')
                        print colored('##########################################', 'yellow')
                    else:
                        sudo('touch '+cachetag+'/'+cachetag+'.fc')
                        line1 ='['+cachetag+'.fc]'
                        line2 =cachedir+'(/.*)? gen_context(system_u:object_r:cachefiles_var_t,s0)'
                        filename_te = str(cachetag + '/' + cachetag + '.fc')
                        append(filename_te, [line1, line2], use_sudo=True, partial=False, escape=True, shell=False)

                    with cd('/usr/share/doc/cachefilesd-*/'+cachetag):
                        sudo('make -f /usr/share/selinux/devel/Makefile '+cachetag+'.pp')
                        sudo('semodule -i '+cachetag+'.pp')
                        sudo('semodule -l | grep '+cachetag)

                    if exists(cachedir, use_sudo=True):
                        print colored('###########################################', 'yellow')
                        print colored('##### Local Cache Dir already exists ######', 'yellow')
                        print colored('###########################################', 'yellow')
                        sudo('restorecon ' + cachedir)
                        sudo('ls -dZ ' + cachedir)
                    else:
                        sudo('mkdir '+cachedir)
                        sudo('restorecon '+cachedir)
                        sudo('ls -dZ '+cachedir)

                    #Modify /etc/cachefilesd.conf to point to the correct directory and then
                    #start the cachefilesd service. In our case in /conf/cachefield.conf
                    #config file
                    file_send_mod('/vagrant/scripts/conf/cachefs/cachefilesd.conf', '/etc/cachefilesd.conf', '664')

                    #The auxiliary policy can be later removed by:""
                    #semodule -r '+cachetag+'.pp

                    #If the policy is updated, then the version number in policy_module() in
                    #'+cachetag+'.te should be increased and the module upgraded:
                	#semodule -u '+cachetag+'.pp
                """
                else:
                    print colored('#############################################################################', 'blue')
                    print colored('##### Selinux supported in Permissive mode or when Selinux is disabled ######', 'blue')
                    print colored('#############################################################################', 'blue')

        else:
            print colored('#################################################################', 'red')
            print colored('##### cachefilesd conf does not exists (Check Instalation) ######', 'red')
            print colored('#################################################################', 'red')

        ## get status ##
        fscachestat = sudo('service cachefilesd status | grep Active | cut -d\' \' -f5')
        parts = fscachestat.split('\n')
        fscachestat = parts[1]

        if fscachestat == "inactive":
            ## start it ##
            sudo('service cachefilesd start')
            print colored('=================================', 'blue')
            print colored('         FSCACHE STARTED         ', 'blue')
            print colored('=================================', 'blue')
            ## Uncoment start it at boot ##
            # systemd enable cachefilesd.service
        elif fscachestat == "active":
            ## stop it ##
            sudo('service cachefilesd restart')
            print colored('=================================', 'blue')
            print colored('        FSCACHE RE-STARTED       ', 'blue')
            print colored('=================================', 'blue')
        else:
            print colored('################################################################', 'red')
            print colored('##### cachefilesd Serv does not exists (Check Instalation) ######', 'red')
            print colored('################################################################', 'red')


        try:
            part_mounted = sudo('df -h | grep /mnt/nfs/var/'+nfs_dir)
            if(part_mounted ==""):
                #mount nfs client with CacheFS support
                sudo('mount -t nfs -o fsc '+nfs_server_ip+':/var/'+nfs_dir+' /mnt/nfs/var/'+nfs_dir+'/')
            else:
                print colored('##################################################', 'yellow')
                print colored('##### cachefilesd partition already mounted ######', 'yellow')
                print colored('##################################################', 'yellow')
                #sudo('mount -t nfs -o fsc ' + nfs_server_ip + ':/var/' + nfs_dir + ' /mnt/nfs/var/' + nfs_dir + '/')

            sudo('cat /proc/fs/nfsfs/servers')
            sudo('cat /proc/fs/fscache/stats')

        except:
            print colored('#########################################', 'red')
            print colored('##### Problem mounting cachefilesd ######', 'red')
            print colored('#########################################', 'red')

        ### TESTING ###
        print colored('===============================', 'blue')
        print colored('        FILE NOT CACHED        ', 'blue')
        print colored('===============================', 'blue')
        sudo('time cp /mnt/nfs/var/nfsshare/chefdk-0.17.17-1.el7.x86_64.rpm /tmp')

        print colored('==============================', 'blue')
        print colored('        FILE NFS CACHED :)    ', 'blue')
        print colored('==============================', 'blue')
        sudo('time cp /mnt/nfs/var/nfsshare/chefdk-0.17.17-1.el7.x86_64.rpm /dev/null')

def nfs_client_centos7(nfs_dir,nfs_server_ip):
    with settings(warn_only=False):
        sudo('yum install -y nfs-utils')
        sudo('mkdir -p /mnt/nfs/var/'+nfs_dir)
        sudo('mount -t nfs '+nfs_server_ip+':/var/'+nfs_dir+' /mnt/nfs/var/'+nfs_dir+'/')
        run('df -kh | grep nfs')
        run('mount | grep nfs')

        try:
            run('touch /mnt/nfs/var/nfsshare/test_nfs')

        except:
            print colored('###########################################', 'red')
            print colored('###### NFS client installation Fail #######', 'red')
            print colored('###########################################', 'red')

def nfs_server_centos6(nfs_dir):
    with settings(warn_only=False):
        sudo('yum install -y nfs-utils nfs-utils-lib')

        if exists('/var/'+nfs_dir, use_sudo=True):
            print colored('###########################################', 'blue')
            print colored('####### Directory already created #########', 'blue')
            print colored('###########################################', 'blue')
        else:
            print colored('###########################################', 'red')
            print colored('###### Creating NFS share Directory #######', 'red')
            print colored('###########################################', 'red')
            sudo('mkdir /var/'+nfs_dir)
            sudo('chmod -R 777 /var/'+nfs_dir+'/')

        sudo('chkconfig nfs on')
        sudo('service rpcbind start')
        sudo('service nfs start')

        ip_addr=sudo('ifconfig eth0 | awk \'/inet /{print substr($2,6)}\'')
        netmask=sudo('ifconfig eth0 | awk \'/inet /{print substr($4,6)}\'')
        subnet_temp = iptools.ipv4.subnet2block(str(ip_addr) + '/' + str(netmask))
        subnet = subnet_temp[0]
        #sudo('echo "/var/' + nfs_dir + '     ' + subnet + '/' + netmask + '(rw,sync,no_root_squash,no_subtree_check)" > /etc/exports')
        sudo('echo "/var/'+nfs_dir+'     *(rw,sync,no_root_squash)" > /etc/exports')

        sudo('sudo exportfs -a')

        #sudo firewall-cmd --zone=public --add-service=nfs --permanent
        #sudo firewall-cmd --zone=public --add-service=rpc-bind --permanent
        #sudo firewall-cmd --zone=public --add-service=mountd --permanent
        #sudo firewall-cmd --reload

def nfs_client_centos6(nfs_dir,nfs_server_ip):
    with settings(warn_only=False):
        sudo('yum install -y nfs-utils nfs-utils-lib')
        sudo('mkdir -p /mnt/nfs/var/'+nfs_dir+'/')
        sudo('mount '+nfs_server_ip+':/var/'+nfs_dir+' /mnt/nfs/var/'+nfs_dir)
        run('df - kh | grep nfs')
        run('mount | grep nfs')

        try:
            run('touch /mnt/nfs/var/nfsshare/test_nfs')

        except:
            print colored('###########################################', 'red')
            print colored('###### Check NFS Client configuration #####', 'red')
            print colored('###########################################', 'red')

def nfs_server_ubuntu(nfs_dir):
    with settings(warn_only=False):
        sudo('apt-get update')
        sudo('apt-get -y install nfs-kernel-server')

        if exists('/var/'+nfs_dir, use_sudo=True):
            print colored('###########################################', 'blue')
            print colored('####### Directory already created #########', 'blue')
            print colored('###########################################', 'blue')
        else:
            print colored('###########################################', 'red')
            print colored('###### Creating NFS share Directory #######', 'red')
            print colored('###########################################', 'red')
            sudo('mkdir /var/'+nfs_dir)
            #sudo('chmod -R 777 /var/'+nfs_dir+'/')
            sudo('chown nobody:nogroup /var/'+nfs_dir+'/')

        #sudo('chkconfig nfs on')
        #sudo('service rpcbind start')
        #sudo('service nfs start')

        ip_addr=sudo('ifconfig eth0 | awk \'/inet /{print substr($2,6)}\'')
        netmask=sudo('ifconfig eth0 | awk \'/inet /{print substr($4,6)}\'')
        subnet_temp = iptools.ipv4.subnet2block(str(ip_addr) + '/' + str(netmask))
        subnet = subnet_temp[0]
        #sudo('echo "/var/' + nfs_dir + '     ' + subnet + '/' + netmask + '(rw,sync,no_root_squash,no_subtree_check)" > /etc/exports')
        sudo('echo "/var/'+nfs_dir+'     *(rw,sync,no_root_squash)" > /etc/exports')

        sudo('sudo exportfs -a')

        sudo('service nfs-kernel-server start')

        #sudo firewall-cmd --zone=public --add-service=nfs --permanent
        #sudo firewall-cmd --zone=public --add-service=rpc-bind --permanent
        #sudo firewall-cmd --zone=public --add-service=mountd --permanent
        #sudo firewall-cmd --reload

def haproxy_ws(action,ws_ip):
    with settings(warn_only=False):
        with cd('/etc/haproxy'):
            try:
                ws_conf = sudo('sudo cat haproxy.cfg | grep "'+ws_ip+':80 weight 1 check" | head -n1')
                #ws_conf = str(ws_conf.lstrip())
                print colored('=========================================', 'blue')
                print colored('Server ' + ws_ip + ' FOUND in haproxy.cfg', 'blue')
                print colored('=========================================', 'blue')
                print colored (ws_conf, 'cyan', attrs=['bold'])

                if ws_conf == "":
                    print colored('=========================================', 'red')
                    print colored('Server '+ws_ip+' NOT FOUND in haproxy.cfg', 'red')
                    print colored('=========================================', 'red')

                elif "disabled" in ws_conf and action == "add":
                    #we erase the last word "disabled" & create the new file add_ws
                    add_ws = ws_conf.rsplit(' ', 1)[0]
                    print colored('=========================================', 'blue')
                    print colored('SERVER '+ws_ip+' WILL BE ADDED to the HLB', 'blue')
                    print colored('=========================================', 'blue')
                    print colored('Line to be ADDED:', attrs=['bold'])
                    print colored(add_ws, 'cyan', attrs=['bold'])

                    print colored('Line to be REMOVED:', attrs=['bold'])
                    remove_ws = ws_conf
                    print colored(remove_ws, 'cyan', attrs=['bold'])

                    sudo('chmod 757 /etc/haproxy/')
                    sudo('chmod 606 /etc/haproxy/haproxy.cfg')
                    sed('/etc/haproxy/haproxy.cfg', remove_ws, add_ws, limit='', use_sudo=True, backup='.bak', flags='', shell=False)
                    #fabric.contrib.files.sed(filename, before, after, limit='', use_sudo=False, backup='.bak', flags='', shell=False)
                    #sudo('sed -i "/'+remove_ws+'/c\'+add_ws+' haproxy.cfg')
                    sudo('chmod 755 /etc/haproxy/')
                    sudo('chmod 600 /etc/haproxy/haproxy.cfg')

                    sudo('systemctl restart haproxy')

                    print colored('=============================================', 'blue', attrs=['bold'])
                    print colored('SERVER ' + ws_ip + ' SUCCESFULLY ADDED to HLB', 'blue', attrs=['bold'])
                    print colored('=============================================', 'blue', attrs=['bold'])

                elif "disabled" not in ws_conf and action == "remove":
                    add_ws = ws_conf + " disabled"
                    print colored('=================================================', 'blue')
                    print colored('SERVER ' + ws_ip + ' WILL BE REMOVED from the HLB', 'blue')
                    print colored('=================================================', 'blue')
                    print colored('Line to be ADDED:', attrs=['bold'])
                    print colored(add_ws, 'cyan', attrs=['bold'])

                    print colored('Line to be REMOVED:', attrs=['bold'])
                    remove_ws = ws_conf
                    print colored(remove_ws, 'cyan', attrs=['bold'])

                    sudo('chmod 757 /etc/haproxy/')
                    sudo('chmod 606 /etc/haproxy/haproxy.cfg')
                    sed('/etc/haproxy/haproxy.cfg', remove_ws, add_ws, limit='', use_sudo=True, backup='.bak', flags='', shell=False)
                    sudo('chmod 755 /etc/haproxy/')
                    sudo('chmod 600 /etc/haproxy/haproxy.cfg')

                    sudo('systemctl restart haproxy')

                    print colored('================================================', 'blue', attrs=['bold'])
                    print colored('SERVER ' + ws_ip + ' SUCCESFULLY REMOVED from HLB', 'blue', attrs=['bold'])
                    print colored('================================================', 'blue', attrs=['bold'])

                else:
                    print colored('===========================================================================', 'red')
                    print colored('WRONG ARGs or conditions unmets, eg: trying to add a WS that already exists', 'red')
                    print colored('===========================================================================', 'red')
            except:
                print colored('=======================================================', 'red')
                print colored('Problem found haproxy.cfg not found - check istallation', 'red')
                print colored('=======================================================', 'red')

def maltrail(role):
    with settings(warn_only=False):
        try:
            #DEPENDENCIAS for AMAZON LINUX:
            #sudo yum install libpcap-devel
            #sudo yum install libnet
            #sudo yum install python-devel
            #sudo yum install gcc-c++
            #sudo yum install git wget
            #wget http://packages.psychotic.ninja/6/base/x86_64/RPMS/schedtool-1.3.0-12.el6.psychotic.x86_64.rpm
            #sudo rpm -Uvh schedtool-1.3.0-12.el6.psychotic.x86_64.rpm
            #wget http://www.coresecurity.com/system/files/pcapy-0.10.6.zip
            #unzip pcapy-0.10.6.zip
            #sudo python setup.py install
            sudo('yum install -y git pcapy schedtool')
            with cd('/home/'+env.user+'/'):
                if exists('/home/'+env.user+'/maltrail', use_sudo=True):
                    print colored('###########################################', 'blue')
                    print colored('####### Directory already created #########', 'blue')
                    print colored('###########################################', 'blue')

                    if role=="sensor":
                        with cd ('maltrail'):
                            sudo('python sensor.py')
                            sudo('ping -c 1 136.161.101.53')
                            sudo('cat /var/log/maltrail/$(date +"%Y-%m-%d").log')

                    elif role=="server":
                        with cd('/home/'+env.user+'/'):
                            run('[[ -d maltrail ]] || git clone https://github.com/stamparm/maltrail.git')

                        with cd ('maltrail/'):
                            sudo('python server.py')
                            sudo('ping -c 1 136.161.101.53')
                            sudo('cat /var/log/maltrail/$(date +"%Y-%m-%d").log')

                    else:
                        print colored('=========================================', 'red')
                        print colored('Wrong arg: excects = "sensor" or "server"', 'red')
                        print colored('=========================================', 'red')
                else:
                    print colored('##########################################', 'red')
                    print colored('###### Creating Maltrail Directory #######', 'red')
                    print colored('##########################################', 'red')
                    if role == "sensor":
                        run('git clone https://github.com/stamparm/maltrail.git')
                        with cd ('maltrail/'):
                            sudo('python sensor.py ')
                            sudo('ping -c 1 136.161.101.53')
                            sudo('cat /var/log/maltrail/$(date +"%Y-%m-%d").log')
                            ### FOR THE CLIENT ###
                            #using configuration file '/home/ebarrirero/maltrail/maltrail.conf.sensor_ok'
                            #using '/var/log/maltrail' for log storage
                            #at least 384MB of free memory required
                            #updating trails (this might take a while)...
                            #loading trails...
                            #1,135,525 trails loaded

                            ### NOTE: ###
                            #in case of any problems with packet capture on virtual interface 'any',
                            #please put all monitoring interfaces to promiscuous mode manually (e.g. 'sudo ifconfig eth0 promisc')
                            #opening interface 'any'
                            #setting capture filter 'udp or icmp or (tcp and (tcp[tcpflags] == tcp-syn or port 80 or port 1080 or
                            #port 3128 or port 8000 or port 8080 or port 8118))'
                            #preparing capture buffer...
                            #creating 1 more processes (out of total 2)
                            #please install 'schedtool' for better CPU scheduling
                    elif role == "server":
                        with cd('/home/' + env.user + '/'):
                            run('[[ -d maltrail ]] || git clone https://github.com/stamparm/maltrail.git')
                        with cd ('maltrail/'):
                            sudo('python server.py')
                            sudo('ping -c 1 136.161.101.53')
                            sudo('cat /var/log/maltrail/$(date +"%Y-%m-%d").log')

                    else:
                        print colored('=========================================', 'red')
                        print colored('Wrong arg: excects = "sensor" or "server"', 'red')
                        print colored('=========================================', 'red')

                #To stop Sensor and Server instances (if running in background) execute the following:
                #sudo pkill -f sensor.py
                #pkill -f server.py

                #http://127.0.0.1:8338 (default credentials: admin:changeme!)

                #If option LOG_SERVER is set, then all events are being sent remotely to the Server,
                #otherwise they are stored directly into the logging directory set with option LOG_DIR,
                #which can be found inside the maltrail.conf.sensor_ok file's section [All].

                #In case that the option UPDATE_SERVER is set, then all the trails are being pulled from
                #the given location, otherwise they are being updated from trails definitions located inside
                #the installation itself.

                #Option UDP_ADDRESS contains the server's log collecting listening address
                #(Note: use 0.0.0.0 to listen on all interfaces), while option UDP_PORT contains
                #listening port value. If turned on, when used in combination with option LOG_SERVER,
                #it can be used for distinct (multiple) Sensor <-> Server architecture.

                #Same as for Sensor, when running the Server (e.g. python server.py) for the first time
                #and/or after a longer period of non-running, if option USE_SERVER_UPDATE_TRAILS is set to true,
                # it will automatically update the trails from trail definitions (Note: stored inside the
                # trails directory).
                # Should server do the trail updates too (to support UPDATE_SERVER)

        except:
            print colored('===========================', 'red')
            print colored('Problem installing MALTRAIL', 'red')
            print colored('===========================', 'red')

def iptables(action,ip_addr):
    with settings(warn_only=False):
        try:
        except:
            print colored('===========================', 'red')
            print colored('Problem installing MALTRAIL', 'red')
            print colored('===========================', 'red')

    #62.210.148.246
    #46.4.116.197
    #51.254.97.23
    #171.113.86.129

    #iptables -A INPUT -s <ip> -j DROP
    #iptables -A INPUT -s 62.210.148.246 -j DROP
    #iptables -A INPUT -s 46.4.116.197 -j DROP
    #iptables -A INPUT -s 51.254.97.23 -j DROP
    #iptables -A INPUT -s 171.113.86.129 -j DROP

    #for ip in list:
    #        iptables -A INPUT

"""
def db_backup():
    with settings(warn_only=False):
        #Check the DBs in PRD
        mysql -h ggcc-prd.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "show databases"
        +--------------------+
        | Database           |
        +--------------------+
        | information_schema |
        | ggcc_prd           |
        | innodb             |
        | mysql              |
        | performance_schema |
        | tmp                |
        +--------------------+

        mysql -h ggcc-prd.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "use ggcc_prd; show tables;"

        Database changed
        mysql> show tables;
        +----------------------------+
        | Tables_in_ggcc_prd         |
        +----------------------------+
        | category                   |
        | category_votes             |
        | category_weights           |
        | contest                    |
        | contest_agencies           |
        | contest_grouping           |
        | contest_status             |
        | contest_submitters_judges  |
        | contest_view               |
        | delayed_action             |
        | groups                     |
        | migrations                 |
        | report_shared              |
        | sessions                   |
        | stage                      |
        | submission                 |
        | submission_awards          |
        | submission_categories      |
        | submission_comments        |
        | submission_downloads       |
        | submission_favorite_shared |
        | submission_favorited       |
        | submission_files           |
        | submission_tags            |
        | submission_votes           |
        | throttle                   |
        | users                      |
        | users_groups               |
        | view                       |
        +----------------------------+
        29 rows in set (0.00 sec)

        mysql> SELECT table_name "Table Name", table_rows "Rows Count", round(((data_length + index_length)/1024/1024),2) "Table Size (MB)" FROM information_schema.TABLES WHERE table_schema = "ggcc_prd";

        mysql> select * from  mysql.user;
        mysql> describe mysql.user;
        mysql> select User from mysql.user;

        mysql> select User from mysql.user;
        +----------------+
        | User           |
        +----------------+
        | grey_ggcc_user |
        | greyrdsadmin   |
        | rdsadmin       |
        +----------------+
        3 rows in set (0.00 sec)

        mysql> show grants for 'greyrdsadmin'@'%';
        mysql> show grants for 'grey_ggcc_user'@'%';

        mysql> show grants for 'greyrdsadmin'@'%';
        +-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | Grants for greyrdsadmin@%                                                                                                                                                                                                                                                                                                                                                                                 |
        +-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, RELOAD, PROCESS, REFERENCES, INDEX, ALTER, SHOW DATABASES, CREATE TEMPORARY TABLES, LOCK TABLES, EXECUTE, REPLICATION SLAVE, REPLICATION CLIENT, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, CREATE USER, EVENT, TRIGGER ON *.* TO 'greyrdsadmin'@'%' IDENTIFIED BY PASSWORD '*A585F04D9672D0A452EACF9A19845977F7B69AD3' WITH GRANT OPTION |
        +-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        1 row in set (0.01 sec)

        mysql> show grants for 'grey_ggcc_user'@'%';
        +---------------------------------------------------------------------------------------------------------------+
        | Grants for grey_ggcc_user@%                                                                                   |
        +---------------------------------------------------------------------------------------------------------------+
        | GRANT USAGE ON *.* TO 'grey_ggcc_user'@'%' IDENTIFIED BY PASSWORD '*0A52185901D9594418AFD3E33EF316C384DDCAF2' |
        | GRANT ALL PRIVILEGES ON `ggcc_prd`.* TO 'grey_ggcc_user'@'%' WITH GRANT OPTION                                |
        +---------------------------------------------------------------------------------------------------------------+
        2 rows in set (0.00 sec)

        [ebarrirero@jumphost ~]$ df -h
        Filesystem      Size  Used Avail Use% Mounted on
        /dev/xvdi        99G   89G  4,7G  96% /ops/backups
        [ebarrirero@jumphost ~]$ cd /ops/backups/

        [ebarrirero@jumphost backups]$ ls -ltr
        total 49104192
        -rw-r--r--  1 jenkins jenkins 16255091287 ago 25 16:54 greycom-prd-2016-08-25.tar.gz
        -rw-r--r--  1 jenkins jenkins 16263377824 ago 30 18:07 greycom-prd-2016-08-30.tar.gz
        -rw-r--r--  1 jenkins jenkins 16275778219 sep  1 19:23 greycom-prd-2016-09-01.tar.gz

        [ebarrirero@jumphost backups]$ sudo rm -rf greycom-prd-2016-08-25.tar.gz
        [ebarrirero@jumphost backups]$ sudo rm -rf greycom-prd-2016-08-30.tar.gz

        [ebarrirero@jumphost backups]$ df -h
        /dev/xvdi        99G   59G   35G  63% /ops/backups


        DATE=`date +%Y-%m-%d`
        mysqldump -q -c --routines --triggers --single-transaction -h ggcc-prd.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p ggcc_prd > /ops/backups/ggcc_prd-$DATE.sql
        #check that the backup was created with a grep.

        #mysql --defaults-file=scripts/conf/connect-stg/connect-stg-my.cnf -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -e "CREATE DATABASE grey_stg_v2"
        #mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "DROP DATABASE grey_stg_v2"
        mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "CREATE DATABASE ggcc_stg_v2"
        mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "show databases;"
        Enter password:
        +--------------------+
        | Database           |
        +--------------------+
        | information_schema |
        | ggcc_stg           |
        | ggcc_stg_v1        |
        | ggcc_stg_v2        |
        | innodb             |
        | mysql              |
        | performance_schema |
        | tmp                |
        +--------------------+

        DATE=`date +%Y-%m-%d`
        mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p ggcc_stg_v2 < /ops/backups/ggcc_prd-$DATE.sql

        THEN IN STG
        If User not created:
        mysql> CREATE USER 'grey_ggcc_user'@'%' IDENTIFIED BY 'grey_ggcc_user';
        Query OK, 0 rows affected (0.01 sec)

        #To grant permisions for a certain user for one DB (* represents the tables)
        #mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "grant all privileges on ggcc_stg_v2.* to 'grey_ggcc_user'@'%' WITH GRANT OPTION;"
        #mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "grant all privileges on ggcc_stg_v2.* to 'grey_ggcc_user'@'%';"

        #To grant permisions for a certain user for a specific DB (for Connect)
        mysql -h ggcc-stg.cqrpklcv3mzd.us-east-1.rds.amazonaws.com -u greyrdsadmin -p -e "grant all on `ggcc_stg_v2`.* to 'ggcc_stg_user'@'%';"

        #Remove the dump
"""

"""
def sp_local(sp_dir):
    with settings(warn_only=False):
        if exists(sp_dir, use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir, 'white', attrs=['bold'])
            with cd(sp_dir):
                try:
                    print colored('#####################################################', 'blue')
                    print colored('####### COMPILE Stream Partitioner w/ MAVEN #########', 'blue')
                    print colored('#####################################################', 'blue')
                    run('mvn install -Dmaven.test.skip=true')
                except:
                    print colored('#############################################################', 'red')
                    print colored('####### FAIL to COMPILE Stream Partitioner w/ MAVEN #########', 'red')
                    print colored('#############################################################', 'red')
        else:
            print colored('###########################################################', 'red')
            print colored('##### Directory /Stream-Partitioner/ does not exists ######', 'red')
            print colored('###########################################################', 'red')

        if exists(sp_dir+'yarara-test/yarara-ace-test/project/', use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir+'yarara-test/yarara-ace-test/project/', 'white', attrs=['bold'])
            with cd(sp_dir+'yarara-test/yarara-ace-test/project/'):
                try:
                    print colored('##################################################', 'blue')
                    print colored('####### RUN Stream Partitioner java -jar #########', 'blue')
                    print colored('##################################################', 'blue')
                    run('cp '+sp_dir+'target/StreamPartitioner-0.0.1-SNAPSHOT.jar SP.jar')
                    run('java -jar SP.jar')
                except:
                    print colored('#########################################################', 'red')
                    print colored('####### FAIL to RUN Stream Partitioner java -jar ########', 'red')
                    print colored('#########################################################', 'red')
        else:
            print colored('################################################', 'red')
            print colored('##### Directory /project/ does not exists ######', 'red')
            print colored('################################################', 'red')

        if exists(sp_dir+'yarara-test/yarara-ace-test/', use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir+'yarara-test/yarara-ace-test/', 'white', attrs=['bold'])
            with cd(sp_dir+'yarara-test/yarara-ace-test/'):
                try:
                    print colored('########################################', 'blue')
                    print colored('####### Creating SP virtual env ########', 'blue')
                    print colored('########################################', 'blue')
                    if exists('create_virtualenv.sh', use_sudo=True):
                        run('chmod +x create_virtualenv.sh')
                        run('./create_virtualenv.sh --http_proxy http://proxy-us.intel.com:911')
                    else:
                        print colored('#############################################', 'red')
                        print colored('#### create_virtualenv.sh does not exist ####', 'red')
                        print colored('#############################################', 'red')

                except:
                    print colored('############################################', 'red')
                    print colored('####### FAIL to Create_virtual env #########', 'red')
                    print colored('############################################', 'red')
        else:
            print colored('############################################################', 'red')
            print colored('##### Dir /yarara-ace-test/ doesnt exists ######', 'red')
            print colored('############################################################', 'red')

        if exists(sp_dir+'yarara-test/yarara-ace-test/', use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir+'yarara-test/yarara-ace-test/', 'white', attrs=['bold'])
            with cd(sp_dir+'yarara-test/yarara-ace-test/'):
                try:
                    if exists('./testFiles', use_sudo=True):
                        print colored('#############################################', 'yellow')
                        print colored('####### testFiles Dir already exists ########', 'yellow')
                        print colored('#############################################', 'yellow')
                    else:
                        print colored('#######################################', 'blue')
                        print colored('####### Creating testFiles Dir ########', 'blue')
                        print colored('#######################################', 'blue')
                        run('mkdir testFiles')

                except:
                    print colored('#############################################', 'red')
                    print colored('####### FAIL to create Dir testFiles ########', 'red')
                    print colored('#############################################', 'red')
        else:
            print colored('############################################################', 'blue')
            print colored('##### Dir /yarara-test-ace/ doesnt exists ######', 'blue')
            print colored('############################################################', 'blue')

        if exists(sp_dir, use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir, 'white', attrs=['bold'])
            with cd(sp_dir):
                try:
                    print colored('########################################################', 'blue')
                    print colored('####### Replacing applications.properties file #########', 'blue')
                    print colored('########################################################', 'blue')
                    run('cp -r -f '+sp_dir+'config/application.properties ./yarara-test/yarara-ace-test/project/config')
                    run('cp -r -f '+sp_dir+'config/application.properties ./yarara-test/yarara-ace-test/config')
                except:
                    print colored('##############################################################', 'red')
                    print colored('####### FAIL to Replace applications.properties file #########', 'red')
                    print colored('##############################################################', 'red')
        else:
            print colored('#########################################################', 'red')
            print colored('#### Directory /Stream-Partitioner/ does not exists #####', 'red')
            print colored('#########################################################', 'red')

        if exists(sp_dir+'yarara-test/yarara-ace-test/', use_sudo=True):
            print colored('##############################', 'blue')
            print colored('##### Directory Tree OK ######', 'blue')
            print colored('##############################', 'blue')
            print colored(sp_dir+'yarara-test/yarara-ace-test/', 'white', attrs=['bold'])
            with cd(sp_dir+'yarara-test/yarara-ace-test/'):
                try:
                    print colored('###############################################', 'blue')
                    print colored('####### Running Yarara component tests ########', 'blue')
                    print colored('###############################################', 'blue')
                    run('chmod +x run_scenarios.sh')
                    run('./run_scenarios.sh -t @COMPONENT --no_proxy NO_PROXY --logging-level DEBUG')

                except:
                    print colored('####################################################', 'red')
                    print colored('####### FAIL to Run Yarara component tests #########', 'red')
                    print colored('####################################################', 'red')
        else:
            print colored('################################################', 'red')
            print colored('##### Dir /yarara-ace-test/ doesnt exists ######', 'red')
            print colored('################################################', 'red')
"""

"""
def push_key(usernamep):
    with settings(warn_only=False):
        #usernamep = prompt("Which USERNAME you like to CREATE & PUSH KEYS?")
        #user_exists = sudo('cat /etc/passwd | grep '+usernamep)
        #user_exists =sudo('grep "^'+usernamep+':" /etc/passwd')
        ##user_exists = sudo('cut -d: -f1 /etc/passwd | grep ' + usernamep)
        #print colored(user_exists, 'green')
        #print(env.host_string)
        #sudo('uname -a')

        try:
        ##if(user_exists != ""):
            user_exists = sudo('cut -d: -f1 /etc/passwd | grep '+usernamep)
            if (user_exists != ""):
                print colored('##############################', 'green')
                print colored('"' + usernamep + '" already exists', 'green')
                print colored('PUSHING KEYS', 'green')
                print colored('##############################', 'green')
                local('sudo chmod 701 /home/' + usernamep)
                local('sudo chmod 741 /home/' + usernamep + '/.ssh')
                local('sudo chmod 604 /home/' + usernamep + '/.ssh/id_rsa')
                local('sudo chmod 604 /home/' + usernamep + '/.ssh/id_rsa.pub')

                local('ssh-copy-id -i /home/' + usernamep + '/.ssh/id_rsa.pub ' + usernamep + '@' + env.host_string)
                sudo('chmod 700 /home/' + usernamep + '/.ssh/authorized_keys')
                sudo('gpasswd -a ' + usernamep + ' wheel')

                local('sudo chmod 700 /home/' + usernamep)
                local('sudo chmod 700 /home/' + usernamep + '/.ssh')
                local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa')
                local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa.pub')
            else:
                print colored('#################################', 'green')
                print colored('"' + usernamep + '" doesnt exists', 'green')
                print colored('PUSHING KEYS', 'green')
                print colored('##################################', 'green')
                local('sudo chmod 701 /home/' + usernamep)
                local('sudo chmod 741 /home/' + usernamep + '/.ssh')
                local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa')
                local('sudo chmod 604 /home/' + usernamep + '/.ssh/id_rsa.pub')

                sudo('useradd ' + usernamep + ' -m -d /home/' + usernamep)
                sudo('echo "' + usernamep + ':' + usernamep + '" | chpasswd')

                # Remember that the usernamep is not in the remote server
                # Then you are gona be ask the pass of this user.
                # To avoid this you must use a user that it's already created
                # in the local and remote host with the proper permissions.
                local('ssh-copy-id -i /home/' + usernamep + '/.ssh/id_rsa.pub ' + usernamep + '@' + env.host_string)
                sudo('chmod 700 /home/' + usernamep + '/.ssh/authorized_keys')
                sudo('gpasswd -a ' + usernamep + ' wheel')

                local('sudo chmod 700 /home/' + usernamep)
                local('sudo chmod 700 /home/' + usernamep + '/.ssh')
                local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa')
                local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa.pub')
        except:
        ##else:
            print colored('#################################', 'green')
            print colored('"' + usernamep + '" doesnt exists', 'green')
            print colored('PUSHING KEYS', 'green')
            print colored('##################################', 'green')
            local('sudo chmod 701 /home/' + usernamep)
            local('sudo chmod 741 /home/' + usernamep + '/.ssh')
            local('sudo chmod 604 /home/' + usernamep + '/.ssh/id_rsa')
            local('sudo chmod 604 /home/' + usernamep + '/.ssh/id_rsa.pub')
            sudo('useradd ' + usernamep + ' -m -d /home/' + usernamep)
            sudo('echo "'+usernamep+':'+usernamep+'" | chpasswd')
            # Remember that the usernamep is not in the remote server
            # Then you are gona be ask the pass of this user.
            # To avoid this you must use a user that it's already created
            # in the local and remote host with the proper permissions.
            local('ssh-copy-id -i /home/'+usernamep+'/.ssh/id_rsa.pub '+usernamep+'@'+env.host_string)
            sudo('chmod 700 /home/'+usernamep+'/.ssh/authorized_keys')
            sudo('gpasswd -a ' + usernamep + ' wheel')
            local('sudo chmod 700 /home/' + usernamep)
            local('sudo chmod 700 /home/' + usernamep + '/.ssh')
            local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa')
            local('sudo chmod 600 /home/' + usernamep + '/.ssh/id_rsa.pub')
"""