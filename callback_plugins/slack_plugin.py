import os
import time
from ansible import utils
from ansible.callbacks import AggregateStats
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

SLACK_INCOMING_WEBHOOK = 'https://hooks.slack.com/services/%s'
TOKEN = 'YOUR_TOKEN'


class CallbackModule(object):
    """
    Send status updates to a Slack channel during playbook execution.
    Only playbooks with the variable `notify_slack` set to true will send slack notifications.
    """

    def __init__(self):
        self.start_time = time.time()
        self.task_report = []
        self.last_task = None
        self.last_task_changed = False
        self.last_task_count = 0
        self.last_task_delta = 0
        self.last_task_start = time.time()
        self.condensed_task_report = False
        self.msg_prefix = ''
        self.playbook_name = None
        self.notify_slack = False

    def _skip_playbook(self):
        return not self.notify_slack

    @staticmethod
    def build_payload_for_slack(text, channel=None, username='Ansible',
                                icon_url='http://www.ansible.com/favicon.ico', icon_emoji=None,
                                link_names=None, parse=None):
        payload = dict(text=text)

        if channel is not None:
            payload['channel'] = channel if (channel[0] == '#') else '#' + channel
        if username is not None:
            payload['username'] = username
        if icon_emoji is not None:
            payload['icon_emoji'] = icon_emoji
        else:
            payload['icon_url'] = icon_url
        if link_names is not None:
            payload['link_names'] = link_names
        if parse is not None:
            payload['parse'] = parse

        payload = "payload=" + utils.jsonify(payload)
        return payload

    def _send_slack(self, text):
        payload = self.build_payload_for_slack(text)
        slack_incoming_webhook = SLACK_INCOMING_WEBHOOK % (TOKEN)

        open_url(slack_incoming_webhook, data=payload)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        if 'msg' in res:
            self._send_slack('{prefix}The ansible run returned the following error:\n\n {error}'.format(
                prefix=self.msg_prefix, error=msg['msg']))

    def runner_on_ok(self, host, res):
        pass

    def runner_on_error(self, host, msg):
        pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        """Display Playbook and play start messages"""
        self.playbook_name, _ = os.path.splitext(os.path.basename(self.play.playbook.filename))
        self.notify_slack = self.play.vars.get('notify_slack', False)
        if self._skip_playbook():
            return

        self.start_time = time.time()
        subset = self.play.playbook.inventory._subset
        msg = "{prefix}Starting ansible run for play *_{play}_*".format(prefix=self.msg_prefix,
                                                                        play=self.playbook_name)
        if self.play.playbook.only_tags and 'all' not in self.play.playbook.only_tags:
            msg = msg + " with tags *_{}_*".format(','.join(self.play.playbook.only_tags))
        if subset:
            msg = msg + " on hosts *_{}_*".format(','.join(subset))
        msg = msg + " by *_{}_*".format(os.environ['USER'])

        self._send_slack(msg)

    def playbook_on_stats(self, stats):
        if self._skip_playbook():
            return

        delta = time.time() - self.start_time
        self.start_time = time.time()
        """Display info about playbook statistics"""
        hosts = sorted(stats.processed.keys())

        summary_all_host_output = []
        for host in hosts:
            if isinstance(stats, AggregateStats):
                stats = stats.summarize(host)
            summary_output = "{prefix}_{host}_ - ".format(prefix=self.msg_prefix, host=host)
            for summary_item in ['ok', 'changed', 'unreachable', 'failures']:
                if stats[summary_item] != 0:
                    summary_output += "[*{}* - {}] ".format(summary_item, stats[summary_item])
            summary_all_host_output.append(summary_output)
        self._send_slack("\n".join(summary_all_host_output))
        msg = "{prefix}Finished Ansible run for *_{play}_* in {min:02} minutes, {sec:02} seconds".format(
            prefix=self.msg_prefix,
            play=self.playbook_name,
            min=int(delta / 60),
            sec=int(delta % 60))

        self._send_slack(msg)
