# -*- coding: utf-8 -*-
#
# diglib: Personal digital document management software.
# Copyright (C) 2011-2015 Yasser Gonzalez <yasserglez@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from diglib.core import Document


class Database(object):

    def __init__(self, database_file):
        pass

    def add_doc(self, doc):
        raise NotImplementedError()

    def get_doc(self, hash_md5):
        raise NotImplementedError()

    # Get documents whose size is between the given values.
    def get_similar_docs(self, lower_size, upper_size):
        raise NotImplementedError()

    def delete_doc(self, hash_md5):
        raise NotImplementedError()

    # Get all tags in the database.
    def get_all_tags(self):
        raise NotImplementedError()

    # Get the frequency of a tag.
    def get_tag_freq(self, tag):
        raise NotImplementedError()

    def rename_tag(self, old_tag, new_tag):
        raise NotImplementedError()

    def update_tags(self, hash_md5, new_tags):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


# Implementation of a SQLite database managed by SQLAchemy.

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
    small_thumbnail_path = Column(String)
    normal_thumbnail_path = Column(String)
    large_thumbnail_path = Column(String)
    language_code = Column(String, nullable=False)
    tags = relationship(SQLAlchemyTag, secondary='document_tags', backref='documents')

    def __init__(self, hash_md5, hash_ssdeep, mime_type, document_path,
                 document_size, small_thumbnail_path, normal_thumbnail_path,
                 large_thumbnail_path, language_code, tags):
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self.document_path = document_path
        self.document_size = document_size
        self.small_thumbnail_path = small_thumbnail_path
        self.normal_thumbnail_path = normal_thumbnail_path
        self.large_thumbnail_path = large_thumbnail_path
        self.language_code = language_code
        self.tags = tags

document_tags = Table('document_tags', SQLAlchemyBase.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class SQLAlchemyDatabase(Database):

    def __init__(self, database_file):
        super(SQLAlchemyDatabase, self).__init__(database_file)
        engine = create_engine('sqlite:///%s' % database_file)
        SQLAlchemyBase.metadata.create_all(engine)
        self._sessionmaker = sessionmaker(engine)

    def add_doc(self, doc):
        session = self._sessionmaker()
        sqlalchemy_tags =  self._normalize_tags(session, doc.tags)
        sqlalchemy_doc = \
            SQLAlchemyDocument(doc.hash_md5, doc.hash_ssdeep, doc.mime_type,
                               doc.document_path, doc.document_size,
                               doc.small_thumbnail_path, doc.normal_thumbnail_path,
                               doc.large_thumbnail_path, doc.language_code,
                               sqlalchemy_tags)
        session.add(sqlalchemy_doc)
        session.commit()
        session.close()

    def get_doc(self, hash_md5):
        session = self._sessionmaker()
        sqlalchemy_doc = session.query(SQLAlchemyDocument) \
            .filter_by(hash_md5=hash_md5).scalar()
        if sqlalchemy_doc:
            tags = set([sqlalchemy_tag.name for sqlalchemy_tag in sqlalchemy_doc.tags])
            doc = Document(sqlalchemy_doc.hash_md5, sqlalchemy_doc.hash_ssdeep,
                           sqlalchemy_doc.mime_type, sqlalchemy_doc.document_path,
                           sqlalchemy_doc.document_size,
                           sqlalchemy_doc.small_thumbnail_path,
                           sqlalchemy_doc.normal_thumbnail_path,
                           sqlalchemy_doc.large_thumbnail_path,
                           sqlalchemy_doc.language_code, tags)
        else:
            doc = None # Document not found.
        session.close()
        return doc

    def get_similar_docs(self, lower_size, upper_size):
        docs = []
        session = self._sessionmaker()
        query = session.query(SQLAlchemyDocument) \
            .filter(SQLAlchemyDocument.document_size >= lower_size) \
            .filter(SQLAlchemyDocument.document_size <= upper_size)
        for sqlalchemy_doc in query.all():
            tags = set([sqlalchemy_tag.name for sqlalchemy_tag in sqlalchemy_doc.tags])
            doc = Document(sqlalchemy_doc.hash_md5, sqlalchemy_doc.hash_ssdeep,
                           sqlalchemy_doc.mime_type, sqlalchemy_doc.document_path,
                           sqlalchemy_doc.document_size,
                           sqlalchemy_doc.small_thumbnail_path,
                           sqlalchemy_doc.normal_thumbnail_path,
                           sqlalchemy_doc.large_thumbnail_path,
                           sqlalchemy_doc.language_code, tags)
            docs.append(doc)
        session.close()
        return docs

    def delete_doc(self, hash_md5):
        session = self._sessionmaker()
        sqlalchemy_doc = session.query(SQLAlchemyDocument) \
            .filter_by(hash_md5=hash_md5).scalar()
        if sqlalchemy_doc:
            for tag in [sqlalchemy_tag.name for sqlalchemy_tag in sqlalchemy_doc.tags]:
                if self.get_tag_count(tag) == 1:
                    sqlalchemy_tag = self._normalize_tag(session, tag)
                    session.delete(sqlalchemy_tag)
            session.delete(sqlalchemy_doc)
            session.commit()
        session.close()

    def get_all_tags(self):
        tags = set()
        session = self._sessionmaker()
        query = session.query(SQLAlchemyTag)
        for sqlalchemy_tag in query.all():
            tags.add(sqlalchemy_tag.name)
        session.close()
        return tags

    def get_doc_count(self):
        session = self._sessionmaker()
        doc_count = session.query(SQLAlchemyDocument).count()
        return doc_count

    def get_tag_count(self, tag):
        session = self._sessionmaker()
        query = session.query(SQLAlchemyTag).filter_by(name=tag)
        sqlalchemy_tag = query.scalar()
        tag_count = len(sqlalchemy_tag.documents) if sqlalchemy_tag else 0
        return tag_count

    def get_tag_freq(self, tag):
        doc_count = self.get_doc_count()
        if doc_count:
            tag_count = self.get_tag_count(tag)
            return tag_count / float(doc_count)
        else:
            return 0.0

    def rename_tag(self, old_tag, new_tag):
        session = self._sessionmaker()
        old_sqlalchemy_tag = session.query(SQLAlchemyTag) \
            .filter_by(name=old_tag).scalar()
        new_sqlalchemy_tag = session.query(SQLAlchemyTag) \
            .filter_by(name=new_tag).scalar()
        if new_sqlalchemy_tag:
            for sqlalchemy_doc in old_sqlalchemy_tag.documents:
                i = sqlalchemy_doc.tags.index(old_sqlalchemy_tag)
                sqlalchemy_doc.tags[i] = new_sqlalchemy_tag
            session.delete(old_sqlalchemy_tag)
        else:
            old_sqlalchemy_tag.name = new_tag
        session.commit()
        session.close()

    def update_tags(self, hash_md5, new_tags):
        session = self._sessionmaker()
        sqlalchemy_doc = session.query(SQLAlchemyDocument) \
            .filter_by(hash_md5=hash_md5).scalar()
        if sqlalchemy_doc:
            old_tags = set([sqlalchemy_tag.name for sqlalchemy_tag in sqlalchemy_doc.tags])
            removed_tags = old_tags.difference(new_tags)
            sqlalchemy_doc.tags = self._normalize_tags(session, new_tags)
            session.commit()
        for tag in removed_tags:
            if not self.get_tag_freq(tag):
                sqlalchemy_tag = self._normalize_tag(session, tag)
                session.delete(sqlalchemy_tag)
                session.commit()
        session.close()

    def close(self):
        self._sessionmaker.close_all()

    # Return a SQLAlchemyTag corresponding to the given tag name.
    # The tag is added if it does not exists in the database.
    def _normalize_tag(self, session, tag):
        query = session.query(SQLAlchemyTag).filter_by(name=tag)
        sqlalchemy_tag = query.scalar()
        if not sqlalchemy_tag: # Tag does not exists.
            sqlalchemy_tag = SQLAlchemyTag(tag)
            session.add(sqlalchemy_tag)
            session.commit()
        return sqlalchemy_tag

    def _normalize_tags(self, session, tags):
        sqlalchemy_tags = []
        for tag in tags:
            sqlalchemy_tag = self._normalize_tag(session, tag)
            sqlalchemy_tags.append(sqlalchemy_tag)
        return sqlalchemy_tags
