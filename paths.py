import ntpath
import os
import sys

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_config_path():
    if hasattr(sys, "_MEIPASS"):
        abs_home = os.path.abspath(os.path.expanduser("~"))
        abs_dir_app = os.path.join(abs_home, f".my_app_folder")
        if not os.path.exists(abs_dir_app):
            os.mkdir(abs_dir_app)
        cfg_path = os.path.join(abs_dir_app, "data.json")
    else:
        cfg_path = os.path.abspath(".%sdata.json" % os.sep)
    return cfg_path