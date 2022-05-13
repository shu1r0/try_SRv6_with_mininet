# vm name 
$name = "ubuntu-SRv6"

# ------------------------------------------------------------
# Description
# ------------------------------------------------------------
$description = <<'EOS'
# ubuntu for testing SRv6

user: vagrant
password: vagrant
EOS


# ------------------------------------------------------------
# install basic package
# ------------------------------------------------------------
$install_package = <<SCRIPT
sudo apt -y update
sudo apt -y upgrade

sudo apt -y install build-essential
sudo apt -y install sshpass
sudo apt -y install python3
sudo apt -y install python3-pip

python3 -m pip install -U pip

sudo apt -y install libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev
sudo apt -y install git
sudo apt -y install curl
sudo apt -y install wireshark-dev

sudo pip3 install --upgrade pip
sudo pip3 install mininet
SCRIPT


# ------------------------------------------------------------
# install mininet
# ------------------------------------------------------------
$install_mininet = <<SCRIPT
git clone https://github.com/mininet/mininet
cd mininet
# git tag  # list available versions
git checkout -b mininet-2.3.0 2.3.0  # or whatever version you wish to install
cd ..
# mininet/util/install.sh -n3fw
mininet/util/install.sh -a

sudo apt -y install openvswitch-switch
sudo service openvswitch-switch start
SCRIPT

# ------------------------------------------------------------
# install FRR
# ------------------------------------------------------------
$install_frr = <<SCRIPT
curl -s https://deb.frrouting.org/frr/keys.asc | sudo apt-key add -
FRRVER="frr-stable"
echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) $FRRVER | sudo tee -a /etc/apt/sources.list.d/frr.list
sudo apt update -y && sudo apt install -y frr frr-pythontools
SCRIPT

# ------------------------------------------------------------
# install Lubutu Desktop
# ------------------------------------------------------------
$install_lubuntu = <<SCRIPT
sudo apt install -y --no-install-recommends lubuntu-desktop
SCRIPT


# ------------------------------------------------------------
# # vagrant configure version 2
# ------------------------------------------------------------
VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    # vm name
    config.vm.hostname = $name + '.localhost'
    # ubuntu image
    # config.vm.box = 'bento/ubuntu-18.04'
    config.vm.box = 'bento/ubuntu-20.04'
    

    # network
    config.vm.network 'private_network', ip: '10.0.0.100'

    # share directory
    config.vm.synced_folder './', '/home/vagrant/share'

    # install package
    config.vm.provision 'shell', inline: $install_package
    config.vm.provision 'shell', inline: $install_mininet
    config.vm.provision 'shell', inline: $install_frr
    config.vm.provision 'shell', inline: $install_lubuntu

    # config virtual box
    config.vm.provider "virtualbox" do |vb|
        vb.name = $name
        vb.gui = true

        vb.cpus = 1
        vb.memory = "2048"
    
        vb.customize [
            "modifyvm", :id,
            "--vram", "16", 
            "--clipboard", "bidirectional", # clip board
            "--draganddrop", "bidirectional", # drag and drop
            "--ioapic", "off", # enable I/O APIC
            '--graphicscontroller', 'vmsvga',
            "--accelerate3d", "off",
            "--hwvirtex", "on",
            "--nestedpaging", "on",
            "--largepages", "on",
            "--pae", "off",
            '--audio', 'none',
            "--description", $description
        ]
    end
end
