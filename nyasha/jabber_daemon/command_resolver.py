# -*- coding: utf-8 -*-
from core import cmd_patterns, cmd

command_patterns = cmd_patterns('jabber_daemon.commands',
        cmd(r'^HELP$', 'help_command', doc='HELP - show this help'),
        cmd(r'^PING$', 'ping_command', doc='PING - pong'),

        cmd(r'^NICK$', 'nick_command', doc='NICK - show nick'),
        cmd(r'^NICK\s+(?P<new_nick>[\w]+)$', 'nick_command', doc='NICK <new username> - set new username'),
        #
        cmd(r'^#(?P<post_pk>\d+)$', 'show_message_command', doc='#1234 - Show message'),
        cmd(r'^#(?P<post_pk>\d+)/(?P<comment_number>\d+)$', 'show_message_command', doc='#1234/1 - Show reply'),
        cmd(r'^#(?P<post_pk>\d+)\+$', 'show_message_command',
            extra_kwargs={'show_comments':True}, doc='#1234+ - Show message with replies'),
        cmd(r'^#(?P<post_pk>\d+)[\s]+[\*](?P<tag>[\S]+)$', 'add_tag_command', doc='#1234 *tag - add or remove tag on message'),
        #
        cmd(r'^#(?P<post_pk>\d+)\s+(?P<message>.*)$', 'comment_add_command',
            doc='#1234 Blah-blah-blah - Answer to message #1234'),
        cmd(r'^#(?P<post_pk>\d+)/(?P<comment_number>\d+)\s+(?P<message>.*)$', 'comment_add_command',
            doc='#1234/5 Blah - Answer to reply #1234/5'),
        #
        cmd(r'^\![\s]+#(?P<post_pk>[\d]+)$', 'recommend_post_command', doc='! #1234 - Recommend post'),

        # delete
        cmd(r'^D[\s]+#(?P<post_pk>\d+)$', 'delete_command' ,doc='D #123 - Delete message'),
        cmd(r'^D[\s]+#(?P<post_pk>\d+)/(?P<comment_number>\d+)$', 'delete_command', doc='D #123/1 - Delete reply'),
        cmd(r'^D[\s]+L$', 'delete_command', doc='D L - Delete last message', extra_kwargs={'last':True}),
        #
        cmd( r'^S$', 'subscribe_show_command', doc='S - Show your subscriptions'),
        #S
        cmd(r'^S[\s]+#(?P<post_pk>\d+)$' ,'subscribe_toggle_command', doc='S #123 - Subscribe to message replies'),
        cmd(r'^S[\s]+@(?P<username>[\w]+)$','subscribe_toggle_command', doc='S @username - Subscribe to user\'s blog'),
        cmd(r'^U[\s]+#(?P<post_pk>\d+)$', 'subscribe_toggle_command', extra_kwargs={'delete':True},
            doc='U #123 - Unsubscribe from comments'),
        cmd(r'^U[\s]+@(?P<username>[\w]+)$' ,'subscribe_toggle_command', extra_kwargs={'delete':True},
            doc='U @username - Unsubscribe from user\'s blog'),
        cmd(r'^\*$', 'show_tags_command', doc='* - Show your tags'),
        cmd(r'^#\+$', 'last_messages', doc='#+ - Show last messages from public timeline'),
        cmd(r'^(?P<numpage>#+)$', 'user_feed_messages', doc='# - Show last messages from your feed (## - second page, ...)'),
        cmd(r'^\*(?P<tag>[\S]+)$', 'last_messages_by_tag', doc='*tag - Show last messages by tag'),
        cmd(r'^@(?P<username>[\w]+)\+$', 'last_messages_by_user', doc='@username+ - Show user\'s info and last 10 messages'),
        cmd(r'^@(?P<username>[\w]+) \*(?P<tag>[\S]+)$', 'last_messages_by_user', doc='@username *tag - User\'s messages with this tag'),
        cmd(r'^@(?P<username>[\w]+)$', 'user_info', doc='@username - User info'),

        #        cmd(r'^VCARD$', 'vcard_command', doc='VCARD - Update "About" info from Jabber vCard'),
        cmd(r'^LOGIN$', 'login_command', doc='LOGIN - login in web ui'),

        cmd(r'^OFF$', 'off_on_command', doc='OFF - Disable subscriptions delivery'),
        cmd(r'^ON$', 'off_on_command', doc='ON - Enable subscriptions delivery', extra_kwargs={'off':False}),

)



