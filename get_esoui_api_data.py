"""Update ESOUI API."""

import argparse
import logging
import os
import pathlib
import requests

################################################################################
_logger = logging.getLogger(name=__file__)
_LOGGING_FORMAT = '%(asctime)s %(module)s %(lineno)s %(levelname)s:  %(message)s'

_TEMP_DIR = "_temp"

_DEFAULT_URL_ESOUI_API_TXT_DOCUMENTATION = "https://www.esoui.com/forums/attachment.php?attachmentid=1427&d=1635778433"
_DEFAULT_ESOUI_API_TXT_DOCUMENTATION_LIVE_FILE_NAME = "%s/esoui_api_txt_documentation_live.txt" % _TEMP_DIR
_ESOUI_CONSTANTS_LIVE_LUA_FILE = "esoui_contants_live.lua"
_DUMPVARS_CONSTANTS_LUA_FILE = "..\\DumpVars\\DumpVars_constants.lua"
_DUMPVARS_SAVEFILE = "..\\..\\SavedVariables\\DumpVars.lua"


################################################################################
def get_esoui_api_txt_documentation(
        version: str = "LIVE",
        destination: str = _DEFAULT_ESOUI_API_TXT_DOCUMENTATION_LIVE_FILE_NAME) -> None:
    """"""
    _logger.info("Downloading the latest ESOU API txt documentation.")

    r = requests.get(_DEFAULT_URL_ESOUI_API_TXT_DOCUMENTATION)  # create HTTP response object

    with pathlib.Path(str(destination)).open('wb') as f:
        f.write(r.content)


################################################################################
def process_esoui_api_txt_documentation(
        file: str = _DEFAULT_ESOUI_API_TXT_DOCUMENTATION_LIVE_FILE_NAME) -> None:
    """"""
    _logger.info("Processing ESOUI API text doc file: %s" % file)
    if not os.path.exists(file):
        raise Exception("ESOUI API text doc not found: %s" % file)

    with pathlib.Path(str(file)).open('r') as f:
        global_constants_list = []
        while True:
            line = f.readline()
            if "h2. Global Variables" in line:
                break
        while True:
            line = f.readline()
            if "h5. Global" in line:
                continue
            if "h2. Game API" in line:
                break
            if "h5. " in line:
                _, constant_label = line.split("h5. ")
                constant_label = constant_label.replace("\r", "").replace("\n", "")
                #_logger.debug(constant_label)
                index = 0
                these_constants = []
                while True:
                    line = f.readline()
                    if "* " != line[:2]:
                        break
                    _, constant_name = line.split("* ")
                    constant_name = constant_name.replace("\r", "").replace("\n", "")
                    #_logger.debug("  %3d    %s" % (index, constant_name))
                    this_constant = {
                        "constant_name": constant_name,
                        "index": index,
                        "lua_definition_string": ("%s = %d\n" % (constant_name, index)).encode('utf-8'),
                        "constant_label": constant_label}
                    these_constants.append(this_constant)
                    index += 1
                global_constants_list.append(these_constants)

    _logger.info("Writing %s file." % _DUMPVARS_CONSTANTS_LUA_FILE)
    with pathlib.Path(_DUMPVARS_CONSTANTS_LUA_FILE).open('wb') as f:
        f.write(b"if DumpVars == nil then DumpVars = {} end\r\n\r\n")
        f.write(b"        DumpVars.constantsToDump = {\r\n")
        for these_constants in global_constants_list[:-1]:
            for this_constant in these_constants:
                this = "%s" % this_constant["constant_name"]
                f.write(('["%s"] = %s,\r\n' % (this, this)).encode("utf-8"))
        for this_constant in global_constants_list[-1][:-1]:
            this = "%s" % this_constant["constant_name"]
            f.write(('["%s"] = %s,\r\n' % (this, this)).encode("utf-8"))
        this = "%s" % global_constants_list[-1][-1]["constant_name"]
        f.write(('["%s"] = %s\r\n' % (this, this)).encode("utf-8"))
        f.write(b"}\r\n")

    _logger.info("Reading %s file." % _DUMPVARS_SAVEFILE)
    live_constants_from_dumpvars = {}
    with pathlib.Path(_DUMPVARS_SAVEFILE).open('r') as f:
        while True:
            line = f.readline()
            if "                    {" in line:
                break
        while True:
            line = f.readline()
            if "}" in line:
                break
            line = line.replace(" ", "")
            line = line.replace("\r", "")
            line = line.replace("\n", "")
            line = line.replace(",", "")
            label, num = line.split("=")
            label = label.replace("[", "")
            label = label.replace("]", "")
            label = label.replace('"', "")
            live_constants_from_dumpvars["%s" % label] = int(num)

    _logger.info("Writing %s file." % _ESOUI_CONSTANTS_LIVE_LUA_FILE)
    with pathlib.Path(_ESOUI_CONSTANTS_LIVE_LUA_FILE).open('wb') as f:
        for these_constants in global_constants_list:
            f.write(('local %s_STRINGS = {\n' % these_constants[0]["constant_label"].upper()).encode('utf-8'))
            for this_constant in these_constants:
                if this_constant["constant_name"] not in live_constants_from_dumpvars:
                    raise Exception("Constant not found: %s" %str(this_constant["constant_name"]))
                s = '    [%d] = ' % live_constants_from_dumpvars[this_constant["constant_name"]]
                s += '"%s",\n' % this_constant["constant_name"]
                f.write(s.encode("utf-8"))
            f.write('}\n'.encode('utf-8'))
            f.write(("function %s_get_string(value)\n" % this_constant["constant_label"]).encode("utf-8"))
            f.write(("    return %s_STRINGS[value] or tostring(value)\n" % this_constant["constant_label"].upper()).encode("utf-8"))
            f.write('}\n\n'.encode('utf-8'))


################################################################################
def parse_args():
    """"""
    parser = argparse.ArgumentParser(description='Generate %s file.' % "_ESOUI_CONSTANTS_LIVE_LUA_FILE")

    parser.add_argument('-l', '--logging_level', dest='logging_level', metavar='LEVEL',
                        default=logging.DEBUG,
                        help='Python logging level. Default = %s' % str(logging.DEBUG))

    parser.add_argument('-d', '--download_live', dest='download_live', action='store_true',
                        help='Download the latest ESOUI live data.')

    args = parser.parse_args()
    return args


################################################################################
def main():
    args = parse_args()

    logging.basicConfig(level=args.logging_level, format=_LOGGING_FORMAT)

    if not os.path.exists("_temp"):
        os.makedirs("_temp")

    if args.download_live:
        get_esoui_api_txt_documentation()

    process_esoui_api_txt_documentation()

    _logger.info("All done.")


################################################################################
if __name__ == "__main__":
    main()
