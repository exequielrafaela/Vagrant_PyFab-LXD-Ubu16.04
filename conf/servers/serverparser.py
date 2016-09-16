import ConfigParser

# Definition of directories and files
CONFIG_DIR = "./conf/"
LOGS_DIR = "./logs/"

SERVERS_FILE_PATH = CONFIG_DIR + "servers.conf"

def LoadServers(self):
    """
    Load configurations from file servers.conf
    """
    config = ConfigParser.ConfigParser()
    try:
        Temp = config.read(SERVERS_FILE_PATH)
    except:
        logger.critical("The configuration file servers.conf cannot be read.")
        sys.exit(1)

    if Temp == []:
        logger.critical("The configuration file servers.conf cannot be read.")
        sys.exit(1)
    else:
        try:
            if len(config.sections()) == 0:
                logger.critical("At least one server must be defined in servers.conf.")
                sys.exit(1)

            for item in config.sections():

                Temp2 = config.get(item, "exten")
                Temp2 = Temp2.split(",")

                exten_list = []
                for x in range(len(Temp2)):
                    for j in range(len(self.Extensions)):
                        if Temp2[x] == self.Extensions[j].Extension:
                            exten_list.append(self.Extensions[j])
                            break

                self.Servers.append(Server(self.behaviour_mode,
                                           item,
                                           self.Active_mode,
                                           self.Passive_mode,
                                           self.Aggressive_mode,
                                           config.get(item, "registrar_ip"),
                                           config.get(item, "registrar_port"),
                                           int(config.get(item, "registrar_time")),
                                           int(config.get(item, "nat_keepalive_interval")),
                                           exten_list,
                                           self.lib,
                                           self.Sound_enabled,
                                           self.Playfile))

        except Exception, e:
            print str(e)
            logger.critical(
                "The configuration file servers.conf cannot be correctly read. Check it out carefully. More info: " + str(
                    e))
            sys.exit(1)

    del config


def LoadConfiguration(self):
    """
    Load configurations from file artemisa.conf
    """
    config = ConfigParser.ConfigParser()
    try:
        Temp = config.read(CONFIG_FILE_PATH)
    except:
        logger.critical("The configuration file artemisa.conf cannot be read.")
        sys.exit(1)

    if Temp == []:
        logger.critical("The configuration file artemisa.conf cannot be read.")
        sys.exit(1)
    else:

        try:

            # Gets the parameters of the behaviour modes
            self.Active_mode = GetConfigSection(BEHAVIOUR_FILE_PATH, "active")
            self.Passive_mode = GetConfigSection(BEHAVIOUR_FILE_PATH, "passive")
            self.Aggressive_mode = GetConfigSection(BEHAVIOUR_FILE_PATH, "aggressive")
            self.Investigate_sec = GetConfigSection(BEHAVIOUR_FILE_PATH, "investigate")

            # Now checks if the items read are known
            for item in self.Active_mode:
                if (item != "send_180") and (item != "send_200"):
                    self.Active_mode.remove(item)

            for item in self.Passive_mode:
                if (item != "send_180") and (item != "send_200"):
                    self.Passive_mode.remove(item)

            for item in self.Aggressive_mode:
                if (item != "send_180") and (item != "send_200"):
                    self.Aggressive_mode.remove(item)

            self.Local_IP = config.get("environment", "local_ip")

            # Now check if the given IP is a valid IP (valid format)
            try:
                IP(self.Local_IP)
            except:
                logger.critical(
                    "The IP address configured in local_ip in file artemisa.conf is not valid (IP address: " + self.Local_IP + ").")
                sys.exit(1)

            self.Local_port = config.get("environment", "local_port")

            try:
                int(self.Local_port)
            except:
                logger.error("local_port in configuration file must be an integer. Set to 5060.")
                self.Local_port = "5060"

            self.Local_xml_port = config.get("environment", "local_xml_port")

            try:
                int(self.Local_xml_port)
            except:
                logger.error("local_xml_port in configuration file must be an integer. Set to 8000.")
                self.Local_xml_port = "8000"

            self.SIPdomain = config.get("environment", "sip_domain")
            self.UserAgent = config.get("environment", "user_agent")
            self.behaviour_mode = config.get("environment", "behaviour_mode")
            try:
                self.MaxCalls = int(config.get("environment", "max_calls"))
            except:
                logger.error("max_calls in configuration file must be an integer. Set to 1.")
                self.MaxCalls = 1
            self.Playfile = config.get("environment", "playfile")

            self.Sound_enabled = config.get("sound", "enabled")

            try:
                self.Sound_device = int(config.get("sound", "device"))
            except:
                logger.error("device in configuration file must be an integer. Set to 0.")
                self.Sound_device = 0

            try:
                self.Sound_rate = int(config.get("sound", "rate"))
            except:
                logger.error("rate in configuration file must be an integer. Set to 44100.")
                self.Sound_rate = 44100

            if self.behaviour_mode != "active" and self.behaviour_mode != "passive" and self.behaviour_mode != "aggressive":
                self.behaviour_mode = "passive"
                logger.info("behaviour_mode value is invalid. Changed to passive.")

        except Exception, e:
            logger.critical(
                "The configuration file artemisa.conf cannot be correctly read. Check it out carefully. Details: " + str(
                    e))
            sys.exit(1)

    del config

    # Now it reads the actions.conf file to load the user-defined parameters to sent when calling the scripts
    config = ConfigParser.ConfigParser()
    try:
        Temp = config.read(ACTIONS_FILE_PATH)
    except:
        logger.critical("The configuration file actions.conf cannot be read.")
        sys.exit(1)

    if Temp == []:
        logger.critical("The configuration file actions.conf cannot be read.")
        sys.exit(1)
    else:
        try:
            # Gets the parameters for the on_flood.sh
            self.On_flood_parameters = config.get("actions", "on_flood")
            self.On_SPIT_parameters = config.get("actions", "on_spit")
            self.On_scanning_parameters = config.get("actions", "on_scanning")

        except:
            logger.critical("The configuration file actions.conf cannot be correctly read. Check it out carefully.")
            sys.exit(1)

    del config


def XmlServer(self):
    """
    Creation of the XML Server
    """
    global xml_serv
    xml_serv = SimpleXMLRPCServer((self.Local_IP, int(self.Local_xml_port)), requestHandler=RequestHandler)
    ### Function to allow Clients (XML-RPC connections) to access XML-RPC service methos - API Interface
    xml_serv.register_introspection_functions()

    print ''  # necessary to correct the console for a better output visualization
    # logger.info('XML-RPC service running...')

    xml_serv.register_function(self.ModifyExt, 'modify_extension')

    def RestartArtemisa():
        f = open('/dev/stdin', 'w')
        f.write('restart\n')
        # self.ArtemisaRestart()

    xml_serv.register_function(RestartArtemisa, 'restart')

    #### Run the XML-RPC_service main loop
    xml_serv.serve_forever()


def ModifyExt(self, mod, ext, user, passwd):
    """
    Modify extensions from file extensions.conf
    """

    config = ConfigParser.ConfigParser()
    config.read(EXTENSIONS_FILE_PATH)

    config1 = ConfigParser.ConfigParser()
    config1.read(SERVERS_FILE_PATH)

    ext_aux = []

    # se usara la instancia configServer de la clase ConfigParser para
    # escribir en server.conf
    # configServer = ConfigParser.ConfigParser()
    # configServer.read(EXTENSIONS_FILE_PATH)

    if mod == 'add':
        if config.has_section(ext):
            logger.info('Extension ' + ext + ' already exists in extensions.conf')
            return 'Extension ' + ext + ' already exists'

        elif len(config.sections()) <= 7:

            config.add_section(ext)
            config.set(ext, 'username', '"' + user + '"')
            config.set(ext, 'password', passwd)

            with open(EXTENSIONS_FILE_PATH, 'wb') as configfile:
                config.write(configfile)

            archi = open(EXTENSIONS_FILE_PATH, 'r')
            lineS = archi.readlines()
            archi.close()

            archi = open(EXTENSIONS_FILE_PATH, 'w')
            archi.write(
                "# Artemisa - Extensions configuration file\n#\n# Be careful when modifying this file!\n\n\n# Here you are able to set up the extensions that shall be used by Artemisa in the registration process. In order to use them, they must be defined in the servers.conf file.\n#\n# The sections name hereunder, such as 3000 in section [3000], refers to a SIP extension and it must be unique in this file, as well as correctly configured in the registrar server.\n\n")
            archi.writelines(lineS)
            archi.close()

            logger.info('Extension ' + ext + ' added in extensions.conf')

            if config1.has_option('myproxy', 'exten'):
                b = False
                ext_aux = config1.get('myproxy', 'exten').split(',')
                for i in ext_aux:
                    if ext == i:
                        logger.info('Extension ' + ext + ' already exists in servers.conf')
                        return 'Extension ' + ext + ' already exists.'

                    aux_str = '%s' % ','.join(map(str, ext_aux))
                    config1.set('myproxy', 'exten', str(aux_str) + ',' + ext)
                    with open(SERVERS_FILE_PATH, 'wb') as configfile:
                        config1.write(configfile)

                    archi = open(SERVERS_FILE_PATH, 'r')
                    lineS = archi.readlines()
                    archi.close()

                    archi = open(SERVERS_FILE_PATH, 'w')
                    archi.write(
                        "# Artemisa - Servers configuration file\n#\n# Be careful when modifying this file!\n\n\n# Here you are able to set the registrar servers configuration that Artemisa shall use to register itself.\n#\n# registrar_time=\n# Is the time in minutes between automatic registrations. This is performed in order to avoid\n# being disconnected from the server because of a lack of activity.\n#\n# nat_keepalive_interal=\n# When dealing with NAT proxies, you can set a value in seconds which indicates the time interval between keep alive messages. If zero is written, then the NAT keep alive messages shall not be sent.\n#\n# exten=\n# In this field you should set the extensions to be used. They must be declared in extensions.conf.\n\n")
                    archi.writelines(lineS)
                    archi.close()

                    logger.info('Extension ' + ext + ' added in servers.conf')
                    return 'Extension ' + ext + ' added'

        else:
            logger.info(
                'Max number of extensions registered. Run another artemisa instance to register more extensions.')
            return 'Max number of extensions registered. Run another artemisa instance to register more extensions.'
    elif mod == 'delete':
        if config.has_section(ext):
            config.remove_section(ext)
            with open(EXTENSIONS_FILE_PATH, 'wb') as configfile:
                config.write(configfile)

            archi = open(EXTENSIONS_FILE_PATH, 'r')
            lineS = archi.readlines()
            archi.close()

            archi = open(EXTENSIONS_FILE_PATH, 'w')
            archi.write(
                "# Artemisa - Extensions configuration file\n#\n# Be careful when modifying this file!\n\n\n# Here you are able to set up the extensions that shall be used by Artemisa in the registration process. In order to use them, they must be defined in the servers.conf file.\n#\n# The sections name hereunder, such as 3000 in section [3000], refers to a SIP extension and it must be unique in this file, as well as correctly configured in the registrar server.\n\n")
            archi.writelines(lineS)
            archi.close()

            logger.info('Extension ' + ext + ' deleted in extensions.conf')

        else:

            logger.info('Extension ' + ext + ' does not exists in extensions.conf')

        if config1.has_option('myproxy', 'exten'):
            b = False
            ext_aux = config1.get('myproxy', 'exten').split(',')

            # len_list_aux = len(ext_aux)
            j = 0
            while j < len(ext_aux):
                if ext == ext_aux[j]:
                    del (ext_aux[j])
                    # len_list_aux = len(ext_aux)
                    b = True
                else:
                    j = j + 1

            aux_str = '%s' % ','.join(map(str, ext_aux))
            config1.set('myproxy', 'exten', aux_str)
            with open(SERVERS_FILE_PATH, 'wb') as configfile:
                config1.write(configfile)

            if not b:
                archi = open(SERVERS_FILE_PATH, 'r')
                lineS = archi.readlines()
                archi.close()

                archi = open(SERVERS_FILE_PATH, 'w')
                archi.write(
                    "# Artemisa - Extensions configuration file\n#\n# Be careful when modifying this file!\n\n\n# Here you are able to set up the extensions that shall be used by Artemisa in the registration process. In order to use them, they must be defined in the servers.conf file.\n#\n# The sections name hereunder, such as 3000 in section [3000], refers to a SIP extension and it must be unique in this file, as well as correctly configured in the registrar server.\n\n")
                archi.writelines(lineS)
                archi.close()

                logger.info('Extension ' + ext + ' does not exists in servers.conf')
                return 'Extension ' + ext + ' does not exists'

            archi = open(SERVERS_FILE_PATH, 'r')
            lineS = archi.readlines()
            archi.close()

            archi = open(SERVERS_FILE_PATH, 'w')
            archi.write(
                "# Artemisa - Servers configuration file\n#\n# Be careful when modifying this file!\n\n\n# Here you are able to set the registrar servers configuration that Artemisa shall use to register itself.\n#\n# registrar_time=\n# Is the time in minutes between automatic registrations. This is performed in order to avoid\n# being disconnected from the server because of a lack of activity.\n#\n# nat_keepalive_interal=\n# When dealing with NAT proxies, you can set a value in seconds which indicates the time interval between keep alive messages. If zero is written, then the NAT keep alive messages shall not be sent.\n#\n# exten=\n# In this field you should set the extensions to be used. They must be declared in extensions.conf.\n\n")
            archi.writelines(lineS)
            archi.close()

            logger.info('Extension ' + ext + ' deleted in servers.conf')
            return 'extension ' + ext + ' deleted'

        else:
            logger.info('Extension ' + ext + ' does not exists.')

    else:
        logger.info('wrong request please try with "add" or "delete"')
        return 'wrong request please try with "add" or "delete"'

    del config