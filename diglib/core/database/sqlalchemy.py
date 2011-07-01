# -*- coding: utf-8 -*-

# Implementation of a SQLAchemy-managed SQLite database.

from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from diglib.core.database import Document, Database


SQLAlchemyBase = declarative_base()

class SQLAlchemyTag(SQLAlchemyBase):

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

class SQLAlchemyDocument(SQLAlchemyBase):

    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    hash_md5 = Column(String, nullable=False, unique=True)
    hash_ssdeep = Column(String, nullable=False, unique=True)
    mime_type = Column(String, nullable=False)
    document_path = Column(String, nullable=False)
    document_size = Column(Integer, nullable=False)
    thumbnail_path = Column(String, nullable=False)
    language_code = Column(String, nullable=False)
    tags = relationship(SQLAlchemyTag, secondary='document_tags', backref='documents', 
                        cascade='all, delete, delete-orphan')

    def __init__(self, hash_md5, hash_ssdeep, mime_type, content, document_path, 
                 document_size, thumbnail_path, language_code, tags):
        super(SQLAlchemyDocument, self).__init_()
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self.document_path = document_path
        self.document_size = document_size
        self.thumbnail_path = thumbnail_path
        self.language_code = language_code
        self.tags = tags

document_tags = Table('document_tags', SQLAlchemyBase.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class SQLAlchemyDatabase(Database):

    def __init__(self, database_file):
        super(SQLAlchemyDatabase, self).__init__(database_file)
        engine = create_engine('sqlite://%s' % database_file)
        SQLAlchemyBase.metadata.create_all(engine)
        self._sessionmaker = sessionmaker(engine)

    def create(self, hash_md5, hash_ssdeep, mime_type, content, document_path,
               document_size, thumbnail_path, language_code, tags):
        session = self._sessionmaker()
        tags =  self._normalize_tags(tags)
        doc = SQLAlchemyDocument(hash_md5, hash_ssdeep, mime_type, document_path,
                                 document_size, thumbnail_path, language_code, tags)
        session.add(doc)
        session.commit()
        document = Document(hash_md5, hash_ssdeep, mime_type, content, 
                            document_path, document_size, thumbnail_path, 
                            language_code, [tag.name for tag in tags])
        return document

    def get(self, hash_md5):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument).filter_by(hash_md5=hash_md5)
        if query.count():
            doc = query.first()
            document = Document(doc.hash_md5, doc.hash_ssdeep, doc.mime_type, 
                                None, doc.document_path, doc.document_size, 
                                doc.thumbnail_path, doc.language_code, 
                                [tag.name for tag in doc.tags])
            return document
        else:
            return None

    def is_retrievable(self, hash_md5):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument).filter_by(hash_md5=hash_md5)
        doc = query.first()
        return len(doc.tags) >= 3
    
    def delete(self, hash_md5):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument).filter_by(hash_md5=hash_md5)
        if query.count():
            doc = query.first()
            session.delete(doc)
            session.commit()
            
    def add_tag(self, tag):
        session = self._sessionmaker()
        tag = SQLAlchemyTag(tag)
        session.add(tag)
        session.commit()

    def rename_tag(self, old_name, new_name):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyTag).filter_by(name=old_name)
        if query.count():
            tag = query.first()
            tag.name = new_name
            session.commit()
        else:
            self.add_tag(new_name)

    def update_tags(self, hash_md5, tags):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument).filter_by(hash_md5=hash_md5)
        if query.count():
            doc = query.first()
            tags = self._normalize_tags(tags)
            doc.tags = tags
            session.commit()

    def get_similar_documents(self, lower_size, upper_size):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument) \
            .filter(SQLAlchemyDocument.document_size >= lower_size) \
            .filter(SQLAlchemyDocument.document_size <= upper_size)
        documents = []
        for doc in query.all():
            document = Document(doc.hash_md5, doc.hash_ssdeep, doc.mime_type, 
                                None, doc.document_path, doc.document_size, 
                                doc.thumbnail_path, doc.language_code, 
                                [tag.name for tag in doc.tags])
            documents.append(document)
        return documents

    def close(self):
        self._sessionmaker.remove()

    def _normalize_tags(self, tags):
        session = self._sessionmaker()
        sqlalchemy_tags = []
        for tag in tags:
            query = session.query(SQLAlchemyTag).filter_by(name=tag)
            sqlalchemy_tag = query.scalar()
            if not sqlalchemy_tag:
                sqlalchemy_tag = SQLAlchemyTag(tag)
                session.add(sqlalchemy_tag)
            sqlalchemy_tags.append(sqlalchemy_tag)
        session.commit()
        return sqlalchemy_tags
