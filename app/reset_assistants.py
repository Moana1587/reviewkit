from app import app, sqlite_db, OpenAICreds

with app.app_context():
    deleted = OpenAICreds.query.filter_by(company_id='129').delete()
    sqlite_db.session.commit()
    print(f"Deleted {deleted} assistant records for company_id 129.")
