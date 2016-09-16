VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "boxcutter/ubuntu1604"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end

  # Assign this VM to a host-only network IP, allowing you to access it
  # via the IP. Host-only networks can talk to the host machine as well as
  # any other machines on the same network, but cannot be accessed (through this
  # network interface) by any external networks.
  config.vm.network "private_network", ip: "192.168.33.33"

  # Use the vagrant hostmaster plugin to automatically add a domain name
  config.vm.define :server do |lxd|
    lxd.vm.hostname = "lxd"
    lxd.hostmanager.enabled = true
    lxd.hostmanager.manage_host = true
    lxd.vm.network "forwarded_port", guest: 80, host: 8080
    lxd.vm.network "forwarded_port", guest: 8338, host: 8338
    lxd.vm.provision :fabric do |fabric|
      fabric.fabfile_path = "./fabfile.py"
      fabric.tasks = ["lxd", ]
    end
  end
end
