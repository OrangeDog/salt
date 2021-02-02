"""
Grain that indicates the system is pending a reboot
See functions in salt.utils.win_system to see what conditions would indicate
a reboot is pending
"""
import logging

import salt.modules.cmdmod
import salt.modules.kernelpkg_linux_apt
import salt.modules.kernelpkg_linux_yum
import salt.utils.path
import salt.utils.platform
import salt.utils.win_system

log = logging.getLogger(__name__)

__salt__ = {"cmd.retcode": salt.modules.cmdmod._retcode_quiet}
__virtualname__ = "pending_reboot"

APT_BIN = salt.utils.path.which("apt-get")
CHECKRESTART_BIN = salt.utils.path.which("checkrestart")
NEEDS_RESTART_BIN = salt.utils.path.which("needs-restarting")
YUM_BIN = salt.utils.path.which_bin(["yum", "dnf"])

if APT_BIN:
    __salt__["kernelpkg.needs_reboot"] = salt.modules.kernelpkg_linux_apt.needs_reboot
elif YUM_BIN:
    __salt__["kernelpkg.needs_reboot"] = salt.modules.kernelpkg_linux_yum.needs_reboot


def __virtual__():
    if not salt.utils.platform.is_linux() and not salt.utils.platform.is_windows():
        return False, "'pending_reboot' grain not available on this platform"

    return __virtualname__


def pending_reboot():
    """
    A grain that indicates that a Windows system is pending a reboot.
    """
    if salt.utils.platform.is_windows():
        return {"pending_reboot": salt.utils.win_system.get_pending_reboot()}

    # TODO: pkg.services_need_restarting (#58262)
    #  these checks are separate to kernel updates
    if CHECKRESTART_BIN is not None:
        if 1 == __salt__["cmd.retcode"](CHECKRESTART_BIN + " -t"):
            return {"pending_reboot": True}
    elif NEEDS_RESTART_BIN is not None:
        if 1 == __salt__["cmd.retcode"](NEEDS_RESTART_BIN):
            return {"pending_reboot": True}

    if "kernelpkg.needs_reboot" in __salt__:
        return {"pending_reboot": __salt__["kernelpkg.needs_reboot"]()}
    else:
        # Unknown
        return {}
