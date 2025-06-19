"""
Integração com API do Asaas para cobrança
"""

import requests
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from models import SystemSettings

logger = logging.getLogger(__name__)

class AsaasAPI:
    """Cliente para API do Asaas"""
    
    def __init__(self):
        self.api_key = SystemSettings.get_setting('asaas_api_key')
        self.base_url = "https://www.asaas.com/api/v3"
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_charge(self, customer_email: str, customer_name: str, amount: float, 
                     description: str, due_date: date) -> Dict[str, Any]:
        """
        Cria uma nova cobrança no Asaas
        
        Args:
            customer_email: Email do cliente
            customer_name: Nome do cliente
            amount: Valor da cobrança
            description: Descrição da cobrança
            due_date: Data de vencimento
            
        Returns:
            Dados da cobrança criada
        """
        try:
            # Primeiro, criar/buscar o cliente
            customer = self.get_or_create_customer(customer_email, customer_name)
            
            if not customer:
                raise Exception("Erro ao criar/buscar cliente no Asaas")
            
            # Criar a cobrança
            charge_data = {
                "customer": customer["id"],
                "billingType": "PIX",  # PIX como padrão
                "value": amount,
                "dueDate": due_date.strftime("%Y-%m-%d"),
                "description": description,
                "externalReference": f"xmldownloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "installmentCount": 1,
                "installmentValue": amount
            }
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=charge_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Cobrança criada com sucesso: {result.get('id')}")
                return {
                    "success": True,
                    "charge_id": result.get("id"),
                    "status": result.get("status"),
                    "value": result.get("value"),
                    "due_date": result.get("dueDate"),
                    "payment_url": result.get("invoiceUrl"),
                    "pix_qr_code": result.get("pixQrCodeUrl"),
                    "data": result
                }
            else:
                error_msg = f"Erro ao criar cobrança: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            error_msg = f"Erro na integração com Asaas: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_or_create_customer(self, email: str, name: str) -> Optional[Dict]:
        """Busca ou cria um cliente no Asaas"""
        try:
            # Buscar cliente existente
            search_response = requests.get(
                f"{self.base_url}/customers",
                params={"email": email},
                headers=self.headers,
                timeout=30
            )
            
            if search_response.status_code == 200:
                customers = search_response.json().get("data", [])
                if customers:
                    logger.info(f"Cliente encontrado: {customers[0]['id']}")
                    return customers[0]
            
            # Criar novo cliente
            customer_data = {
                "name": name,
                "email": email,
                "mobilePhone": "",  # Opcional
                "cpfCnpj": "",     # Opcional para este caso
                "postalCode": "",   # Opcional
                "address": "",      # Opcional
                "addressNumber": "", # Opcional
                "complement": "",    # Opcional
                "province": "",      # Opcional
                "city": "",         # Opcional
                "state": "",        # Opcional
                "country": "Brasil"
            }
            
            create_response = requests.post(
                f"{self.base_url}/customers",
                json=customer_data,
                headers=self.headers,
                timeout=30
            )
            
            if create_response.status_code == 200:
                customer = create_response.json()
                logger.info(f"Cliente criado: {customer['id']}")
                return customer
            else:
                logger.error(f"Erro ao criar cliente: {create_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar/criar cliente: {str(e)}")
            return None
    
    def check_payment_status(self, charge_id: str) -> Dict[str, Any]:
        """Verifica o status de uma cobrança"""
        try:
            response = requests.get(
                f"{self.base_url}/payments/{charge_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status"),
                    "value": result.get("value"),
                    "payment_date": result.get("paymentDate"),
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro ao consultar status: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na consulta: {str(e)}"
            }
    
    def list_charges(self, customer_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Lista cobranças"""
        try:
            params = {"limit": limit}
            if customer_id:
                params["customer"] = customer_id
            
            response = requests.get(
                f"{self.base_url}/payments",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "charges": result.get("data", []),
                    "total": result.get("totalCount", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro ao listar cobranças: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na listagem: {str(e)}"
            }

def create_minimum_charge(user, amount: float = None) -> Dict[str, Any]:
    """
    Cria uma cobrança do valor mínimo para o usuário
    
    Args:
        user: Objeto User
        amount: Valor personalizado (opcional)
        
    Returns:
        Resultado da criação da cobrança
    """
    try:
        if amount is None:
            amount = float(SystemSettings.get_setting('min_charge_amount', '19.90'))
        
        asaas = AsaasAPI()
        
        # Data de vencimento: 7 dias a partir de hoje
        due_date = date.today() + timedelta(days=7)
        
        description = f"Recarga de saldo - {SystemSettings.get_setting('company_name', 'XML Downloader')}"
        
        result = asaas.create_charge(
            customer_email=user.email,
            customer_name=user.name,
            amount=amount,
            description=description,
            due_date=due_date
        )
        
        if result["success"]:
            # Salvar cobrança no banco
            from models import Charge, db
            
            charge = Charge(
                user_id=user.id,
                asaas_charge_id=result["charge_id"],
                amount=amount,
                description=description,
                due_date=due_date,
                status=result["status"],
                payment_url=result.get("payment_url")
            )
            
            db.session.add(charge)
            db.session.commit()
            
            logger.info(f"Cobrança criada para usuário {user.email}: R$ {amount}")
            
        return result
        
    except Exception as e:
        logger.error(f"Erro ao criar cobrança mínima: {str(e)}")
        return {
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }

def process_webhook_payment(webhook_data: Dict) -> bool:
    """
    Processa webhook de pagamento do Asaas
    
    Args:
        webhook_data: Dados do webhook
        
    Returns:
        True se processado com sucesso
    """
    try:
        from models import Charge, User, db
        
        charge_id = webhook_data.get("id")
        status = webhook_data.get("status")
        
        if not charge_id:
            logger.warning("Webhook sem ID de cobrança")
            return False
        
        # Buscar cobrança no banco
        charge = Charge.query.filter_by(asaas_charge_id=charge_id).first()
        
        if not charge:
            logger.warning(f"Cobrança {charge_id} não encontrada no banco")
            return False
        
        # Atualizar status da cobrança
        charge.status = status
        
        # Se foi paga, adicionar saldo ao usuário
        if status == "RECEIVED":
            charge.paid_at = datetime.utcnow()
            
            user = User.query.get(charge.user_id)
            if user:
                user.add_balance(charge.amount)
                logger.info(f"Saldo adicionado para usuário {user.email}: R$ {charge.amount}")
        
        db.session.commit()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return False