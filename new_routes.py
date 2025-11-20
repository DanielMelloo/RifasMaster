@app.route('/admin/remove_promotion/<int:raffle_id>', methods=['POST'])
@login_required
def remove_promotion(raffle_id):
    """Remove a promoção de uma rifa"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    db = database.get_db()
    
    # Atualizar rifa removendo promoção
    db.execute('''
        UPDATE raffle 
        SET promo_price = NULL, promo_end = NULL 
        WHERE id = ?
    ''', (raffle_id,))
    db.commit()
    
    flash('Promoção removida com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_raffle/<int:raffle_id>', methods=['POST'])
@login_required
def delete_raffle(raffle_id):
    """Deleta uma rifa (somente se não houver bilhetes vendidos)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    db = database.get_db()
    
    # Verificar se a rifa pode ser deletada
    raffle = db.execute('SELECT * FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
    
    if not raffle:
        flash('Rifa não encontrada.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Contar tickets
    ticket_count = db.execute('SELECT COUNT(*) as count FROM ticket WHERE raffle_id = ?', (raffle_id,)).fetchone()['count']
    
    if ticket_count > 0:
        flash('Não é possível deletar rifa com bilhetes vendidos.', 'error')
        return redirect(url_for('admin_panel'))
    
    if raffle['status'] == 'closed':
        flash('Não é possível deletar rifa já encerrada.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Deletar rifa
    db.execute('DELETE FROM raffle WHERE id = ?', (raffle_id,))
    db.commit()
    
    flash(f'Rifa "{raffle["title"]}" deletada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/winner_details/<int:raffle_id>')
@login_required
def winner_details(raffle_id):
    """Retorna detalhes do ganhador em JSON"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = database.get_db()
    
    # Buscar dados da rifa e do ganhador
    query = '''
        SELECT r.*, t.number as winning_number, t.purchase_date,
               u.username, u.email
        FROM raffle r
        LEFT JOIN ticket t ON r.winner_ticket_id = t.id
        LEFT JOIN user u ON t.user_id = u.id
        WHERE r.id = ?
    '''
    result = db.execute(query, (raffle_id,)).fetchone()
    
    if not result or not result['winner_ticket_id']:
        return jsonify({'error': 'No winner found'}), 404
    
    return jsonify({
        'raffle_title': result['title'],
        'winner_name': result['username'],
        'winner_email': result['email'],
        'winning_number': result['winning_number'],
        'purchase_date': result['purchase_date'],
        'raffle_price': float(result['price'])
    })
