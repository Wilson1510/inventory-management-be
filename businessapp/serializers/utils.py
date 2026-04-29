READ_ONLY_FIELDS = ['created_at', 'created_by', 'updated_at', 'updated_by']
METADATA_FIELDS = ['id'] + READ_ONLY_FIELDS


def sync_fk_children(parent, rows, *, related_name, model, fk_field, user=None):
    manager = getattr(parent, related_name)
    existing = {obj.id: obj for obj in manager.all()}
    keep_ids = {row['id'] for row in rows if row.get('id') is not None}

    for pk in existing.keys() - keep_ids:
        existing[pk].delete()

    for row in rows:
        pk = row.get('id')
        payload = {k: v for k, v in row.items() if k != 'id'}
        
        if user:
            payload['updated_by'] = user

        if pk is not None and pk in existing:
            obj = existing[pk]
            for attr, value in payload.items():
                setattr(obj, attr, value)
            obj.save()
        else:
            if user:
                payload['created_by'] = user
            model.objects.create(**{fk_field: parent}, **payload)