# -*- coding: utf-8 -*-
from core import cmd_patterns, cmd

command_patterns = cmd_patterns('jabber_daemon.commands',
        cmd(r'^HELP$', 'help_command', doc='HELP - show this help'),
        cmd(r'^PING$', 'ping_command', doc='PING - pong'),

        cmd(r'^NICK$', 'nick_command', doc='NICK - show nick'),
        cmd(r'^NICK\s+(?P<new_nick>[\w]+)$', 'nick_command', doc='NICK <new username> - set new username'),
        #
        cmd(r'^#(?P<post_pk>\d+)$', 'show_message_command', doc='#1234 - Show message'),
        cmd(r'^#(?P<post_pk>\d+)/(?P<comment_number>\d+)$', 'show_message_command', doc='#1234\\1 - Show reply'),
        cmd(r'^#(?P<post_pk>\d+)\+$', 'show_message_command',
            extra_kwargs={'show_comments':True}, doc='#1234+ - Show message with replies'),
        #
        cmd(r'^#(?P<post_pk>\d+)\s+(?P<message>.*)$', 'comment_add_command',
            doc='#1234 Blah-blah-blah - Answer to message #1234'),
        cmd(r'^#(?P<post_pk>\d+)/(?P<comment_number>\d+)\s+(?P<message>.*)$', 'comment_add_command',
            doc='#1234/5 Blah - Answer to reply #1234/5'),

)



