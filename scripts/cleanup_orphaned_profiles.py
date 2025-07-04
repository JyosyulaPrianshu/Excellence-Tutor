from app import create_app, db
from app.models import User, Profile, Fee, Payment, Mark, Notification, DropoutRequest

def delete_user_and_data(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"No user found with email: {email}")
        return
    # Delete related Profile
    profile = Profile.query.filter_by(user_id=user.id).first()
    if profile:
        db.session.delete(profile)
    # Delete related Fees
    Fee.query.filter_by(user_id=user.id).delete()
    # Delete related Payments
    Payment.query.filter_by(user_id=user.id).delete()
    # Delete related Marks
    Mark.query.filter_by(user_id=user.id).delete()
    # Delete related Notifications
    Notification.query.filter_by(user_id=user.id).delete()
    # Delete related DropoutRequests
    DropoutRequest.query.filter_by(user_id=user.id).delete()
    # Delete the User
    db.session.delete(user)
    db.session.commit()
    print(f"Deleted all data for user: {email}")

def cleanup_orphaned_profiles():
    # Find all orphaned profiles
    orphaned_profiles = Profile.query.filter(~Profile.user_id.in_([u.id for u in User.query.all()])).all()
    count = len(orphaned_profiles)
    for orphan in orphaned_profiles:
        db.session.delete(orphan)
    db.session.commit()
    print(f"Deleted {count} orphaned profiles.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        delete_user_and_data('freshstudent1_6@example.com')
        cleanup_orphaned_profiles() 