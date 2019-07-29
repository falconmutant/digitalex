from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.genesis import Maya


class GenesisRest(APIView):
	def post(self, request):
		if 'multiSearch' in request.data['target']:
			data = []
			for search in request.data['model']:
				genesis = Maya(search)
				data, _status = genesis.handler()
				data.append({
					'data': data,
					'status': _status
				})
			return Response(data, status=status.HTTP_200_OK)
		else:
			genesis = Maya(request)
			data, _status = genesis.handler()
			return Response(data, status=_status)


class GenesisAPI(APIView):
	permission_classes = (AllowAny,)

	def post(self, request):
		if request.data['action'] in 'get all login register':
			if 'multiSearch' in request.data['target']:
				data = []
				for search in request.data['model']:
					genesis = Maya(search)
					data, _status = genesis.handler()
					data.append({
						'data': data,
						'status': _status
					})
				return Response(data, status=status.HTTP_200_OK)
			else:
				genesis = Maya(request)
				data, _status = genesis.handler()
				return Response(data, status=_status)
