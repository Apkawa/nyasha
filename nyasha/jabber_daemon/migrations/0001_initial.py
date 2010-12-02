# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SendQueue'
        db.create_table('jabber_daemon_sendqueue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_jid', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('to_jid', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('datetime_create', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_send', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('is_send', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_raw', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('jabber_daemon', ['SendQueue'])


    def backwards(self, orm):
        
        # Deleting model 'SendQueue'
        db.delete_table('jabber_daemon_sendqueue')


    models = {
        'jabber_daemon.sendqueue': {
            'Meta': {'object_name': 'SendQueue'},
            'datetime_create': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_send': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'from_jid': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_raw': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_send': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'priority': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'to_jid': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['jabber_daemon']
