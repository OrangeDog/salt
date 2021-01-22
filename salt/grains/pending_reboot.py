"""
Grain that indicates the system is pending a reboot
See functions in salt.utils.win_system to see what conditions would indicate
a reboot is pending
"""
import logging
import os.path

import salt.modules.cmdmod
import salt.utils.path
import salt.utils.platform
import salt.utils.win_system

log = logging.getLogger(__name__)

__salt__ = {"cmd.retcode": salt.modules.cmdmod._retcode_quiet}
__virtualname__ = "pending_reboot"

CHECKRESTART_BIN = salt.utils.path.which("checkrestart")
NEEDS_RESTART_BIN = salt.utils.path.which("needs-restarting")


def __virtual__():
    if not salt.utils.platform.is_linux() and not salt.utils.platform.is_windows():
        return False, "'pending_reboot' grain not available on this platform"

    return __virtualname__


def pending_reboot(grains):
    """
    A grain that indicates that a Windows system is pending a reboot.
    """
    if salt.utils.platform.is_windows():
        return {"pending_reboot": salt.utils.win_system.get_pending_reboot()}
    elif CHECKRESTART_BIN is not None:
        ret = __salt__["cmd.retcode"](CHECKRESTART_BIN + " -t")
        return {"pending_reboot": ret == 1}
    elif NEEDS_RESTART_BIN is not None:
        ret = __salt__["cmd.retcode"](NEEDS_RESTART_BIN)
        return {"pending_reboot": ret == 1}
    elif grains["os_family"] == "Debian":
        return {"pending_reboot": os.path.isfile("/var/run/reboot-required")}
    else:
        # Could compare running vs. installed kernel version
        return {}
