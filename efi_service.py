"""
Serviço de integração com Efí (Gerencianet) para pagamentos PIX
Usando API REST direta (sem SDK)
"""
import os
import hashlib
import hmac
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()


class EfiService:
    """Classe para gerenciar pagamentos PIX via Efí API REST"""
    
    def __init__(self):
        """Inicializa a conexão com a API da Efí"""

        env = os.getenv('EFI_ENVIRONMENT', 'sandbox').lower()
        self.is_sandbox = env == 'sandbox'

        if self.is_sandbox:
            self.client_id = os.getenv('EFI_SANDBOX_CLIENT_ID')
            self.client_secret = os.getenv('EFI_SANDBOX_CLIENT_SECRET')
            self.certificate_path = os.getenv('EFI_SANDBOX_CERTIFICATE_PATH', 'certs/homologacao.pem')
            self.pix_key = os.getenv('EFI_SANDBOX_PIX_KEY')
            self.base_url = 'https://pix-h.api.efipay.com.br'
        else:
            self.client_id = os.getenv('EFI_PRODUCTION_CLIENT_ID')
            self.client_secret = os.getenv('EFI_PRODUCTION_CLIENT_SECRET')
            self.certificate_path = os.getenv('EFI_PRODUCTION_CERTIFICATE_PATH', 'certs/producao.pem')
            self.pix_key = os.getenv('EFI_PRODUCTION_PIX_KEY')
            self.base_url = 'https://pix.api.efipay.com.br'

        # Corrigir .p12 → .pem baseado no ambiente
        if self.certificate_path.endswith('.p12'):
            # Tentar trocar extensão diretamente
            pem = self.certificate_path.replace('.p12', '.pem')
            if os.path.exists(pem):
                self.certificate_path = pem
            else:
                # Usar certificado correto baseado no ambiente
                if self.is_sandbox:
                    if os.path.exists('certs/homologacao.pem'):
                        self.certificate_path = 'certs/homologacao.pem'
                else:
                    if os.path.exists('certs/producao.pem'):
                        self.certificate_path = 'certs/producao.pem'

        if not all([self.client_id, self.client_secret, self.pix_key]):
            raise ValueError("Credenciais da Efí incompletas. Verifique o .env")

        self.access_token = None
        self.token_expiry = None

    # ==========================================================
    # TOKEN
    # ==========================================================
    def _get_access_token(self):
        """Obtém token OAuth2 da Efí"""

        # TEMPORÁRIO: Invalidar token para forçar renovação
        self.access_token = None
        self.token_expiry = None

        # Reutilizar se válido
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        print(f"DEBUG: Using cert path: {self.certificate_path}")
        
        scope_param = "gn.pix.write gn.pix.read"
        print(f"DEBUG: Requesting OAuth scopes: {scope_param}")
        
        try:
            response = requests.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "scope": scope_param
                },
                auth=(self.client_id, self.client_secret),
                cert=self.certificate_path,
                verify=True
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600) - 300)

            return self.access_token

        except Exception as e:
            raise Exception(f"Erro ao obter token: {str(e)}")

    # ==========================================================
    # CRIAÇÃO DA COBRANÇA PIX
    # ==========================================================
    def create_pix_charge(self, amount, raffle_title, raffle_id, user_id, tickets_data, cpf):
        """
        Cria cobrança PIX imediata (geração de QR Code)
        """

        try:
            token = self._get_access_token()
            txid = self._generate_txid(raffle_id, user_id)

            clean_cpf = ''.join(filter(str.isdigit, str(cpf)))
            if len(clean_cpf) != 11:
                return {"success": False, "error": "CPF inválido (11 dígitos necessários)"}

            body = {
                "calendario": {"expiracao": 900},
                "devedor": {
                    "nome": f"Usuário {user_id}",
                    "cpf": clean_cpf
                },
                "valor": {
                    "original": f"{amount:.2f}"
                },
                "chave": self.pix_key,
                "solicitacaoPagador": f"Rifa: {raffle_title}",
                "infoAdicionais": [
                    {"nome": "Rifa ID", "valor": str(raffle_id)},
                    {"nome": "User ID", "valor": str(user_id)},
                ]
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
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

            # A resposta já inclui pixCopiaECola, não precisa de outra chamada!
            pix_code = cob_data.get('pixCopiaECola', '')
            
            # Gerar QR Code localmente (evita chamada extra e problema de escopo)
            if pix_code:
                import qrcode
                import io
                import base64
                
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(pix_code)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                qr_code_base64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            else:
                qr_code_base64 = ''

            expiration = datetime.now() + timedelta(minutes=15)

            return {
                "success": True,
                "txid": txid,
                "loc_id": cob_data["loc"]["id"],
                "qr_code": qr_code_base64,
                "copy_paste": pix_code,
                "expiration": expiration.isoformat(),
                "status": "pending"
            }

        except requests.exceptions.RequestException as e:
            err = f"Erro na API Efí: {str(e)}"
            if e.response is not None:
                err += f" | {e.response.text}"
            return {"success": False, "error": err}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================
    # CONSULTAR STATUS DO PAGAMENTO
    # ==========================================================
    def check_payment_status(self, txid):
        try:
            token = self._get_access_token()

            response = requests.get(
                f"{self.base_url}/v2/cob/{txid}",
                headers={"Authorization": f"Bearer {token}"},
                cert=self.certificate_path,
                verify=True
            )
            response.raise_for_status()

            cob = response.json()

            status_map = {
                "ATIVA": "pending",
                "CONCLUIDA": "paid",
                "REMOVIDA_PELO_USUARIO_RECEBEDOR": "cancelled",
                "REMOVIDA_PELO_PSP": "expired"
            }

            status = status_map.get(cob.get("status"), "pending")
            paid_at = None

            if status == "paid" and "pix" in cob and len(cob["pix"]) > 0:
                paid_at = cob["pix"][0]["horario"]

            return {"success": True, "status": status, "paid_at": paid_at, "raw_response": cob}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================================
    # WEBHOOK
    # ==========================================================
    def validate_webhook(self, payload, signature):
        try:
            if not signature.startswith("sha256="):
                return False

            received = signature.replace("sha256=", "")
            calc = hmac.new(
                self.client_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(received, calc)

        except:
            return False

    # ==========================================================
    # GERAÇÃO DO TXID
    # ==========================================================
    def _generate_txid(self, raffle_id, user_id):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        base = f"{raffle_id}{user_id}{timestamp}"
        return hashlib.sha256(base.encode()).hexdigest()[:32].upper()


efi_service = EfiService()
