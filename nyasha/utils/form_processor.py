# -*- coding: utf-8 -*-
from copy import copy
from django import forms
class BaseFormProcessor(object):
    '''
    Обертка, которая немного упрощает обработку формы
    
    Базовый класс

    :arg form_class: Форма, которую заворачиваем
    :type form_class: `django.forms.Form` or `django.forms.ModelForm`
    :arg request: Объект реквеста
    :type request: `HttpRequest`
    :arg initial: начальные данные для формы
    :type initial: `dict`
    :arg instance: Объект модели, используется, если форма унаследована от `models.Model`
    :type instance: subclass :class:`django.db.models.Model`
    :arg args: Дополнительные неименованные аргументы, которые передаются в форму
    :type args: `list` or `tuple`
    :arg kwargs: Дополнительные именованные аргументы, которые передаются в форму
    :type kwargs: `dict`
    '''
    def __init__(self, form_class, request=None,
            initial=None, instance=None, args=None, kwargs=None):

        self.form_class = form_class
        self.request = request
        if request:
            self.post_data = copy(request.POST)
        else:
            self.post_data = {}
        self.initial = initial
        self.instance = instance

        self.args = args or ()
        self.kwargs = kwargs or {}


        self.valid = False
        self.data = None
        self.form = None

    def process(self, commit=True):
        '''
        Процесс валидации

        :arg commit: Если значение истинно - то при успешной проверке данных для формы она сохраняется, иначе пропускается этот шаг.
        :type commit: `bool`
        '''
        if self.initial:
            self.kwargs['initial'] = self.initial
        if self.instance:
            self.kwargs['instance'] = self.instance


        post = self.post_data
        if post and self.form_class.base_fields.has_key('form_id'):
            prefix = self.kwargs.get('prefix')
            form_id = "%s-form_id"% prefix if prefix else 'form_id'
            if form_id not in post \
                or  self.form_class.get_form_id(prefix) not in post.getlist(form_id):
                self.post_data = None

        if self.request and self.post_data:
            self.form = self.form_class(data= self.post_data,
                    files=self.request.FILES, *self.args, **self.kwargs)
            if self.form.is_valid():
                #print 'VALIDDDD'
                self.data = self.form.cleaned_data
                self.valid = True
                if not issubclass(self.form_class, forms.Form) and commit:
                    return self.success()
            else:
                print 'errors ', self.form.errors
        else:
            self.form = self.form_class(*self.args, **self.kwargs)

    def is_valid(self):
        '''
        Копирует функциональность Form().is_valid
        '''
        return self.form.is_valid() and self.valid

    def success(self):
        '''
        Метод, вызываемый при успешной валидации формы.
        По умолчанию, если форма `forms.ModelForm`, то сохраняется и возвращается `self.instance`
        '''
        pass

    def fail(self):
        '''
        Метод, вызываемый при провале валидации
        '''
        pass

class FormProcessor(BaseFormProcessor):
    '''
    Обертка, автоматизирующая обработку форм

    Пример использования:
        >>> form_p  = FormProcessor(Form, request, instance=instance)
        >>> form_p.process()
        >>> if form_p.is_valid():
        >>>     form_p.save()
    '''
    pass




