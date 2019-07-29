from django.apps import apps
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import ManyToManyField, ForeignKey
from rest_framework import serializers, status
from knox.models import AuthToken


class DynamicSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model', None)
        fields = kwargs.pop('fields', None)
        super(DynamicSerializer, self).__init__(*args, **kwargs)

        if model is not None:
            self.Meta.model = model
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class Serializer(DynamicSerializer):
    class Meta:
        model = None
        fields = '__all__'


class Maya:
    def __init__(self, request):
        self.request = request
        self.fields = None
        self.depth = 0
        self.depth_fields = None
        self.error = False
        self.save = False

        self.target = request.data['target']
        self.action = request.data['action']
        self.data = request.data['model']

        if 'depth' in request.data:
            self.depth = request.data['depth']
        if 'd_fields' in request.data:
            self.depth_fields = request.data['d_fields']
        if self.target not in 'auth user':
            try:
                self.model = apps.get_app_config("core").models[self.target]
            except Exception:
                self.error = True

            if 'get' in request.data:
                self.fields = request.data['get']
        elif 'user' in self.target:
            self.fields = ['id', 'username', 'password', 'email']
            self.model = User

    @transaction.atomic
    def is_valid(self, data):
        try:
            if data.is_valid():
                data.save()
                self.save = True
                return data.data, status.HTTP_200_OK
            else:
                raise IntegrityError
        except IntegrityError:
            return {'MayaMessage': data.errors}, status.HTTP_400_BAD_REQUEST

    @transaction.atomic
    def depth_transaction(self, json, model):
        if 'MayaMessage' in json:
            return json, status.HTTP_400_BAD_REQUEST
        elif 'id' in json:
            return json, status.HTTP_200_OK
        else:
            for item in json.items():
                if isinstance(item[1], type([])):
                    field = model._meta.get_field(item[0])
                    if isinstance(field, ManyToManyField):
                        values = []
                        for value in item[1]:
                            if isinstance(value, dict):
                                response, _status = self.depth_transaction(value, field.related_model)
                                try:
                                    if 'MayaMessage' in response:
                                        raise IntegrityError
                                    values.append(response['id'])
                                except IntegrityError:
                                    return response, _status
                            else:
                                values.append(value)
                        json[item[0]] = values
                elif isinstance(item[1], dict):
                    field = model._meta.get_field(item[0])
                    if isinstance(field, ForeignKey):
                        if 'user' in item[0]:
                            response, _status = self.is_valid(
                                Serializer(data=item[1], fields=('id', 'username', 'email'), model=User))
                            try:
                                if 'MayaMessage' in response:
                                    raise IntegrityError
                                json[item[0]] = response['id']
                                user = User.objects.get(id=response['id'])
                                user.set_password(item[1]['password'])
                                user.save()
                            except IntegrityError:
                                if 'MayaMessage' in response:
                                    return response, _status
                                else:
                                    return {'MayaMessage': 'Usuario sin contraseña'}, status.HTTP_400_BAD_REQUEST
                        else:
                            response, _status = self.depth_transaction(item[1], field.related_model)
                            try:
                                if 'MayaMessage' in response:
                                    raise IntegrityError
                                json[item[0]] = response['id']
                            except IntegrityError:
                                return response, _status
            return self.is_valid(Serializer(data=json, fields=self.fields, model=model))

    def depth_serializer(self, json, model, depth=0, d_fields=None):
        if 'MayaMessage' in json:
            return json
        fields = model._meta.get_fields()
        for field in fields:
            if field.name in json:
                if json[field.name] is not None:
                    if isinstance(field, ManyToManyField):
                        model_tmp = field.related_model
                        values = model_tmp.objects.filter(id__in=json[field.name])
                        json[field.name] = Serializer(values, many=True, fields=d_fields, model=model_tmp).data
                        if depth > 0:
                            json_element = []
                            for element in json[field.name]:
                                if depth == 1:
                                    json_element.append(self.depth_serializer(element, model_tmp))
                                elif depth == 2:
                                    json_element.append(self.depth_serializer(element, model_tmp, 1))
                            json[field.name] = json_element

                    elif isinstance(field, ForeignKey):
                        model_tmp = field.related_model
                        value = model_tmp.objects.get(id=json[field.name])
                        if field.name == 'user':
                            json[field.name] = Serializer(value, fields=('id', 'username', 'email'), model=User).data
                        else:
                            json[field.name] = Serializer(value, fields=d_fields, model=model_tmp).data
                            if depth > 0:
                                if depth == 1:
                                    json[field.name] = self.depth_serializer(json[field.name], model_tmp)
                                elif depth == 2:
                                    json[field.name] = self.depth_serializer(json[field.name], model_tmp, 1)
        return json

    def depth_modify(self, json, model):
        fields = model._meta.get_fields()
        for field in fields:
            if field.name in json:
                if json[field.name] is not None:
                    if isinstance(field, ManyToManyField):
                        for pos in range(0, len(json[field.name])):
                            if isinstance(json[field.name][pos], dict):
                                model_tmp = field.related_model
                                if 'id' in json[field.name][pos]:
                                    obj = model_tmp.objects.get(id=json[field.name][pos]['id'])
                                    modify = Serializer(obj, data=json[field.name][pos], partial=True, fields=self.fields, model=model_tmp)
                                    response, _status = self.is_valid(modify)
                                    try:
                                        json[field.name][pos] = response['id']
                                    except Exception:
                                        return response, _status
                                else:
                                    _transaction, _status = self.depth_transaction(json[field.name][pos], model_tmp)
                                    if 'MayaMessage' in _transaction:
                                        return _transaction, _status
                                    json[field.name][pos] = _transaction['id']
                    elif isinstance(field, ForeignKey):
                        if isinstance(json[field.name], dict):
                            model_tmp = field.related_model
                            if 'id' in json[field.name]:
                                obj = model_tmp.objects.get(id=json[field.name]['id'])
                                modify = Serializer(obj, data=json[field.name], partial=True, fields=self.fields, model=model_tmp)
                                response, _status = self.is_valid(modify)
                                try:
                                    json[field.name] = response['id']
                                except Exception:
                                    return response, _status
                            else:
                                _transaction, _status = self.depth_transaction(json[field.name], model_tmp)
                                if 'MayaMessage' in _transaction:
                                    return _transaction, _status
                                json[field.name] = _transaction['id']
        return json, status.HTTP_200_OK

    def search(self, json, model):
        fields = model._meta.get_fields()
        for field in fields:
            if field.name in json:
                if json[field.name] is not None:
                    if isinstance(field, ManyToManyField) and isinstance(json[field.name], dict):
                        model_tmp = field.related_model
                        json[field.name] = self.search(json[field.name], model_tmp)
                        values = model_tmp.objects.filter(**json[field.name])
                        json[field.name + "__in"] = [value.id for value in values]
                        json.pop(field.name, None)

                    elif isinstance(field, ForeignKey) and isinstance(json[field.name], dict):
                        model_tmp = field.related_model
                        json[field.name] = self.search(json[field.name], model_tmp)
                        value = model_tmp.objects.filter(**json[field.name])
                        if len(value) > 1:
                            json[field.name + "__in"] = [val.id for val in value]
                            json.pop(field.name, None)
                        else:
                            json[field.name] = value.id

                    elif isinstance(json[field.name], list):
                        json[field.name + "__in"] = json[field.name]
                        json.pop(field.name, None)
        return json

    def get(self, all=False):
        if all:
            if 'user' == self.target:
                self.fields.pop(self.fields.index('password'))
                data = self.model.objects.all()
            else:
                data = self.model.objects.filter(alive=True)
        elif 'search' in self.data:
            data = self.search(self.data['search'], self.model)
            data = self.model.objects.filter(**data)
        else:
            data = self.model.objects.filter(id__in=self.data['id'])

        if 'order_by' in self.data:
            data = data.order_by(self.data['order_by'])
        if 'limit' in self.data:
            data = data[:self.data['limit']]

        response = Serializer(data, many=True, fields=self.fields, model=self.model).data

        for pos in range(0, len(response)):
            response[pos] = self.depth_serializer(response[pos], self.model, self.depth, self.depth_fields)

        return response, status.HTTP_200_OK

    @staticmethod
    def validate(data, model):
        result = model.objects.filter(**data)
        if result.count() > 0:
            return False
        return True

    @transaction.atomic
    def add(self):
        if self.target == 'user' or self.action == 'register':
            response, _status = self.is_valid(
                Serializer(data=self.data, fields=('id', 'username', 'password', 'email'), model=User))
            try:
                user = User.objects.get(id=response['id'])
                user.set_password(self.data['password'])
                user.save()
            except IntegrityError:
                pass
            return response, _status
        else:
            valid = True
            if 'validate' in self.request.data:
                valid = self.validate(self.request.data['validate'], self.model)
            if valid:
                response, _status = self.depth_transaction(self.data, self.model)
                try:
                    if 'MayaMessage' in response:
                        raise IntegrityError
                    return self.depth_serializer(response, self.model, self.depth, self.depth_fields), _status
                except IntegrityError:
                    return response, _status
            else:
                return {
                           'MayaMessage': 'Validation not passed, data not saved',
                           'validate': self.request.data['validate'],
                           'data': self.data
                       }, status.HTTP_401_UNAUTHORIZED

    def delete(self):
        model = self.model.objects.filter(id__in=self.data['id'])
        for m in model:
            if self.target == 'user':
                m.delete()
            else:
                m.alive = False
                m.save()
        return {'MayaMessage': 'Deleted'}, status.HTTP_200_OK

    @transaction.atomic
    def modify(self):
        data = self.model.objects.get(id=self.data['id'])
        if self.target == 'user':
            if 'password' in self.data:
                self.fields.pop(self.fields.index('password'))
                response, _status = self.is_valid(
                    Serializer(data, data=self.data, partial=True, fields=self.fields, model=self.model))
                try:
                    if 'MayaMessage' in response:
                        raise IntegrityError
                    data.set_password(self.data['password'])
                    data.save()
                except IntegrityError:
                    pass
                return response, _status
            else:
                self.fields.pop(self.fields.index('password'))
                response, _status = self.is_valid(
                    Serializer(data, data=self.data, partial=True, fields=self.fields, model=self.model))
                try:
                    if 'MayaMessage' in response:
                        raise IntegrityError
                except IntegrityError:
                    pass
                return response, _status

        else:
            response, _status = self.depth_modify(self.data, self.model)
            try:
                if 'MayaMessage' in response:
                    raise IntegrityError
                data = Serializer(data, data=response, partial=True, fields=self.fields, model=self.model)
                response, _status = self.is_valid(data)
                if 'MayaMessage' in response:
                    raise IntegrityError
                return self.depth_serializer(response, self.model, self.depth, self.depth_fields), _status
            except IntegrityError:
                return response, _status

    def login(self):
        user = authenticate(**self.data)
        if user and user.is_active:
            token = AuthToken.objects.create(user)
            return {
                'user': Serializer(user, fields=('id', 'username', 'email'), model=User).data,
                'token': token[1]
            }, status.HTTP_200_OK
        else:
            return {'MayaMessage': "Usuario o Contraseña Incorrectos"}, status.HTTP_401_UNAUTHORIZED

    def handler(self):
        if self.error:
            return {'MayaMessage': 'Target no exist'}, status.HTTP_400_BAD_REQUEST
        else:
            if 'all' in self.action:
                return self.get(True)
            elif 'get' in self.action:
                return self.get()
            elif 'add' in self.action:
                return self.add()
            elif 'delete' in self.action:
                return self.delete()
            elif 'modify' in self.action:
                return self.modify()
            elif 'login' in self.action:
                if 'actual' in self.action:
                    return Serializer(self.request.user, fields=('id', 'username', 'email'), model=User).data, status.HTTP_200_OK
                else:
                    return self.login()
            elif 'register' in self.action:
                self.add()
                return self.login()
