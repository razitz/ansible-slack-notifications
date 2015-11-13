# ansible-slack-notifications


![Slack Screen Capture](screen_capture.gif)

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
