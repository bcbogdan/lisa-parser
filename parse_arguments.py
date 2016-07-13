import getopt


def parse_arguments(arg_list):
    xml_file = ''
    log_file = ''

    try:
        opts, args = getopt.getopt(arg_list,
                                   "hx:l:", ["xmlfile=", "logfile="])
    except getopt.GetoptError:
        print('sql_persist.py -x <XmlFile> -l <LogFile>')
        return False

    for opt, arg in opts:
        if opt == '-h':
            print('sql_persist.py -x <XmlFile> -l <LogFile>')
            return False
        elif opt in ("-x", "--xmlfile"):
            xml_file = arg
        elif opt in ("-l", "--logfile"):
            log_file = arg

    return xml_file, log_file
