# ansible-slack-notifications


![Slack Screen Capture](screen_capture.png)

## Example config
```
---

- name: Configure webservers
  hosts: web-servers
  vars:
    notify_slack: True
  roles:
    - nginx
  ...
```
