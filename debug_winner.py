import sqlite3

db = sqlite3.connect('rifamaster.db')

# Find iPhone raffle
raffles = db.execute("SELECT id, title, winner_ticket_id FROM raffle WHERE title LIKE '%phone%'").fetchall()
print('Raffles with iPhone:', raffles)

if raffles:
    raffle_id = raffles[0][0]
    winner_id = raffles[0][2]
    print(f'Raffle ID: {raffle_id}')
    print(f'Winner Ticket ID: {winner_id}')
    
    if winner_id:
        winner = db.execute('SELECT id, user_id, number FROM ticket WHERE id = ?', (winner_id,)).fetchone()
        print(f'Winner ticket: ID={winner[0]}, User={winner[1]}, Number={winner[2]}')
        
        user_tickets = db.execute('SELECT id, number FROM ticket WHERE user_id = ? AND raffle_id = ?', (winner[1], raffle_id)).fetchall()
        print(f'User owns {len(user_tickets)} tickets for this raffle:')
        for t in user_tickets:
            print(f'  - Ticket {t[0]}: number {t[1]}')

db.close()
