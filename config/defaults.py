PRIO_MAP = {
    "0": "EMERGENCY", "1": "ALERT", "2": "CRITICAL", "3": "ERROR",
    "4": "WARNING", "5": "NOTICE", "6": "INFO", "7": "DEBUG"
}

DOMAIN_MAP = {
    "KERNEL": {"kernel"},
    "BOOT": {"systemd", "dracut", "dracut-cmdline", "systemd-modules-load", "systemd-fsck"},
    "NETWORK": {"NetworkManager", "wpa_supplicant", "ModemManager", "avahi-daemon", "chronyd"},
    "AUDIO": {"pipewire", "wireplumber", "alsactl"},
    "SECURITY": {"auditd", "audit", "polkitd", "setroubleshoot", "sudo"},
    "PACKAGE_MGMT": {"dnf", "dnf5", "dnf5daemon-server", "PackageKit", "fwupd"},
    "CRASH_HANDLING": {"abrt-server", "abrtd", "abrt-dump-journal-core", "systemd-coredump"},
    "SCHEDULERS": {"crond", "CROND", "atd", "anacron"},
    "DESKTOP": {"xfce4-terminal", "dolphin", "vlc", "chrome", "brave-browser-stable"},
}
