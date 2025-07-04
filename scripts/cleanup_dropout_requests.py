from app import db, create_app
from app.models import DropoutRequest

def cleanup_dropout_requests():
    print('Deleting all records from dropout_requests table...')
    num_deleted = DropoutRequest.query.delete()
    db.session.commit()
    print(f'Deleted {num_deleted} records.')

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        cleanup_dropout_requests() 