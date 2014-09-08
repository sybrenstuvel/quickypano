import os
import sys
import ctypes

PROCESS_MODE_BACKGROUND_BEGIN = 0x00100000
PROCESS_MODE_BACKGROUND_END = 0x00200000
PROCESS_SET_INFORMATION = 0x0200

kernel32 = ctypes.windll.kernel32


def _win_set_priority_class(priority_class):
    pid = os.getpid()
    handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, True, pid)
    kernel32.SetPriorityClass(handle, priority_class)


def lowpriority():
    """ Set the priority of the process to below-normal."""

    if sys.platform == 'win32':
        _win_set_priority_class(PROCESS_MODE_BACKGROUND_BEGIN)
    else:
        os.nice(1)


def normalpriority():
    if sys.platform == 'win32':
        _win_set_priority_class(PROCESS_MODE_BACKGROUND_END)
    # Unable to decrease nice level on other systems
