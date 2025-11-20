
# --- Rotas de Pagamento PIX (Efí) ---

@app.route('/create_pix_payment', methods=['POST'])
@login_required
def create_pix_payment():
    """Cria uma cobrança PIX via Efí e retorna QR Code"""
    db = database.get_db()
    
    # Obter dados do checkout
    ticket_ids_str = request.form.get('ticket_ids', '')
    from_session = request.form.get('from_session') == 'true'
    
    try:
        if from_session and 'pending_purchase' in session:
            # Fazendinha: dados na sessão
            purchase = session['pending_purchase']
            raffle_id = purchase['raffle_id']
            raffle_title = purchase['raffle_title']
            quantity = purchase['quantity']
            
            # Calcular preço efetivo
            raffle_data = {
                'price': purchase['price'],
                'promo_price': purchase.get('promo_price'),
                'promo_end': purchase.get('promo_end')
            }
            effective_price = get_current_price(raffle_data)
            total_amount = effective_price * quantity
            
            tickets_data = {
                'quantity': quantity,
                'type': 'fazendinha'
            }
            
        elif ticket_ids_str:
            # Manual: tickets já criados
            ticket_ids = [int(id) for id in ticket_ids_str.split(',')]
            
            placeholders = ','.join(['?'] * len(ticket_ids))
            query = f'''
                SELECT t.*, r.title as raffle_title, r.price, r.promo_price, r.promo_end, r.id as raffle_id
                FROM ticket t 
                JOIN raffle r ON t.raffle_id = r.id 
                WHERE t.id IN ({placeholders}) AND t.user_id = ?
            '''
            params = ticket_ids + [current_user.id]
            
            tickets = db.execute(query, params).fetchall()
            
            if not tickets:
                return jsonify({'success': False, 'error': 'Bilhetes não encontrados'}), 404
            
            raffle_id = tickets[0]['raffle_id']
            raffle_title = tickets[0]['raffle_title']
            
            # Calcular total
            total_amount = 0
            for t in tickets:
                raffle_data = {
                    'price': t['price'],
                    'promo_price': t['promo_price'],
                    'promo_end': t['promo_end']
                }
                total_amount += get_current_price(raffle_data)
            
            tickets_data = {
                'ticket_ids': ticket_ids,
                'type': 'manual'
            }
        else:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        # Criar cobrança PIX via Efí
        result = efi_service.create_pix_charge(
            amount=total_amount,
            raffle_title=raffle_title,
            raffle_id=raffle_id,
            user_id=current_user.id,
            tickets_data=tickets_data
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        # Salvar txid na sessão ou banco temporariamente
        if from_session:
            session['pending_pix'] = {
                'txid': result['txid'],
                'amount': total_amount,
                'raffle_id': raffle_id,
                'quantity': quantity
            }
        else:
            # Atualizar tickets com txid
            for ticket_id in ticket_ids:
                db.execute('''
                    UPDATE ticket 
                    SET payment_txid = ?, payment_status = 'pending', 
                        pix_qrcode = ?, pix_copy_paste = ?, 
                        payment_expiration = ?, total_price = ?
                    WHERE id = ?
                ''', (result['txid'], result['qr_code'], result['copy_paste'], 
                      result['expiration'], total_amount / len(ticket_ids), ticket_id))
            db.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/check_payment_status/<txid>', methods=['GET'])
@login_required
def check_payment_status(txid):
    """Consulta status de pagamento PIX"""
    try:
        result = efi_service.check_payment_status(txid)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/webhook/efi', methods=['POST'])
def efi_webhook():
    """Recebe notificações de pagamento da Efí"""
    try:
        # Validar assinatura
        signature = request.headers.get('X-Efi-Signature', '')
        payload = request.get_data()
        
        if not efi_service.validate_webhook(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        
        # Processar notificação PIX
        if data.get('evento') == 'pix':
            for pix in data.get('pix', []):
                txid = pix.get('txid')
                
                if not txid:
                    continue
                
                # Buscar tickets com este txid
                db = database.get_db()
                tickets = db.execute('SELECT * FROM ticket WHERE payment_txid = ?', (txid,)).fetchall()
                
                if tickets:
                    # Pagamento de rifa manual
                    for ticket in tickets:
                        db.execute('''
                            UPDATE ticket 
                            SET payment_status = 'paid', status = 'paid', paid_at = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), ticket['id']))
                    db.commit()
                else:
                    # Pode ser fazendinha - verificar sessão (mas webhook não tem sessão)
                    # Precisamos armazenar txid → pending_purchase mapping no banco
                    pass
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

