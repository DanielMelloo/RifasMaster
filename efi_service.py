"""
Serviço de integração com Efí (Gerencianet) para pagamentos PIX
Usando API REST direta (sem SDK)
"""
import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()


class EfiService:
    """Classe para gerenciar pagamentos PIX via Efí API REST"""
    
    def __init__(self):
        """Inicializa a conexão com a API da Efí"""
        # Determinar ambiente (sandbox ou production)
        env = os.getenv('EFI_ENVIRONMENT', 'sandbox').lower()
        self.is_sandbox = env == 'sandbox'
        
        # Carregar credenciais do ambiente correto
        if self.is_sandbox:
            self.client_id = os.getenv('EFI_SANDBOX_CLIENT_ID')
            self.client_secret = os.getenv('EFI_SANDBOX_CLIENT_SECRET')
            self.certificate_path = os.getenv('EFI_SANDBOX_CERTIFICATE_PATH', 'certs/homologacao.p12')
            self.pix_key = os.getenv('EFI_SANDBOX_PIX_KEY')
            self.base_url = 'https://pix-h.api.efipay.com.br'
        else:
            self.client_id = os.getenv('EFI_PRODUCTION_CLIENT_ID')
            self.client_secret = os.getenv('EFI_PRODUCTION_CLIENT_SECRET')
            self.certificate_path = os.getenv('EFI_PRODUCTION_CERTIFICATE_PATH', 'certs/producao.p12')
            self.pix_key = os.getenv('EFI_PRODUCTION_PIX_KEY')
            self.base_url = 'https://pix.api.efipay.com.br'
        
        # Validar credenciais
        if not all([self.client_id, self.client_secret, self.pix_key]):
            raise ValueError(
                f"Credenciais da Efí incompletas para ambiente '{env}'. "
                f"Verifique o arquivo .env"
            )
        
        self.access_token = None
        self.token_expiry = None
    
    def _get_access_token(self):
        """Obtém token de acesso OAuth2"""
        # Reusar token se ainda válido
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        # Gerar novo token
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }
        data = {'grant_type': 'client_credentials'}
        
        try:
            response = requests.post(
                f"{self.base_url}/oauth/token",
                headers=headers,
                json=data,
                cert=self.certificate_path,
                verify=True
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token válido por 1 hora, mas renovamos 5min antes
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600) - 300)
            
            return self.access_token
        except Exception as e:
            raise Exception(f"Erro ao obter token: {str(e)}")
    
    def create_pix_charge(self, amount, raffle_title, raffle_id, user_id, tickets_data):
        """
        Cria uma cobrança PIX imediata
        
        Args:
            amount (float): Valor total em reais
            raffle_title (str): Título da rifa
            raffle_id (int): ID da rifa
            user_id (int): ID do usuário
            tickets_data (dict): Dados dos bilhetes (para meta)
            
        Returns:
            dict: {
                'success': bool,
                'txid': str,
                'qr_code': str (base64),
                'copy_paste': str,
                'expiration': str (ISO datetime)
            }
        """
        try:
            token = self._get_access_token()
            
            # Gerar txid único
            txid = self._generate_txid(raffle_id, user_id)
            
            # Corpo da requisição
            body = {
                'calendario': {
                    'expiracao': 900  # 15 minutos em segundos
                },
                'devedor': {
                    'nome': f'Usuário {user_id}'
                },
                'valor': {
                    'original': f'{amount:.2f}'
                },
                'chave': self.pix_key,
                'solicitacaoPagador': f'Rifa: {raffle_title}',
                'infoAdicionais': [
                    {'nome': 'Rifa ID', 'valor': str(raffle_id)},
                    {'nome': 'User ID', 'valor': str(user_id)}
                ]
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Criar cobrança
            response = requests.put(
                f"{self.base_url}/v2/cob/{txid}",
                headers=headers,
                json=body,
                cert=self.certificate_path,
                verify=True
            )
            response.raise_for_status()
            
            cob_data = response.json()
            
            # Gerar QR Code
            loc_id = cob_data['loc']['id']
            qrcode_response = requests.get(
                f"{self.base_url}/v2/loc/{loc_id}/qrcode",
                headers=headers,
                cert=self.certificate_path,
                verify=True
            )
            qrcode_response.raise_for_status()
            
            qr_data = qrcode_response.json()
            
            expiration = datetime.now() + timedelta(minutes=15)
            
            return {
                'success': True,
                'txid': txid,
                'loc_id': loc_id,
                'qr_code': qr_data.get('imagemQrcode', ''),
                'copy_paste': qr_data.get('qrcode', ''),
                'expiration': expiration.isoformat(),
                'status': 'pending'
            }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erro na API Efí: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_payment_status(self, txid):
        """
        Consulta o status de um pagamento
        
        Args:
            txid (str): ID da transação
            
        Returns:
            dict: {'status': 'pending'/'paid'/'expired', 'paid_at': datetime or None}
        """
        try:
            token = self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/v2/cob/{txid}",
                headers=headers,
                cert=self.certificate_path,
                verify=True
            )
            response.raise_for_status()
            
            cob_data = response.json()
            
            status_map = {
                'ATIVA': 'pending',
                'CONCLUIDA': 'paid',
                'REMOVIDA_PELO_USUARIO_RECEBEDOR': 'cancelled',
                'REMOVIDA_PELO_PSP': 'expired'
            }
            
            status = status_map.get(cob_data.get('status'), 'pending')
            paid_at = None
            
            # Se pago, pegar data do pagamento
            if status == 'paid' and 'pix' in cob_data and len(cob_data['pix']) > 0:
                paid_at = cob_data['pix'][0].get('horario')
            
            return {
                'success': True,
                'status': status,
                'paid_at': paid_at,
                'raw_response': cob_data
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_webhook(self, payload, signature):
        """
        Valida a assinatura do webhook da Efí
        
        Args:
            payload (bytes): Corpo da requisição
            signature (str): Assinatura enviada no header
            
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            # A Efí envia a assinatura no formato: sha256=<hash>
            if not signature.startswith('sha256='):
                return False
            
            received_hash = signature.replace('sha256=', '')
            
            # Calcular hash esperado
            secret = self.client_secret.encode('utf-8')
            calculated_hash = hmac.new(secret, payload, hashlib.sha256).hexdigest()
            
            # Comparação segura
            return hmac.compare_digest(calculated_hash, received_hash)
        except Exception:
            return False
    
    def _generate_txid(self, raffle_id, user_id):
        """Gera um txid único para a transação"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        base = f"{raffle_id}{user_id}{timestamp}"
        # txid deve ter entre 26 e 35 caracteres
        return hashlib.sha256(base.encode()).hexdigest()[:32].upper()


# Instância singleton
efi_service = EfiService()
