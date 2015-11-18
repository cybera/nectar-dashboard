# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'AllocationRequest.volume_quota'
        db.delete_column(u'rcallocation_allocationrequest', 'volume_quota')

        # Deleting field 'AllocationRequest.volume_gb'
        db.delete_column(u'rcallocation_allocationrequest', 'volume_gb')

        # Deleting field 'AllocationRequest.object_storage_GBs'
        db.delete_column(u'rcallocation_allocationrequest', 'object_storage_GBs')

        # Deleting field 'AllocationRequest.object_store_quota'
        db.delete_column(u'rcallocation_allocationrequest', 'object_store_quota')


    def backwards(self, orm):
        # Adding field 'AllocationRequest.volume_quota'
        db.add_column(u'rcallocation_allocationrequest', 'volume_quota',
                      self.gf('django.db.models.fields.IntegerField')(default='0'),
                      keep_default=False)

        # Adding field 'AllocationRequest.volume_gb'
        db.add_column(u'rcallocation_allocationrequest', 'volume_gb',
                      self.gf('django.db.models.fields.IntegerField')(default='0'),
                      keep_default=False)

        # Adding field 'AllocationRequest.object_storage_GBs'
        db.add_column(u'rcallocation_allocationrequest', 'object_storage_GBs',
                      self.gf('django.db.models.fields.IntegerField')(default='0'),
                      keep_default=False)

        # Adding field 'AllocationRequest.object_store_quota'
        db.add_column(u'rcallocation_allocationrequest', 'object_store_quota',
                      self.gf('django.db.models.fields.IntegerField')(default='0'),
                      keep_default=False)


    models = {
        u'rcallocation.allocationrequest': {
            'Meta': {'object_name': 'AllocationRequest'},
            'approver_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'convert_trial_project': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'core_hours': ('django.db.models.fields.IntegerField', [], {'default': "'100'"}),
            'core_quota': ('django.db.models.fields.IntegerField', [], {'default': "'0'"}),
            'cores': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2015, 8, 17, 0, 0)'}),
            'field_of_research_1': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'field_of_research_2': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'field_of_research_3': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'for_percentage_1': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'for_percentage_2': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'for_percentage_3': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'geographic_requirements': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_quota': ('django.db.models.fields.IntegerField', [], {'default': "'0'"}),
            'instances': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'modified_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'object_storage_zone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'parent_request': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['rcallocation.AllocationRequest']", 'null': 'True', 'blank': 'True'}),
            'primary_instance_type': ('django.db.models.fields.CharField', [], {'default': "'S'", 'max_length': '1'}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'ram_quota': ('django.db.models.fields.IntegerField', [], {'default': "'0'"}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'status_explanation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'submit_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'tenant_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'tenant_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'usage_patterns': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'use_case': ('django.db.models.fields.TextField', [], {'max_length': '4096'}),
            'volume_zone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        u'rcallocation.quota': {
            'Meta': {'object_name': 'Quota'},
            'allocation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quotas'", 'to': u"orm['rcallocation.AllocationRequest']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quota': ('django.db.models.fields.IntegerField', [], {'default': "'0'"}),
            'requested_quota': ('django.db.models.fields.IntegerField', [], {'default': "'0'"}),
            'resource': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'units': ('django.db.models.fields.CharField', [], {'default': "'GB'", 'max_length': '64'}),
            'zone': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['rcallocation']
