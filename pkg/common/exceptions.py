from rest_framework.exceptions import ValidationError
import inflection


class GraphQlValidationError(ValidationError):
    def __str__(self):
        return 'GraphQlValidationError'


class DomainException(Exception):
    @property
    def code(self):
        return inflection.underscore(self.__class__.__name__)
        