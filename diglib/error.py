# -*- coding: utf-8 -*-

class DigitalLibraryError(Exception):
    pass


class DocumentError(DigitalLibraryError):
    pass 


class DocumentNotFound(DocumentError):
    pass


class DuplicateError(DocumentError):
    pass


class ExactDuplicateError(DuplicateError):
    pass


class SimilarDuplicateError(DuplicateError):
    pass


class NotRetrievableError(DocumentError):
    pass
