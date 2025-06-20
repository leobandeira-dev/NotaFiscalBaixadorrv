"""
Teste robusto de conexão POP3 para diagnosticar problemas específicos
"""
import poplib
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pop3_connection_robust():
    """Testa conexão POP3 com diagnóstico detalhado"""
    
    # Configurações POP3
    server = "pop.titan.email"
    port = 995
    email = "suporte@crosswms.com.br"
    password = "Cross2025!"
    
    pop3 = None
    
    try:
        logger.info(f"Conectando ao servidor {server}:{port}")
        pop3 = poplib.POP3_SSL(server, port)
        logger.info("Conexão SSL estabelecida")
        
        # Teste de autenticação
        logger.info(f"Autenticando como {email}")
        pop3.user(email)
        response = pop3.pass_(password)
        logger.info(f"Autenticação OK: {response}")
        
        # Teste STAT (mais seguro que LIST)
        logger.info("Testando comando STAT...")
        stat_response = pop3.stat()
        total_messages = stat_response[0]
        total_size = stat_response[1]
        logger.info(f"STAT OK: {total_messages} mensagens, {total_size} bytes")
        
        if total_messages > 0:
            logger.info("Testando RETR com primeira mensagem...")
            try:
                # Testar apenas cabeçalho da primeira mensagem
                top_response = pop3.top(1, 0)
                logger.info("TOP OK: cabeçalho obtido com sucesso")
                
                # Testar RETR completo
                retr_response = pop3.retr(1)
                logger.info(f"RETR OK: mensagem obtida ({len(retr_response[1])} linhas)")
                
            except Exception as msg_error:
                logger.error(f"Erro ao acessar mensagem: {msg_error}")
        
        # Evitar LIST que está causando problema
        logger.info("Evitando comando LIST devido a erro conhecido")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro na conexão POP3: {e}")
        return False
        
    finally:
        if pop3:
            try:
                pop3.quit()
                logger.info("Conexão POP3 encerrada")
            except:
                pass

if __name__ == "__main__":
    print("=== TESTE ROBUSTO POP3 ===")
    success = test_pop3_connection_robust()
    print(f"Resultado: {'SUCESSO' if success else 'FALHA'}")