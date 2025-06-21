# Clean Email Import Routes - 3 Protocol Types (IMAP, POP3, SMTP)
# This file contains standalone route definitions that should be imported into the main app

@app.route('/save_imap_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_imap_credentials():
    """Salva credenciais IMAP do usuário"""
    try:
        password = request.form.get('imap_password')
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.imap_email = request.form.get('imap_email')
        current_user.imap_password = encrypt_email_password(password)
        current_user.imap_server = request.form.get('imap_server')
        current_user.imap_port = int(request.form.get('imap_port', 993))
        current_user.imap_ssl = 'imap_ssl' in request.form
        current_user.imap_configured = True
        
        db.session.commit()
        flash('Configurações IMAP salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais IMAP: {e}")
        flash(f'Erro ao salvar configurações IMAP: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/save_pop3_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_pop3_credentials():
    """Salva credenciais POP3 do usuário"""
    try:
        password = request.form.get('pop3_password')
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.pop3_email = request.form.get('pop3_email')
        current_user.pop3_password = encrypt_email_password(password)
        current_user.pop3_server = request.form.get('pop3_server')
        current_user.pop3_port = int(request.form.get('pop3_port', 995))
        current_user.pop3_ssl = 'pop3_ssl' in request.form
        current_user.pop3_configured = True
        
        db.session.commit()
        flash('Configurações POP3 salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais POP3: {e}")
        flash(f'Erro ao salvar configurações POP3: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/save_smtp_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_smtp_credentials():
    """Salva credenciais SMTP do usuário"""
    try:
        password = request.form.get('smtp_password')
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.smtp_email = request.form.get('smtp_email')
        current_user.smtp_password = generate_password_hash(password)
        current_user.smtp_server = request.form.get('smtp_server')
        current_user.smtp_port = int(request.form.get('smtp_port', 587))
        current_user.smtp_ssl = 'smtp_ssl' in request.form
        current_user.smtp_configured = True
        
        db.session.commit()
        flash('Configurações SMTP salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais SMTP: {e}")
        flash(f'Erro ao salvar configurações SMTP: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/test-imap-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def test_imap_connection():
    """Testa conexão IMAP"""
    try:
        import imaplib
        data = request.get_json()
        
        server = data['server']
        port = int(data['port'])
        email = data['email']
        password = data['password']
        use_ssl = data['ssl']
        
        if use_ssl:
            mail = imaplib.IMAP4_SSL(server, port)
        else:
            mail = imaplib.IMAP4(server, port)
            
        mail.login(email, password)
        mail.select('inbox')
        mail.logout()
        
        return jsonify({'success': True, 'message': 'Conexão IMAP bem-sucedida'})
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão IMAP: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test-pop3-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def test_pop3_connection():
    """Testa conexão POP3"""
    try:
        import poplib
        data = request.get_json()
        
        server = data['server']
        port = int(data['port'])
        email = data['email']
        password = data['password']
        use_ssl = data['ssl']
        
        if use_ssl:
            pop3 = poplib.POP3_SSL(server, port)
        else:
            pop3 = poplib.POP3(server, port)
            
        pop3.user(email)
        pop3.pass_(password)
        pop3.quit()
        
        return jsonify({'success': True, 'message': 'Conexão POP3 bem-sucedida'})
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão POP3: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test-smtp-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def test_smtp_connection():
    """Testa conexão SMTP"""
    try:
        import smtplib
        data = request.get_json()
        
        server = data['server']
        port = int(data['port'])
        email = data['email']
        password = data['password']
        use_ssl = data['ssl']
        
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)
            smtp.starttls()
            
        smtp.login(email, password)
        smtp.quit()
        
        return jsonify({'success': True, 'message': 'Conexão SMTP bem-sucedida'})
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão SMTP: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/check-emails-now', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def check_emails_now():
    """Verifica emails manualmente agora"""
    try:
        from email_xml_processor import EmailXMLProcessor
        processor = EmailXMLProcessor()
        result = processor.process_user_emails(current_user)
        
        if result['success']:
            # Construir mensagem detalhada baseada nos resultados
            processed_count = result.get('processed_count', 0)
            skipped_count = result.get('skipped_count', 0)
            total_found = result.get('total_found', 0)
            total_messages = result.get('total_messages', 0)
            
            if total_found == 0:
                message = f"Verificação concluída: {total_messages} mensagens verificadas, nenhum XML encontrado."
            elif processed_count == 0 and skipped_count > 0:
                message = f"Verificação concluída: {total_found} XMLs encontrados, {skipped_count} já importados anteriormente."
            elif processed_count > 0 and skipped_count == 0:
                message = f"Verificação concluída: {processed_count} novos XMLs importados com sucesso."
            else:
                message = f"Verificação concluída: {processed_count} novos XMLs importados, {skipped_count} já existentes."
            
            return jsonify({
                'success': True, 
                'message': message,
                'details': {
                    'processed_count': processed_count,
                    'skipped_count': skipped_count,
                    'total_found': total_found,
                    'total_messages': total_messages,
                    'processed_xmls': result.get('processed_xmls', []),
                    'skipped_xmls': result.get('skipped_xmls', [])
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Erro na verificação')
            })
            
    except Exception as e:
        logger.error(f"Erro ao verificar emails: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})