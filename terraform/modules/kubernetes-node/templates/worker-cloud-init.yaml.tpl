${common}

runcmd:
  - /usr/local/bin/install-or-upgrade-rke2.sh
  - systemctl daemon-reload
  - systemctl enable rke2-agent.service
  - systemctl start rke2-agent.service
