# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Post.is_deleted'
        db.add_column('blog_post', 'is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding unique constraint on 'Post', fields ['id', 'user']
        db.create_unique('blog_post', ['id', 'user_id'])

        # Adding field 'Comment.user'
        db.add_column('blog_comment', 'user', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['auth.User']), keep_default=False)

        # Adding field 'Comment.number'
        db.add_column('blog_comment', 'number', self.gf('django.db.models.fields.IntegerField')(default=1), keep_default=False)

        # Adding field 'Comment.is_deleted'
        db.add_column('blog_comment', 'is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding unique constraint on 'Comment', fields ['post', 'number']
        db.create_unique('blog_comment', ['post_id', 'number'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Comment', fields ['post', 'number']
        db.delete_unique('blog_comment', ['post_id', 'number'])

        # Removing unique constraint on 'Post', fields ['id', 'user']
        db.delete_unique('blog_post', ['id', 'user_id'])

        # Deleting field 'Post.is_deleted'
        db.delete_column('blog_post', 'is_deleted')

        # Deleting field 'Comment.user'
        db.delete_column('blog_comment', 'user_id')

        # Deleting field 'Comment.number'
        db.delete_column('blog_comment', 'number')

        # Deleting field 'Comment.is_deleted'
        db.delete_column('blog_comment', 'is_deleted')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'blog.comment': {
            'Meta': {'unique_together': "(('post', 'number'),)", 'object_name': 'Comment'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'from_client': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['blog.Post']"}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['blog.Comment']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'blog.post': {
            'Meta': {'unique_together': "(('id', 'user'),)", 'object_name': 'Post'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'from_client': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'blog.recommends': {
            'Meta': {'object_name': 'Recommends'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['blog.Post']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recommends_user'", 'to': "orm['auth.User']"})
        },
        'blog.subscribed': {
            'Meta': {'object_name': 'Subscribed'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subscribe_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscribed'", 'to': "orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'me_subscribe'", 'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['blog']
