from rest_framework import viewsets, status
from api.models import *
from api.serializers import *
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import yagmail
import os
from dotenv import load_dotenv
from django.contrib.auth import get_user_model
import random
import string
from django.conf import settings


class User(APIView):
    
    def get(self, request, id=None):
        if id:
            usuario = get_object_or_404(CustomUser, pk=id)
            serializer = UserSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 👇 SEMPRE começa filtrando NÃO ADMINS
        queryset = CustomUser.objects.filter(is_adm=False)

        nome = request.query_params.get("nome")
        if nome:
            queryset = queryset.filter(first_name__icontains=nome)

        # 👇 Só depois aplica limite de 5
        usuarios = queryset[:5]

        serializer = UserSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



    def post(self, request):
        nome = request.data.get('nome')
        senha = request.data.get('senha')
        ra = request.data.get('ra')
        fistName = request.data.get('first_name')
        isAdm = request.data.get('is_adm')
        

        if not nome or not senha:
            return Response({"error": "Todos os campos são obrigatórios!", "status": status.HTTP_400_BAD_REQUEST}, status= status.HTTP_400_BAD_REQUEST)

        usuario = CustomUser.objects.create(
            username = nome,
            password = make_password(senha),
            is_active = True,
            first_name = fistName,
            is_adm = isAdm,
            ra = ra
        )

        # Enviar email após cadastro #
        load_dotenv()

        yag = yagmail.SMTP(
            user=os.getenv("EMAIL_USER"),
            password=os.getenv("EMAIL_PASSWORD"),
            host=os.getenv("EMAIL_HOST"),
            port=int(os.getenv("EMAIL_PORT")),
            smtp_starttls=True,       
            smtp_ssl=False    
        )

        yag.send(
            to=usuario.username,
            subject='Bem vindo ao Sistema Digicoin',
            contents=(
                f'Nome: {fistName}\n'
                f'RA: {ra}\n'
                f'Login: {nome}\n'
                f'Senha: {senha}\n'
                f"Altere sua senha depois do primeiro acesso."
            )
        )

        return Response({"message":"Usuário criado com sucesso!", "id":usuario.id, "status": status.HTTP_201_CREATED})

    def put(self, request, id):
        usuario = get_object_or_404(CustomUser, pk=id)
        data = request.data.copy()
        operacao = data.get("operacao")
       
        
        if operacao in ['adicionar', 'remover']:
            try:
                saldo = int(data.get("saldo", 0))
            except (TypeError, ValueError):
                return Response({"erro": "Saldo inválido."}, status=status.HTTP_400_BAD_REQUEST)

            if operacao == 'adicionar':
                usuario.pontuacao += saldo
                usuario.saldo += saldo

            elif operacao == 'remover':
                if usuario.saldo < saldo:
                    return Response({"erro": "Saldo insuficiente."}, status=status.HTTP_400_BAD_REQUEST)
                usuario.pontuacao -= saldo
                usuario.saldo -= saldo

            usuario.save()
            return Response({"status": status.HTTP_200_OK})
        
        serializer = UserSerializer(usuario, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": status.HTTP_200_OK})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        usuario = get_object_or_404(CustomUser, pk = id)
        if usuario:
            usuario.delete()
            return Response({"status": status.HTTP_200_OK})
        else:
            return Response({"status": status.HTTP_404_NOT_FOUND})
    
class PrimeiroAcessoSenhaView(APIView):
    def post(self, request, id):
        senha = request.data.get('senha')
        confirmar_senha = request.data.get('confirmarSenha')

        if not senha or not confirmar_senha:
            return Response({"erro": "Ambas as senhas são obrigatórias."}, status=status.HTTP_400_BAD_REQUEST)

        if senha != confirmar_senha:
            return Response({"erro": "As senhas não coincidem."}, status=status.HTTP_400_BAD_REQUEST)

        usuario = get_object_or_404(CustomUser, pk=id)
        usuario.password = make_password(senha)
        usuario.primeiroAcesso = False
        usuario.save()
        logout(request)
        return Response({"mensagem": "Senha atualizada com sucesso."}, status=status.HTTP_200_OK)


class Login(APIView):
    def post(self, request):
        nome = request.data.get('nome')
        senha = request.data.get('senha')
        
        user = authenticate(username=nome, password=senha)
        if user is not None:
            login(request, user)
            return Response({
                'is_adm': user.is_adm
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)
        
class Logout(APIView):
    def post(self, request):
        logout(request)
        return Response({"status": status.HTTP_200_OK, "mensagem": "Logout realizado com sucesso"})

class GetDadosUsuarioLogado(APIView):
    def get(self, request):
        usuarioId = request.session.get('_auth_user_id')
        if usuarioId:
            usuario = CustomUser.objects.filter(id= usuarioId).first()
            serializer = UserSerializer(usuario)
            return Response(serializer.data)

        return Response(usuarioId)
    

    
class CampanhaViewSet(viewsets.ModelViewSet):
    queryset = Campanha.objects.all()
    serializer_class = CampanhaSerializer

    def perform_create(self, serializer):
        campanha = serializer.save()

        # Filtra quem deve receber (aqui: todos usuários ativos)
        users = CustomUser.objects.filter(is_active=True)

        # Monta objetos Notificacao (não gravados ainda)
        notifs = [
            Notificacao(
                titulo=f"Nova campanha!",
                mensagem=f"A campanha de {campanha.nome} começou!",  # corta se for muito grande
                idUsuario=u
            )
            for u in users
        ]

        # Cria em massa no DB
        Notificacao.objects.bulk_create(notifs)

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

class DesafioViewSet(viewsets.ModelViewSet):
    queryset = Desafio.objects.all()
    serializer_class = DesafioSerializer

    def perform_create(self, serializer):
        desafio = serializer.save()

        users = CustomUser.objects.filter(is_active=True)

        notifs = [
            Notificacao(
                titulo=f"Novo desafio!",
                mensagem=f"O desafio de {desafio.nome} começou!",
                idUsuario=u
            )
            for u in users
        ]

        Notificacao.objects.bulk_create(notifs)

class CompraViewSet(viewsets.ModelViewSet):

    queryset = Compra.objects.all()
    serializer_class = CompraSerializer

class ItensCompraViewSet(viewsets.ModelViewSet):
    queryset = ItensCompra.objects.all()
    serializer_class = ItensCompraSerializer

class CadastrarCompraView(APIView):
    def post(self, request):
        dadosCompra = request.data.get('compra')
        itensCompra = request.data.get('itens')
        usuario_id = request.user.id
        # adiciona o id do usuário ao dadosCompra
        dadosCompra['idUsuario'] = usuario_id

        # Verifica se o usuário tem moeda suficiente
        usuario = CustomUser.objects.get(id=usuario_id)
        total_custo = dadosCompra['total']
        if usuario.saldo < total_custo:
            return Response({"error": "Usuário não tem saldo suficiente.", "status":status.HTTP_400_BAD_REQUEST})

        # Verifica se os produtos têm quantidade suficiente
        erros = []
        for item in itensCompra:
            produto = Produto.objects.get(id=item['idProduto'])
            if produto.quantidade < item['qtdProduto']:
                erros.append(f"Produto {produto.nome} não tem quantidade suficiente.")
        
        if erros:
            return Response({"error": erros, "status":status.HTTP_400_BAD_REQUEST})

        # Cria a compra
        compraSerializer = CompraSerializer(data=dadosCompra)
        if compraSerializer.is_valid():
            compra = compraSerializer.save()
        else:
            return Response(compraSerializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Cria os itens de compra
        for item in itensCompra:
            item['idCompra'] = compra.id
            itemSerializer = ItensCompraSerializer(data=item)
            if itemSerializer.is_valid():
                itemSerializer.save()
                produto.quantidade -= item['qtdProduto']
                produto.save()
            else:
                erros.append(itemSerializer.errors)

        if erros:
            return Response(erros, status=status.HTTP_400_BAD_REQUEST)

        # Deduzir moeda do usuário
        usuario.saldo -= total_custo
        usuario.save()

        return Response({"message": "Compra e itens criados com sucesso!", "status": status.HTTP_201_CREATED})
    
 
class HistoricoSaldoUsuarioView(APIView):
    """Retorna as últimas 5 alterações de saldo do usuário logado"""
    def get(self, request):
        usuario = request.user
        serializer = UsuarioComHistoricoSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

class HistoricoSaldoPorIdView(APIView):
    """Retorna as últimas 5 alterações de saldo de um usuário pelo ID"""
    def get(self, request, id):
        usuario = get_object_or_404(CustomUser, pk=id)
        serializer = UsuarioComHistoricoSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class DesenvolvedoresViewSet(viewsets.ModelViewSet):
    queryset = Desenvolvedores.objects.all()
    serializer_class = DesenvolvedoresSerializer

class NotificacaoViewSet(viewsets.ModelViewSet):
    queryset = Notificacao.objects.all()
    serializer_class = NotificacaoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(idUsuario_id=user_id)
            qs = qs[:3]
        return qs
    
class NonAdminActiveUsersAPIView(APIView):

    def get(self, request):
        users = CustomUser.objects.filter(
            is_active=True,
            is_adm=False
        ).values('id', 'first_name', 'email', 'username', 'saldo')
        return Response(list(users), status=status.HTTP_200_OK)
   

load_dotenv()

CustomUser = get_user_model() 
    
class ResetUserPasswordView(APIView):

    def post(self, request, user_id):
        if not request.user.is_authenticated or not request.user.is_adm:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        nova_senha = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        usuario.set_password(nova_senha)
        usuario.save()

        try:
            yag = yagmail.SMTP(
            user=os.getenv("EMAIL_USER"),
            password=os.getenv("EMAIL_PASSWORD"),
            host=os.getenv("EMAIL_HOST"),
            port=int(os.getenv("EMAIL_PORT", 587)),
            smtp_starttls=True,
            smtp_ssl=False
        )

            yag.send(
                to=usuario.username,  # ou usuario.email, se for o caso
                subject='[Digicoin] Sua senha foi redefinida',
                contents=(
                    f'Olá {usuario.first_name},\n\n'
                    f'Você é uma rata\n'
                    f'Por Favor vamos fazer cookies\n\n'
                    f'Se declare para o vitor tmb \n\n'
                    f'Atenciosamente,\nEquipe Digicoin'
                )
            )

        except Exception as e:
            return Response({'error': f'Erro ao enviar e-mail: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
                    'message': 'Senha redefinida e e-mail enviado com sucesso!',
                    'user_id': usuario.id,
                    'email_enviado_para': usuario.username
                }, status=status.HTTP_200_OK)
        
        
        
# f'Olá {usuario.first_name},\n\n'
#                     f'Sua senha foi redefinida pelo administrador.\n'
#                     f'Nova senha: {nova_senha}\n\n'
#                     f'Por favor, altere sua senha após o primeiro acesso.\n\n'
#                     f'Atenciosamente,\nEquipe Digicoin'