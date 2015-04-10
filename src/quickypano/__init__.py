import os
import sys
import ctypes

PROCESS_MODE_BACKGROUND_BEGIN = 0x00100000
PROCESS_MODE_BACKGROUND_END = 0x00200000
IDLE_PRIORITY_CLASS = 0x00000040
NORMAL_PRIORITY_CLASS = 0x00000020
PROCESS_SET_INFORMATION = 0x0200


def _win_set_priority_class(priority_class):
    pid = os.getpid()
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, True, pid)
    kernel32.SetPriorityClass(handle, priority_class)


def lowpriority():
    """ Set the priority of the process to below-normal."""

    if sys.platform == 'win32':
        _win_set_priority_class(IDLE_PRIORITY_CLASS)
    else:
        os.nice(1)


def normalpriority():
    if sys.platform == 'win32':
        _win_set_priority_class(NORMAL_PRIORITY_CLASS)
    # Unable to decrease nice level on other systems
