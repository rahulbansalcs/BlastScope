from app.db.database import Base,initialize_database
from app.models.analysis import AnalysisRecord
def init_db():
    engine=initialize_database()
    Base.metadata.create_all(bind=engine)
if __name__=="__main__":
    init_db()