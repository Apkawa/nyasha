import os, Image
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import ImageFieldFile

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^blog\.fields\.AvatarImageField"])


class AvatarStorage(FileSystemStorage):
    def __init__(self, thumb_sizes=None, **kwargs):
        self.thumb_sizes = thumb_sizes or []
        super(AvatarStorage, self).__init__(**kwargs)

    def get_thumb_name(self, name, thumb_size):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        name = os.path.join(dir_name, "%s_%s%s" % (file_root, thumb_size, file_ext))
        return name

    def get_available_name(self, name):
        if self.exists(name):
            self.delete(name)
        return name

    def _save_thumb(self, name, size):
        i = Image.open(self.path(name))
        i.thumbnail([size, size])
        name = self.path(self.get_thumb_name(name, size))
        i.save(open(name, 'w'), 'jpeg')
        return name


    def _save(self, name, content):
        result =  super(AvatarStorage, self)._save(name, content)
        for size in self.thumb_sizes:
            self._save_thumb(name, size)
        return result

class AvatarImageFileField(ImageFieldFile):
    def __init__(self, *args, **kwargs):
        super(AvatarImageFileField, self).__init__(*args, **kwargs)
        self.thumb_sizes = self.field.thumb_sizes
        self._make_prop()

    def get_thumb_name(self, size):
        thumb_name = self.storage.get_thumb_name(self.name, size)
        if self.storage.exists(self.name) and not self.storage.exists(thumb_name):
            self.storage._save_thumb(self.name, size)
        return thumb_name

    def _make_prop(self):
        for size in self.thumb_sizes:
            if self.name:
                thumb_name = self.get_thumb_name(size)
                path = self.storage.path(thumb_name)
                url = self.storage.url(thumb_name)
            else:
                path = url = None
            setattr(self, 'path_%s'%size, path)
            setattr(self, 'url_%s'%size, url)

    def save(self, *args, **kwargs):
        super(AvatarImageFileField, self).save(*args, **kwargs)
        if self.name and self.storage.exists(self.name):
            self._make_prop()

    def delete(self, *args, **kwargs):
        super(AvatarImageFileField, self).delete(*args, **kwargs)
        if self.name and self.storage.exists(self.name):
            self._make_prop()



class AvatarImageField(models.ImageField):
    attr_class = AvatarImageFileField

    def __init__(self, thumb_sizes=None, **kwargs):
        if 'storage' not in kwargs:
            kwargs['storage'] = AvatarStorage(thumb_sizes=thumb_sizes)
        self.thumb_sizes = thumb_sizes or []
        super(AvatarImageField, self).__init__(**kwargs)

