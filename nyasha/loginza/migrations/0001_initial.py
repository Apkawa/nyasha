# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OpenID'
        db.create_table('loginza_openid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uid', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('provider_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('profile_json', self.gf('django.db.models.fields.TextField')()),
            ('datetime_create', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('loginza', ['OpenID'])

        # Adding unique constraint on 'OpenID', fields ['provider', 'uid']
        db.create_unique('loginza_openid', ['provider', 'uid'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'OpenID', fields ['provider', 'uid']
        db.delete_unique('loginza_openid', ['provider', 'uid'])

        # Deleting model 'OpenID'
        db.delete_table('loginza_openid')


    models = {
        'loginza.openid': {
            'Meta': {'unique_together': "(('provider', 'uid'),)", 'object_name': 'OpenID'},
            'datetime_create': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile_json': ('django.db.models.fields.TextField', [], {}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'provider_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        }
    }

    complete_apps = ['loginza']
